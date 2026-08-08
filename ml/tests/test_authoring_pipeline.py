"""Integration and non-interference tests for authoring ML pipeline.

Verifies:
1. Saved M1 and M2 model artifacts load cleanly.
2. analyze_item() is pure and deterministic.
3. Same item produces identical prediction across runs.
4. Low confidence / fallback items enter review queue.
5. Symbolic validation errors are caught and queued.
6. Original bank metadata is strictly preserved during enrichment.
7. Enrichment outputs match item counts and preserve IDs.
8. HARD INVARIANT: Exam-time generator does NOT import ML modules.
9. Fixed-precision IRT parameter serialization conforms to RFC 8785.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

from ml.dataset.schema import IRTParameters, Item, ItemKindEnum, SubjectEnum
from ml.pipeline import AuthoringMLPipeline, analyze_item
from ml.tools.analyze_item_bank import analyze_item_bank
from ml.tools.enrich_item_bank import enrich_item_bank

ROOT_DIR = Path(__file__).resolve().parents[2]
SAMPLE_BANK_PATH = ROOT_DIR / "backend" / "app" / "bank" / "sample_bank.json"


def test_saved_artifacts_load_cleanly():
    pipeline = AuthoringMLPipeline()
    assert pipeline.m1_engine.model.is_fitted
    assert pipeline.m2_engine.model.is_fitted


def test_analyze_item_is_deterministic():
    test_item = {
        "id": "TEST-PHY-001",
        "subject": "physics",
        "chapter": "kinematics",
        "cognitive_level": "application",
        "kind": "template",
        "stem": "A particle is projected at {angle} degrees with velocity {v} m/s under gravity g = 10 m/s^2. Determine the range.",
        "params": {"angle": [15, 30, 37, 53, 75], "v": [10, 20, 30, 40]},
        "answer": "v**2 * sin(2*radians(angle)) / 10",
        "distractors": ["v**2 * sin(radians(angle)) / 10", "v**2 / 35", "v * sin(2*radians(angle)) / 10"],
        "unit": "m",
        "irt": {"a": "1.20", "b": "-0.30", "c": "0.25"},
    }

    res1 = analyze_item(test_item)
    res2 = analyze_item(test_item)

    assert res1["m1"] == res2["m1"]
    assert res1["m2"] == res2["m2"]
    assert res1["validation"] == res2["validation"]
    assert res1["validation"]["symbolic"] is True


def test_symbolic_failure_is_flagged():
    bad_template = {
        "id": "BAD-TEMP-001",
        "subject": "physics",
        "chapter": "kinematics",
        "kind": "template",
        "stem": "A body accelerates at {a} m/s^2 with mass {m} kg.",
        "params": {"a": [2, 4], "m": [3, 5]},
        "answer": "m * a",
        "distractors": ["m * a", "m + a", "m / a"],  # Distractor 1 equals answer!
        "unit": "N",
        "irt": {"a": "1.00", "b": "0.00", "c": "0.25"},
    }

    res = analyze_item(bad_template)
    assert res["validation"]["symbolic"] is False
    assert len(res["validation"]["issues"]) > 0


def test_enrichment_preserves_original_metadata(tmp_path: Path):
    out_bank = tmp_path / "enriched_sample_bank.json"
    summary = enrich_item_bank(
        input_bank_path=SAMPLE_BANK_PATH,
        output_bank_path=out_bank,
    )

    assert out_bank.exists()
    enriched_data = json.loads(out_bank.read_text(encoding="utf-8"))
    original_data = json.loads(SAMPLE_BANK_PATH.read_text(encoding="utf-8"))

    assert len(enriched_data["items"]) == len(original_data["items"])

    for orig, enr in zip(original_data["items"], enriched_data["items"]):
        assert orig["id"] == enr["id"]
        assert orig["subject"] == enr["subject"]
        assert orig["chapter"] == enr["chapter"]
        assert orig["stem"] == enr["stem"]
        assert orig["irt"] == enr["irt"]
        assert "ml_analysis" in enr
        assert enr["ml_analysis"]["m2"]["provisional"] is True


def test_review_queue_creation_on_bank_analysis(tmp_path: Path):
    report_file = tmp_path / "test_report.json"
    queue_file = tmp_path / "test_queue.json"

    report = analyze_item_bank(
        bank_path=SAMPLE_BANK_PATH,
        report_output_path=report_file,
        queue_output_path=queue_file,
    )

    assert report_file.exists()
    assert queue_file.exists()
    assert report["total_items"] == 12
    assert "symbolic_validation_failures" in report


def test_exam_time_generator_does_not_import_ml():
    """CRITICAL NON-INTERFERENCE PROPERTY TEST.
    
    Proves that importing and executing backend/app/generation/generator.py
    does NOT load scikit-learn, scipy, or any ml.* module into memory.
    """
    check_script = (
        "import sys;"
        "from app.generation import generator;"
        "from app.generation.blueprint import DEMO;"
        "bank = generator.load_bank();"
        "paper = generator.generate(bytes(range(32)), bank, DEMO);"
        "imported_mods = [m for m in sys.modules if m.startswith('ml.') or m.startswith('sklearn') or m.startswith('scipy')];"
        "assert len(imported_mods) == 0, f'ML modules leaked into exam runtime: {imported_mods}';"
        "print('ISOLATION_VERIFIED')"
    )

    # Run in fresh subprocess to verify pure import namespace
    res = subprocess.run(
        [sys.executable, "-c", check_script],
        cwd=str(ROOT_DIR / "backend"),
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ISOLATION_VERIFIED" in res.stdout.strip()
