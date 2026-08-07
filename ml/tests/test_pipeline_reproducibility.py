"""Unit tests for ML pipeline reproducibility and determinism."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest

from ml.dataset.synthetic import generate_synthetic_dataset
from ml.m1_tagger.baseline import M1ConceptTaggerBaseline
from ml.m2_difficulty.baseline import M2DifficultyPredictorBaseline


def test_m1_training_is_strictly_reproducible():
    synth1 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)
    synth2 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)

    tagger1 = M1ConceptTaggerBaseline(random_state=42).fit(synth1.items)
    tagger2 = M1ConceptTaggerBaseline(random_state=42).fit(synth2.items)

    test_samples = [
        "A force acts on mass m accelerating it.",
        "Calculate the molar mass of water.",
        "Structure of DNA double helix in genetics.",
    ]

    preds1 = tagger1.predict(test_samples)
    preds2 = tagger2.predict(test_samples)

    assert preds1 == preds2


def test_m2_training_is_strictly_reproducible():
    synth1 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)
    synth2 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)

    m2_1 = M2DifficultyPredictorBaseline(alpha=1.0, random_state=42).fit(synth1.items)
    m2_2 = M2DifficultyPredictorBaseline(alpha=1.0, random_state=42).fit(synth2.items)

    test_samples = [
        "A force acts on mass m accelerating it.",
        "Calculate the molar mass of water.",
        "Structure of DNA double helix in genetics.",
    ]

    res1 = [p.to_floats() for p in m2_1.predict(test_samples)]
    res2 = [p.to_floats() for p in m2_2.predict(test_samples)]

    assert res1 == res2
