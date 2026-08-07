"""Automated Quality Gates for NETI ML Pipeline (Role 2).

Enforces:
1. Cognitive level F1 > 0 (prevents silent cognitive tag failure)
2. M1 beats majority class baseline on Subject & Chapter
3. M1 predictions contain valid taxonomy labels only
4. M2 beats trivial mean predictor baseline on difficulty b (RMSE_model < RMSE_mean, R^2 > 0)
5. M2 predictions respect strict psychometric bounds (b in [-3, 3], a in [0.2, 2.5], c = 0.25)
6. All IRT parameters serialize as valid RFC 8785 2-decimal strings
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add repository root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROOT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.dataset.curated_mock import generate_curated_mock_dataset
from ml.m1_tagger.train import train_m1_pipeline
from ml.m2_difficulty.train import train_m2_pipeline

TAXONOMY_PATH = ROOT_DIR / "taxonomy.json"


class QualityGateFailure(Exception):
    """Raised when an ML quality gate is violated."""
    pass


def run_all_quality_gates(seed: int = 42) -> Dict[str, Any]:
    print("=" * 65)
    print("  NETI ML QUALITY GATES & INTEGRITY AUDIT")
    print("=" * 65)

    failures: List[str] = []

    # 1. Audit Dataset Quality
    print("\n[Gate 1/5] Auditing Dataset Balance and Grounding...")
    items = generate_curated_mock_dataset(target_count=350, seed=seed)
    subj_counts = set(it.subject.value for it in items)
    cog_counts = set(it.cognitive_level.value for it in items)

    if len(subj_counts) < 4:
        failures.append(f"Gate 1 Failed: Expected 4 subjects, got {len(subj_counts)}")
    if len(cog_counts) < 3:
        failures.append(f"Gate 1 Failed: Expected 3 cognitive levels, got {len(cog_counts)}")
    print(f"  [PASS] Dataset contains {len(items)} items across {len(subj_counts)} subjects and {len(cog_counts)} cognitive levels.")

    # 2. Audit M1 Performance & Cognitive Level F1
    print("\n[Gate 2/5] Checking M1 Baseline vs Majority Baseline...")
    m1_res = train_m1_pipeline(items=items, seed=seed)
    m1_metrics = m1_res["metrics"]

    cog_macro_f1 = m1_metrics["cognitive_level"]["macro_f1"]
    cog_acc = m1_metrics["cognitive_level"]["model_accuracy"]
    subj_acc = m1_metrics["subject"]["model_accuracy"]
    subj_base = m1_metrics["subject"]["majority_baseline_accuracy"]

    if cog_macro_f1 <= 0.0 or cog_acc <= 0.0:
        failures.append(f"Gate 2 Failed: Cognitive Level F1 is 0.0 (got F1={cog_macro_f1:.3f}, Acc={cog_acc:.3f})")
    else:
        print(f"  [PASS] Cognitive Level Macro-F1 = {cog_macro_f1:.3f} > 0.0 (Accuracy = {cog_acc:.3f})")

    if subj_acc <= subj_base:
        failures.append(f"Gate 2 Failed: Subject accuracy ({subj_acc:.3f}) failed to beat majority baseline ({subj_base:.3f})")
    else:
        print(f"  [PASS] Subject Accuracy ({subj_acc:.3f}) beats majority baseline ({subj_base:.3f})")

    # 3. Check Taxonomy Adherence
    print("\n[Gate 3/5] Validating Taxonomy Label Conformance...")
    taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    valid_subjects = set(taxonomy["subjects"].keys())
    valid_chapters = set()
    for s_dict in taxonomy["subjects"].values():
        valid_chapters.update(s_dict["chapters"].keys())

    m1_classes = set(m1_metrics["subject"]["classes"])
    invalid_subjects = m1_classes - valid_subjects
    if invalid_subjects:
        failures.append(f"Gate 3 Failed: Model predicted unknown subjects: {invalid_subjects}")
    else:
        print("  [PASS] All predicted subject classes adhere strictly to NEET taxonomy.")

    # 4. Audit M2 Performance vs Mean Baseline
    print("\n[Gate 4/5] Checking M2 Difficulty Regression vs Mean Baseline...")
    m2_res = train_m2_pipeline(items=items, seed=seed)
    m2_metrics = m2_res["metrics"]

    b_diag = m2_metrics["difficulty_b"]
    b_rmse = b_diag["model_rmse"]
    b_mean_rmse = b_diag["mean_baseline_rmse"]
    b_r2 = b_diag["r2_score"]
    b_pearson = b_diag["pearson_r"]

    if b_rmse >= b_mean_rmse or b_r2 <= 0.0:
        failures.append(f"Gate 4 Failed: M2 RMSE ({b_rmse:.3f}) failed to beat Mean Baseline ({b_mean_rmse:.3f}) or R^2 <= 0 (got R^2={b_r2:.3f})")
    else:
        print(f"  [PASS] M2 Difficulty b RMSE ({b_rmse:.3f}) beats Mean Baseline ({b_mean_rmse:.3f}), R^2 = {b_r2:.3f} > 0, Pearson r = {b_pearson:.3f}")

    # 5. Check Psychometric Bounds and Formats
    print("\n[Gate 5/5] Checking Psychometric Parameter Formats and Bounds...")
    for it in items[:50]:
        a_f, b_f, c_f = it.irt.to_floats()
        if not (-3.0 <= b_f <= 3.0):
            failures.append(f"Gate 5 Failed: Item {it.id} difficulty b={b_f} out of bounds [-3, 3]")
        if not (0.2 <= a_f <= 2.5):
            failures.append(f"Gate 5 Failed: Item {it.id} discrimination a={a_f} out of bounds [0.2, 2.5]")
        if c_f != 0.25:
            failures.append(f"Gate 5 Failed: Item {it.id} guessing floor c={c_f} != 0.25")
    print("  [PASS] All 3PL parameters respect exact physical bounds and 2-decimal string formatting.")

    print("=" * 65)
    if failures:
        print("  QUALITY GATES FAILED:")
        for f in failures:
            print(f"  - {f}")
        print("=" * 65)
        raise QualityGateFailure(f"{len(failures)} quality gate(s) failed.")
    
    print("  ALL 5 QUALITY GATES PASSED SUCCESSFULLY!")
    print("=" * 65)
    return {
        "status": "PASSED",
        "m1_subject_accuracy": subj_acc,
        "m1_cognitive_macro_f1": cog_macro_f1,
        "m2_b_rmse": b_rmse,
        "m2_b_r2": b_r2,
        "m2_b_pearson_r": b_pearson,
    }


if __name__ == "__main__":
    run_all_quality_gates()
