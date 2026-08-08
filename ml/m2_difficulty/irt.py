"""3-Parameter Logistic (3PL) IRT Parameter Calibration Module.

Calibrates:
- Item difficulty (b): location on latent theta scale [-3.0, +3.0]
- Item discrimination (a): slope parameter [0.2, 2.5]
- Guessing floor (c): fixed to 0.25 for 4-option MCQs

Implements numerical optimization via Joint Maximum Likelihood / Logistic Proxy
with bounded Newton-Raphson / L-BFGS-B estimation.
Serializes outputs strictly to fixed-precision strings (RFC 8785).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import minimize

from ..dataset.schema import IRTParameters, format_fixed_precision
from ..dataset.synthetic import compute_3pl_probability, generate_synthetic_dataset


@dataclass
class CalibrationResult:
    """Summary of 3PL calibration results across J items."""
    item_ids: List[str]
    estimated_a: np.ndarray  # Shape (J,)
    estimated_b: np.ndarray  # Shape (J,)
    estimated_c: np.ndarray  # Shape (J,)
    irt_parameters: List[IRTParameters]
    converged: bool
    iterations: int
    log_likelihood: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_items": len(self.item_ids),
            "converged": self.converged,
            "iterations": self.iterations,
            "log_likelihood": float(self.log_likelihood),
            "mean_estimated_b": float(np.mean(self.estimated_b)),
            "mean_estimated_a": float(np.mean(self.estimated_a)),
            "mean_estimated_c": float(np.mean(self.estimated_c)),
        }


def _item_negative_log_likelihood(
    params: np.ndarray,
    thetas: np.ndarray,
    responses: np.ndarray,
    c_fixed: float = 0.25,
) -> float:
    """Negative log likelihood for a single item under 3PL with fixed c."""
    a, b = params
    probs = compute_3pl_probability(thetas, np.array([a]), np.array([b]), np.array([c_fixed])).flatten()
    # Epsilon clip for numerical stability
    eps = 1e-12
    probs = np.clip(probs, eps, 1.0 - eps)
    nll = -np.sum(responses * np.log(probs) + (1.0 - responses) * np.log(1.0 - probs))
    return float(nll)


def calibrate_3pl_response_matrix(
    response_matrix: np.ndarray,
    item_ids: Optional[List[str]] = None,
    c_fixed: float = 0.25,
    max_iter: int = 100,
    a_bounds: Tuple[float, float] = (0.2, 2.5),
    b_bounds: Tuple[float, float] = (-3.0, 3.0),
) -> CalibrationResult:
    """Estimate 3PL IRT parameters from an (N, J) binary response matrix.
    
    Uses standardized score proxy for student ability theta, followed by
    constrained quasi-Newton optimization (L-BFGS-B) per item.
    """
    N, J = response_matrix.shape
    if item_ids is None:
        item_ids = [f"ITEM-{j:04d}" for j in range(J)]
    elif len(item_ids) != J:
        raise ValueError(f"item_ids length ({len(item_ids)}) must match number of items ({J})")

    # Step 1: Proxy student abilities theta via standardized total test score
    raw_scores = np.sum(response_matrix, axis=1).astype(float)
    mean_score = np.mean(raw_scores)
    std_score = np.std(raw_scores)
    if std_score < 1e-6:
        std_score = 1.0
    
    # Transform raw score to z-score proxy for theta ~ N(0, 1)
    student_thetas = (raw_scores - mean_score) / std_score

    # Step 2: Calibrate each item independently given the proxy abilities
    est_a = np.zeros(J, dtype=float)
    est_b = np.zeros(J, dtype=float)
    est_c = np.full(J, c_fixed, dtype=float)
    irt_param_list: List[IRTParameters] = []

    total_nll = 0.0
    all_converged = True
    total_iters = 0

    for j in range(J):
        resp_j = response_matrix[:, j]
        p_j = np.mean(resp_j)

        # Initial heuristic for b: inverse logistic of difficulty
        # Clamp p_j away from extremes
        p_clamped = np.clip(p_j, 0.05, 0.95)
        # Invert: p = c + (1-c)/(1+exp(-a*(0-b))) -> logit approx
        b_init = -np.log((p_clamped - c_fixed * 0.5) / (1.0 - p_clamped + 1e-4) + 1e-4)
        b_init = float(np.clip(b_init, b_bounds[0], b_bounds[1]))
        a_init = 1.0

        res = minimize(
            _item_negative_log_likelihood,
            x0=np.array([a_init, b_init]),
            args=(student_thetas, resp_j, c_fixed),
            method="L-BFGS-B",
            bounds=[a_bounds, b_bounds],
            options={"maxiter": max_iter},
        )

        if not res.success:
            all_converged = False

        total_iters += res.nit
        total_nll += res.fun

        a_opt, b_opt = res.x
        est_a[j] = float(a_opt)
        est_b[j] = float(b_opt)

        # Format to 2-decimal fixed-precision strings
        irt_param_list.append(IRTParameters.from_floats(est_a[j], est_b[j], est_c[j]))

    return CalibrationResult(
        item_ids=item_ids,
        estimated_a=est_a,
        estimated_b=est_b,
        estimated_c=est_c,
        irt_parameters=irt_param_list,
        converged=all_converged,
        iterations=total_iters,
        log_likelihood=-total_nll,
        metadata={
            "num_students": N,
            "num_items": J,
            "c_fixed": c_fixed,
            "a_bounds": a_bounds,
            "b_bounds": b_bounds,
        },
    )


def run_synthetic_calibration_experiment(
    num_students: int = 2000,
    num_items: int = 500,
    seed: int = 42,
) -> Dict[str, Any]:
    """Synthetic experiment: Generate items -> generate responses -> calibrate -> compare true vs estimated."""
    synth = generate_synthetic_dataset(num_students=num_students, num_items=num_items, seed=seed)
    
    calib = calibrate_3pl_response_matrix(
        response_matrix=synth.response_matrix,
        item_ids=synth.item_ids,
        c_fixed=0.25,
    )

    mae_b = float(np.mean(np.abs(calib.estimated_b - synth.true_b)))
    rmse_b = float(np.sqrt(np.mean((calib.estimated_b - synth.true_b) ** 2)))
    
    mae_a = float(np.mean(np.abs(calib.estimated_a - synth.true_a)))
    rmse_a = float(np.sqrt(np.mean((calib.estimated_a - synth.true_a) ** 2)))

    pearson_b = float(np.corrcoef(calib.estimated_b, synth.true_b)[0, 1])
    pearson_a = float(np.corrcoef(calib.estimated_a, synth.true_a)[0, 1])

    return {
        "experiment": "3PL Synthetic Calibration",
        "num_students": num_students,
        "num_items": num_items,
        "seed": seed,
        "difficulty_b": {
            "mae": mae_b,
            "rmse": rmse_b,
            "pearson_r": pearson_b,
        },
        "discrimination_a": {
            "mae": mae_a,
            "rmse": rmse_a,
            "pearson_r": pearson_a,
        },
        "log_likelihood": calib.log_likelihood,
        "calibration_summary": calib.to_dict(),
    }
