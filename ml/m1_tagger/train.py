"""Training and evaluation pipeline for M1 Concept Tagger Baseline.

Evaluates:
- Subject: Accuracy, Macro F1, Weighted F1, Micro F1, Majority Baseline, Confusion Matrix
- Chapter: Accuracy, Macro F1, Weighted F1, Micro F1, Majority Baseline
- Cognitive Level: Accuracy, Macro F1, Weighted F1, Micro F1, Majority Baseline, Confusion Matrix
- Concept Tags: Multi-label Micro F1, Macro F1, Hamming Loss

Saves versioned artifact and metrics JSON.
"""

from __future__ import annotations

import collections
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    hamming_loss,
)

from ..dataset.curated_mock import generate_curated_mock_dataset
from ..dataset.ingest import create_leakage_safe_split, load_items_from_json
from ..dataset.schema import Item
from .baseline import M1ConceptTaggerBaseline

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "models" / "m1_concept_tagger.joblib"
DEFAULT_METRICS_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "metrics" / "m1_metrics.json"

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



def compute_classification_diagnostics(y_train: list, y_test: list, y_pred: list, task_name: str) -> Dict[str, Any]:
    """Compute detailed evaluation diagnostics including majority baseline and confusion matrix."""
    train_counts = collections.Counter(y_train)
    test_counts = collections.Counter(y_test)
    
    # Majority baseline (predict most common class in train set)
    majority_class = train_counts.most_common(1)[0][0]
    majority_preds = [majority_class] * len(y_test)
    majority_acc = accuracy_score(y_test, majority_preds)

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    micro_f1 = f1_score(y_test, y_pred, average="micro", zero_division=0)

    # Unique sorted labels for confusion matrix
    labels = sorted(list(set(y_train) | set(y_test)))
    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    return {
        "task": task_name,
        "num_classes": len(labels),
        "classes": labels,
        "train_class_distribution": dict(train_counts),
        "test_class_distribution": dict(test_counts),
        "majority_class": majority_class,
        "majority_baseline_accuracy": float(majority_acc),
        "model_accuracy": float(acc),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "micro_f1": float(micro_f1),
        "beats_majority_baseline": bool(acc > majority_acc),
        "confusion_matrix": cm,
    }


def evaluate_tagger(
    model: M1ConceptTaggerBaseline,
    train_items: List[Item],
    test_items: List[Item],
) -> Dict[str, Any]:
    """Evaluate M1 tagger against majority baselines and return complete diagnostics."""
    predictions = model.predict(test_items)

    y_train_subj = [it.subject.value for it in train_items]
    y_test_subj = [it.subject.value for it in test_items]
    y_pred_subj = [p["subject"] for p in predictions]

    y_train_chap = [it.chapter for it in train_items]
    y_test_chap = [it.chapter for it in test_items]
    y_pred_chap = [p["chapter"] for p in predictions]

    y_train_cog = [it.cognitive_level.value for it in train_items]
    y_test_cog = [it.cognitive_level.value for it in test_items]
    y_pred_cog = [p["cognitive_level"] for p in predictions]

    # Binary representations for multi-label concept tags
    mlb = model.mlb_concepts
    known_classes = set(mlb.classes_)
    y_test_concepts = [it.concept_tags for it in test_items]
    y_pred_concepts = [p["concept_tags"] for p in predictions]

    y_true_filtered = [[c for c in tags if c in known_classes] for tags in y_test_concepts]
    y_pred_filtered = [[c for c in tags if c in known_classes] for tags in y_pred_concepts]

    Y_true_bin = mlb.transform(y_true_filtered)
    Y_pred_bin = mlb.transform(y_pred_filtered)

    subj_diag = compute_classification_diagnostics(y_train_subj, y_test_subj, y_pred_subj, "subject")
    chap_diag = compute_classification_diagnostics(y_train_chap, y_test_chap, y_pred_chap, "chapter")
    cog_diag = compute_classification_diagnostics(y_train_cog, y_test_cog, y_pred_cog, "cognitive_level")

    concept_metrics = {
        "micro_f1": float(f1_score(Y_true_bin, Y_pred_bin, average="micro", zero_division=0)),
        "macro_f1": float(f1_score(Y_true_bin, Y_pred_bin, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(Y_true_bin, Y_pred_bin, average="weighted", zero_division=0)),
        "hamming_loss": float(hamming_loss(Y_true_bin, Y_pred_bin)),
    }

    metrics = {
        "num_train_items": len(train_items),
        "num_test_items": len(test_items),
        "subject": subj_diag,
        "chapter": chap_diag,
        "cognitive_level": cog_diag,
        "concept_tags": concept_metrics,
    }
    return metrics


def train_m1_pipeline(
    items: Optional[List[Item]] = None,
    model_output_path: Path = DEFAULT_MODEL_PATH,
    metrics_output_path: Path = DEFAULT_METRICS_PATH,
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute end-to-end M1 training, evaluation, and artifact serialization."""
    if items is None:
        items = generate_curated_mock_dataset(target_count=350, seed=seed)

    train_items, val_items, test_items = create_leakage_safe_split(
        items,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=seed,
    )

    model = M1ConceptTaggerBaseline(random_state=seed)
    model.fit(train_items)

    metrics = evaluate_tagger(model, train_items, test_items)
    metrics_payload = {
        "model": "M1ConceptTaggerBaseline",
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
    train_m1_pipeline()
