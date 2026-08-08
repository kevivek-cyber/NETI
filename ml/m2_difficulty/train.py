"""Training and evaluation pipeline for M2 Difficulty & Discrimination Predictor.

Evaluates against the Mean Predictor Baseline:
- Difficulty b: MAE, RMSE, Pearson r, Spearman rho, R^2
- Discrimination a: MAE, RMSE, Pearson r, Spearman rho, R^2
- Comparison against Mean Baseline (asserts model beats trivial baseline)

Saves versioned model artifact and metrics JSON.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error

from ..dataset.curated_mock import generate_curated_mock_dataset
from ..dataset.ingest import create_leakage_safe_split
from ..dataset.schema import Item
from .baseline import M2DifficultyPredictorBaseline

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "models" / "m2_difficulty_predictor.joblib"
DEFAULT_METRICS_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "metrics" / "m2_metrics.json"

# Every metrics file must state where its labels came from. Without this,
# a score computed against generated labels is indistinguishable from a
# measurement, and gets quoted as one.
SYNTHETIC_PROVENANCE = {
    "label_origin_kind": "synthetic",
    "circular": True,
    "source": "ml/dataset/curated_mock.py",
    "note": (
        "NOT A RESULT. curated_mock.py writes both the questions and their "
        "labels, and the label formula's terms (cognitive level, maths-symbol "
        "presence, source template) are also model input features. A high "
        "score is therefore guaranteed before training and measures formula "
        "recovery, not prediction. These metrics validate that the pipeline "
        "runs end to end. Do not quote them as model performance."
    ),
    "for_a_real_number": (
        "Train against measured difficulty (real student responses) or "
        "expert-rated labels. Published text-based work reports Pearson r of "
        "0.38-0.60 typically, 0.77-0.87 at the state of the art."
    ),
}



def evaluate_regression_diagnostics(y_train: np.ndarray, y_test: np.ndarray, y_pred: np.ndarray, param_name: str) -> Dict[str, Any]:
    """Compute detailed regression diagnostics compared against a trivial Mean Predictor baseline."""
    mean_val = float(np.mean(y_train))
    mean_preds = np.full_like(y_test, mean_val)

    mean_baseline_mae = float(mean_absolute_error(y_test, mean_preds))
    mean_baseline_rmse = float(root_mean_squared_error(y_test, mean_preds))

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(root_mean_squared_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    # Pearson and Spearman correlations
    pr, _ = pearsonr(y_test, y_pred) if len(y_test) > 2 and np.std(y_pred) > 1e-6 and np.std(y_test) > 1e-6 else (0.0, 1.0)
    sr, _ = spearmanr(y_test, y_pred) if len(y_test) > 2 and np.std(y_pred) > 1e-6 and np.std(y_test) > 1e-6 else (0.0, 1.0)

    return {
        "parameter": param_name,
        "mean_baseline_mae": mean_baseline_mae,
        "mean_baseline_rmse": mean_baseline_rmse,
        "model_mae": mae,
        "model_rmse": rmse,
        "r2_score": r2,
        "pearson_r": float(pr),
        "spearman_rho": float(sr),
        "beats_mean_baseline_rmse": bool(rmse < mean_baseline_rmse),
        "beats_mean_baseline_mae": bool(mae < mean_baseline_mae),
    }


def evaluate_difficulty_predictor(
    model: M2DifficultyPredictorBaseline,
    train_items: List[Item],
    test_items: List[Item],
) -> Dict[str, Any]:
    """Evaluate M2 baseline on test items and compare with Mean baseline."""
    predictions = model.predict(test_items)

    y_train_b = np.array([float(it.irt.b) for it in train_items])
    y_test_b = np.array([float(it.irt.b) for it in test_items])
    y_pred_b = np.array([float(p.b) for p in predictions])

    y_train_a = np.array([float(it.irt.a) for it in train_items])
    y_test_a = np.array([float(it.irt.a) for it in test_items])
    y_pred_a = np.array([float(p.a) for p in predictions])

    b_diag = evaluate_regression_diagnostics(y_train_b, y_test_b, y_pred_b, "b_difficulty")
    a_diag = evaluate_regression_diagnostics(y_train_a, y_test_a, y_pred_a, "a_discrimination")

    metrics = {
        "num_train_items": len(train_items),
        "num_test_items": len(test_items),
        "difficulty_b": b_diag,
        "discrimination_a": a_diag,
        "fixed_c": "0.25",
    }
    return metrics


def train_m2_pipeline(
    items: Optional[List[Item]] = None,
    model_output_path: Path = DEFAULT_MODEL_PATH,
    metrics_output_path: Path = DEFAULT_METRICS_PATH,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute end-to-end M2 training, evaluation, and artifact serialization."""
    if items is None:
        items = generate_curated_mock_dataset(target_count=350, seed=seed)

    train_items, val_items, test_items = create_leakage_safe_split(
        items,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=seed,
    )

    model = M2DifficultyPredictorBaseline(alpha=1.0, random_state=seed)
    model.fit(train_items)

    metrics = evaluate_difficulty_predictor(model, train_items, test_items)
    metrics_payload = {
        "model": "M2DifficultyPredictorBaseline",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "seed": seed,
        "dataset": {
            "total_items": len(items),
            "train_items": len(train_items),
            "val_items": len(val_items),
            "test_items": len(test_items),
        },
        "metrics": metrics,
    }

    # Save model and metrics
    model.save(model_output_path)
    metrics_payload["data_provenance"] = SYNTHETIC_PROVENANCE
    metrics_output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_output_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    return metrics_payload


if __name__ == "__main__":
    train_m2_pipeline()
