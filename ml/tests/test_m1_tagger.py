"""Unit tests for M1 Concept Tagger baseline."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from ml.dataset.synthetic import generate_synthetic_dataset
from ml.m1_tagger.baseline import M1ConceptTaggerBaseline
from ml.m1_tagger.infer import M1InferenceEngine
from ml.m1_tagger.train import train_m1_pipeline


def test_m1_training_and_inference():
    synth = generate_synthetic_dataset(num_students=200, num_items=60, seed=42)
    items = synth.items

    tagger = M1ConceptTaggerBaseline(random_state=42)
    tagger.fit(items)

    test_stem = "A body accelerates under force according to Newton second law in mechanics."
    preds = tagger.predict([test_stem])
    assert len(preds) == 1
    p = preds[0]

    assert p["subject"] in ["physics", "chemistry", "botany", "zoology"]
    assert "chapter" in p
    assert "cognitive_level" in p
    assert isinstance(p["concept_tags"], list)
    assert len(p["concept_tags"]) > 0


def test_m1_save_and_load(tmp_path: Path):
    synth = generate_synthetic_dataset(num_students=100, num_items=40, seed=42)
    model_file = tmp_path / "test_m1.joblib"

    tagger = M1ConceptTaggerBaseline(random_state=42)
    tagger.fit(synth.items)
    tagger.save(model_file)

    loaded_engine = M1InferenceEngine(model_path=model_file)
    pred = loaded_engine.predict_one("What is the primary function of chloroplast in photosynthesis?")
    assert pred["subject"] == "botany"
    assert "photosynthesis" in pred["chapter"] or "cell_biology" in pred["chapter"]


def test_m1_pipeline_metrics_generation(tmp_path: Path):
    model_file = tmp_path / "m1_model.joblib"
    metrics_file = tmp_path / "m1_metrics.json"

    metrics_payload = train_m1_pipeline(
        model_output_path=model_file,
        metrics_output_path=metrics_file,
        seed=42,
    )

    assert model_file.exists()
    assert metrics_file.exists()
    assert "subject" in metrics_payload["metrics"]
    assert "concept_tags" in metrics_payload["metrics"]
    assert 0.0 <= metrics_payload["metrics"]["subject"]["model_accuracy"] <= 1.0
