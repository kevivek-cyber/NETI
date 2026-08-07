"""Item Bank Analysis & Review Queue Generator Tool.

Inspects an Item Bank JSON using authoring-time M1 & M2 pipelines and SymPy symbolic validation.
Identifies suspicious items, metadata conflicts, and symbolic failures for expert review.
Never modifies the original item bank.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add repository root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipeline import analyze_item

DEFAULT_BANK_PATH = ROOT_DIR / "backend" / "app" / "bank" / "sample_bank.json"
DEFAULT_REPORT_PATH = ROOT_DIR / "ml" / "artifacts" / "reports" / "bank_analysis_report.json"
DEFAULT_QUEUE_PATH = ROOT_DIR / "ml" / "artifacts" / "reports" / "review_queue.json"
TAXONOMY_PATH = ROOT_DIR / "ml" / "taxonomy.json"


def analyze_item_bank(
    bank_path: Path = DEFAULT_BANK_PATH,
    report_output_path: Path = DEFAULT_REPORT_PATH,
    queue_output_path: Path = DEFAULT_QUEUE_PATH,
) -> Dict[str, Any]:
    """Audit every item in an item bank and generate diagnostic reports and review queues."""
    if not bank_path.exists():
        raise FileNotFoundError(f"Item bank not found at: {bank_path}")

    raw_bank = json.loads(bank_path.read_text(encoding="utf-8"))
    items = raw_bank.get("items", [])
    bank_version = raw_bank.get("bank_version", "unknown")

    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    valid_subjects = set(taxonomy["subjects"].keys())
    valid_chapters = {subj: set(taxonomy["subjects"][subj]["chapters"].keys()) for subj in valid_subjects}

    total_items = len(items)
    subject_counts = collections.Counter()
    chapter_counts = collections.Counter()
    concept_counts = collections.Counter()
    cognitive_counts = collections.Counter()
    fallback_count = 0
    symbolic_failures = 0
    confidence_scores = []
    b_values = []
    a_values = []

    review_queue: List[Dict[str, Any]] = []
    item_analysis_records: List[Dict[str, Any]] = []

    for item in items:
        item_id = item.get("id", "unknown_id")
        existing_subject = item.get("subject", "unknown")
        existing_chapter = item.get("chapter", "unknown")
        existing_concepts = item.get("concept_tags", [])
        existing_cognitive = item.get("cognitive_level", "application")

        subject_counts[existing_subject] += 1
        chapter_counts[existing_chapter] += 1
        cognitive_counts[existing_cognitive] += 1
        for c in existing_concepts:
            concept_counts[c] += 1

        # Run authoring-time pipeline
        analysis = analyze_item(item)
        m1 = analysis["m1"]
        m2 = analysis["m2"]
        val = analysis["validation"]

        conf = m1["confidence"]
        confidence_scores.append(conf)
        b_values.append(float(m2["b"]))
        a_values.append(float(m2["a"]))

        if m1["fallback_used"]:
            fallback_count += 1
        if not val["symbolic"]:
            symbolic_failures += 1

        # -------------------------------------------------------------
        # Review Queue Flagging Logic
        # -------------------------------------------------------------
        reasons = []
        severity = "low"

        # Check 1: Symbolic validation failure (High Severity)
        if not val["symbolic"]:
            reasons.append(f"Symbolic validation failed: {'; '.join(val['issues'])}")
            severity = "high"

        # Check 2: Subject disagreement
        if existing_subject != m1["subject"]:
            reasons.append(f"Subject conflict: existing='{existing_subject}' vs predicted='{m1['subject']}'")
            if severity != "high":
                severity = "medium"

        # Check 3: Chapter disagreement
        if existing_chapter != m1["chapter"]:
            reasons.append(f"Chapter conflict: existing='{existing_chapter}' vs predicted='{m1['chapter']}'")
            if severity == "low":
                severity = "medium"

        # Check 4: Low ML confidence
        if conf < 0.35:
            reasons.append(f"Low ML confidence ({conf:.1%}) - taxonomy fallback used")

        # Check 5: Invalid taxonomy chapter
        if existing_subject in valid_chapters and existing_chapter not in valid_chapters[existing_subject]:
            reasons.append(f"Chapter '{existing_chapter}' not in valid taxonomy for {existing_subject}")
            severity = "high"

        # Enqueue item if any issues or conflicts detected
        if reasons:
            review_queue.append({
                "item_id": item_id,
                "existing_metadata": {
                    "subject": existing_subject,
                    "chapter": existing_chapter,
                    "concept_tags": existing_concepts,
                    "cognitive_level": existing_cognitive,
                },
                "predicted_metadata": {
                    "subject": m1["subject"],
                    "chapter": m1["chapter"],
                    "concept_tags": m1["concept_tags"],
                    "cognitive_level": m1["cognitive_level"],
                    "confidence": conf,
                    "source": m1["source"],
                    "predicted_irt": {"a": m2["a"], "b": m2["b"], "c": m2["c"]},
                },
                "reasons": reasons,
                "severity": severity,
            })

        item_analysis_records.append({
            "item_id": item_id,
            "existing": item,
            "analysis": analysis,
            "flagged_for_review": bool(reasons),
        })

    # Compile report payload
    report = {
        "bank_path": str(bank_path),
        "bank_version": bank_version,
        "total_items": total_items,
        "subject_distribution": dict(subject_counts),
        "chapter_distribution": dict(chapter_counts),
        "concept_distribution": dict(concept_counts),
        "cognitive_level_distribution": dict(cognitive_counts),
        "m1_confidence": {
            "mean": float(sum(confidence_scores) / max(1, len(confidence_scores))),
            "min": float(min(confidence_scores)) if confidence_scores else 0.0,
            "max": float(max(confidence_scores)) if confidence_scores else 0.0,
            "fallback_usage_count": fallback_count,
        },
        "provisional_irt_distribution": {
            "b_mean": float(sum(b_values) / max(1, len(b_values))),
            "b_min": float(min(b_values)) if b_values else 0.0,
            "b_max": float(max(b_values)) if b_values else 0.0,
            "a_mean": float(sum(a_values) / max(1, len(a_values))),
            "a_min": float(min(a_values)) if a_values else 0.0,
            "a_max": float(max(a_values)) if a_values else 0.0,
        },
        "symbolic_validation_failures": symbolic_failures,
        "review_queue_count": len(review_queue),
        "items": item_analysis_records,
    }

    # Save reports
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    queue_output_path.parent.mkdir(parents=True, exist_ok=True)
    queue_output_path.write_text(json.dumps(review_queue, indent=2), encoding="utf-8")

    return report


def print_human_readable_summary(report: Dict[str, Any]) -> None:
    print("=" * 68)
    print(f"  NETI ITEM BANK ANALYSIS SUMMARY ({report['bank_version']})")
    print("=" * 68)
    print(f"Total Items Analyzed:           {report['total_items']}")
    print(f"Subject Distribution:           {report['subject_distribution']}")
    print(f"Chapter Distribution:           {len(report['chapter_distribution'])} chapters covered")
    print(f"Cognitive Level Distribution:   {report['cognitive_level_distribution']}")
    print(f"M1 Mean Prediction Confidence:  {report['m1_confidence']['mean']:.1%}")
    print(f"Taxonomy Fallback Used:         {report['m1_confidence']['fallback_usage_count']} items")
    print(f"Symbolic Validation Failures:   {report['symbolic_validation_failures']} items")
    print(f"Provisional Difficulty (b):     mean={report['provisional_irt_distribution']['b_mean']:.2f}, range=[{report['provisional_irt_distribution']['b_min']:.2f}, {report['provisional_irt_distribution']['b_max']:.2f}]")
    print(f"Provisional Discrimination (a): mean={report['provisional_irt_distribution']['a_mean']:.2f}, range=[{report['provisional_irt_distribution']['a_min']:.2f}, {report['provisional_irt_distribution']['a_max']:.2f}]")
    print(f"Items Flagged for Review:       {report['review_queue_count']} / {report['total_items']}")
    print("=" * 68)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze NETI Item Bank Offline")
    parser.add_argument("--bank-path", type=str, default=str(DEFAULT_BANK_PATH), help="Path to input item bank JSON")
    parser.add_argument("--report-path", type=str, default=str(DEFAULT_REPORT_PATH), help="Output analysis report path")
    parser.add_argument("--queue-path", type=str, default=str(DEFAULT_QUEUE_PATH), help="Output review queue path")
    args = parser.parse_args()

    report = analyze_item_bank(
        bank_path=Path(args.bank_path),
        report_output_path=Path(args.report_path),
        queue_output_path=Path(args.queue_path),
    )
    print_human_readable_summary(report)


if __name__ == "__main__":
    main()
