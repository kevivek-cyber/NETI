"""Unit tests for M2 Difficulty Predictor baseline."""

from __future__ import annotations

from pathlib import Path
import pytest

from ml.dataset.synthetic import generate_synthetic_dataset
from ml.m2_difficulty.baseline import M2DifficultyPredictorBaseline
from ml.m2_difficulty.infer import M2InferenceEngine
from ml.m2_difficulty.train import train_m2_pipeline


def test_m2_training_and_clamped_output():
    synth = generate_synthetic_dataset(num_students=200, num_items=60, seed=42)
    predictor = M2DifficultyPredictorBaseline(random_state=42)
    predictor.fit(synth.items)

    test_stem = "Calculate the kinetic energy of a mass m moving at speed v."
    preds = predictor.predict([test_stem])
    assert len(preds) == 1
    p = preds[0]

    # IRT parameter format checks
    assert isinstance(p.a, str)
    assert isinstance(p.b, str)
    assert p.c == "0.25"

    a_flt, b_flt, c_flt = p.to_floats()
    assert 0.2 <= a_flt <= 2.5
    assert -3.0 <= b_flt <= 3.0
    assert c_flt == 0.25


def test_m2_save_and_load(tmp_path: Path):
    synth = generate_synthetic_dataset(num_students=100, num_items=40, seed=42)
    model_file = tmp_path / "test_m2.joblib"

    predictor = M2DifficultyPredictorBaseline(random_state=42)
    predictor.fit(synth.items)
    predictor.save(model_file)

    engine = M2InferenceEngine(model_path=model_file)
    res = engine.predict_one("What is the speed of light in a vacuum?")
    assert "a" in res and "b" in res and "c" in res
    assert res["c"] == "0.25"


def test_m2_pipeline_metrics_generation(tmp_path: Path):
    model_file = tmp_path / "m2_model.joblib"
    metrics_file = tmp_path / "m2_metrics.json"

    metrics_payload = train_m2_pipeline(
        model_output_path=model_file,
        metrics_output_path=metrics_file,
        seed=42,
    )

    assert model_file.exists()
    assert metrics_file.exists()
    assert "difficulty_b" in metrics_payload["metrics"]
    assert "discrimination_a" in metrics_payload["metrics"]
    assert metrics_payload["metrics"]["difficulty_b"]["model_mae"] < 2.0
