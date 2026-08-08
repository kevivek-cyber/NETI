"""Build model artifacts on demand so the suite runs on a fresh clone.

`test_authoring_pipeline.py` loads `artifacts/models/*.joblib`, but those
are gitignored — trained binaries are regenerable output, not source, and
committing them puts a few MB of churn in every diff.

So the artifacts are trained here instead, once per session, if absent.
The suite then passes on a clean checkout and in CI with no manual step.

Training on the curated_mock dataset takes a few seconds. Note what that
means for the tests that depend on this fixture: they verify the pipeline
*runs and is deterministic*. They say nothing about whether the models
predict anything real — the labels come from a formula whose terms are
also model features (see ml/README or m2_metrics.json).
"""

from __future__ import annotations

from pathlib import Path

import pytest

ML_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ML_ROOT / "artifacts" / "models"
M1_PATH = MODELS_DIR / "m1_concept_tagger.joblib"
M2_PATH = MODELS_DIR / "m2_difficulty_predictor.joblib"


@pytest.fixture(scope="session", autouse=True)
def model_artifacts() -> None:
    """Train M1 and M2 once if their artifacts are missing.

    autouse so tests that load artifacts indirectly — through
    AuthoringMLPipeline or the bank tools — are covered without each one
    having to remember to request the fixture.
    """
    if M1_PATH.exists() and M2_PATH.exists():
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if not M1_PATH.exists():
        from ml.m1_tagger.train import train_m1_pipeline

        train_m1_pipeline()

    if not M2_PATH.exists():
        from ml.m2_difficulty.train import train_m2_pipeline

        train_m2_pipeline()

    missing = [p.name for p in (M1_PATH, M2_PATH) if not p.exists()]
    if missing:
        pytest.fail(
            "training completed but these artifacts were not written: "
            f"{missing}. Check the output paths in the train_* pipelines."
        )
