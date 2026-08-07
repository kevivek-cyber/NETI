"""Unit tests for SymPy symbolic validation and distractor collision verification."""

from __future__ import annotations

import pytest

from ml.validators.symbolic import (
    SymbolicValidationError,
    evaluate_symbolic_expression,
    validate_template_algebra,
)


def test_evaluate_symbolic_valid_physics():
    params = {"v": 20, "angle": 30}
    # R = v^2 * sin(2*30°) / 10 = 400 * sin(60°) / 10 = 40 * (sqrt(3)/2) = 20 * 1.73205 = 34.64
    expr = "v**2 * sin(2*radians(angle)) / 10"
    res = evaluate_symbolic_expression(expr, params)
    assert res == "34.64"


def test_evaluate_symbolic_handles_division_and_trig():
    params = {"m": 4, "v": 5}
    # KE = 1/2 * m * v^2 = 0.5 * 4 * 25 = 50.00
    expr = "m * v**2 / 2"
    res = evaluate_symbolic_expression(expr, params)
    assert res == "50.00"


def test_reject_division_by_zero():
    params = {"x": 0}
    with pytest.raises(SymbolicValidationError):
        evaluate_symbolic_expression("10 / x", params)


def test_template_algebra_validator_detects_collision():
    # Intentionally bad distractor that equals answer when angle=45
    params = {"v": [10, 20], "angle": [45]}
    answer_expr = "v**2 * sin(2*radians(angle)) / 10"  # at 45 deg, sin(90)=1 -> v^2/10
    colliding_distractor = ["v**2 / 10", "v/2", "v*2"]  # "v**2/10" is identical to answer!

    validation = validate_template_algebra(
        stem="Test projectile",
        params=params,
        answer_expr=answer_expr,
        distractor_exprs=colliding_distractor,
    )
    assert not validation["is_valid"]
    assert validation["num_collisions"] > 0


def test_template_algebra_validator_passes_clean_template():
    params = {"m": [2, 4, 6], "a": [3, 5, 8]}
    answer_expr = "m * a"
    distractors = ["m + a", "m / a", "m * a * 10"]

    validation = validate_template_algebra(
        stem="Test Newton 2nd law",
        params=params,
        answer_expr=answer_expr,
        distractor_exprs=distractors,
    )
    assert validation["is_valid"]
    assert validation["num_collisions"] == 0
