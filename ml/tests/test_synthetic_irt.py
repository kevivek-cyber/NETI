"""Unit tests for synthetic 3PL IRT data generation and calibration."""

from __future__ import annotations

import numpy as np
import pytest

from ml.dataset.synthetic import (
    compute_3pl_probability,
    generate_synthetic_dataset,
)
from ml.m2_difficulty.irt import calibrate_3pl_response_matrix, run_synthetic_calibration_experiment


def test_synthetic_generation_determinism():
    data1 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)
    data2 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)

    np.testing.assert_array_equal(data1.student_thetas, data2.student_thetas)
    np.testing.assert_array_equal(data1.true_b, data2.true_b)
    np.testing.assert_array_equal(data1.true_a, data2.true_a)
    np.testing.assert_array_equal(data1.response_matrix, data2.response_matrix)


def test_different_seeds_diverge():
    data1 = generate_synthetic_dataset(num_students=100, num_items=50, seed=42)
    data2 = generate_synthetic_dataset(num_students=100, num_items=50, seed=99)

    assert not np.array_equal(data1.student_thetas, data2.student_thetas)
    assert not np.array_equal(data1.response_matrix, data2.response_matrix)


def test_response_matrix_shape_and_probabilities():
    N, J = 200, 80
    data = generate_synthetic_dataset(num_students=N, num_items=J, seed=123)

    assert data.response_matrix.shape == (N, J)
    assert data.probability_matrix.shape == (N, J)
    assert set(np.unique(data.response_matrix)).issubset({0, 1})
    assert np.all(data.probability_matrix >= 0.25)  # Guessing floor c=0.25
    assert np.all(data.probability_matrix <= 1.0)


def test_synthetic_items_schema_validity():
    data = generate_synthetic_dataset(num_students=50, num_items=20, seed=42)
    assert len(data.items) == 20
    for item in data.items:
        assert item.bank_version == "synthetic-v0.1"
        assert item.irt.c == "0.25"
        assert float(item.irt.a) > 0.0


def test_3pl_calibration_experiment_convergence():
    # Run calibration with small synthetic dataset for fast test
    exp = run_synthetic_calibration_experiment(num_students=500, num_items=30, seed=42)

    assert "difficulty_b" in exp
    assert "discrimination_a" in exp
    assert exp["difficulty_b"]["rmse"] < 1.2  # Reasonable recovery with proxy theta
    assert exp["difficulty_b"]["pearson_r"] > 0.60  # Positive rank correlation
