"""Authoring-Time ML Service for NETI Item Quality & Verification.

Exposes analyze_item(item) for offline authoring, QA, and bank auditing.
Strictly OFF the live exam-time critical path.

Uses saved model artifacts only (zero retraining during inference).
Enforces explicit confidence, fallback provenance, and provisional IRT status.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Add repository root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROOT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.dataset.schema import IRTParameters, Item, ItemKindEnum
from ml.m1_tagger.infer import M1InferenceEngine
from ml.m2_difficulty.infer import M2InferenceEngine
from ml.validators.symbolic import (
    SymbolicValidationError,
    evaluate_symbolic_expression,
    validate_template_algebra,
)

DEFAULT_M1_PATH = ROOT_DIR / "artifacts" / "models" / "m1_concept_tagger.joblib"
DEFAULT_M2_PATH = ROOT_DIR / "artifacts" / "models" / "m2_difficulty_predictor.joblib"


class AuthoringMLPipeline:
    """Authoring-time analysis pipeline using pre-trained offline model artifacts."""

    def __init__(
        self,
        m1_path: Union[str, Path] = DEFAULT_M1_PATH,
        m2_path: Union[str, Path] = DEFAULT_M2_PATH,
        confidence_threshold: float = 0.35,
    ) -> None:
        self.m1_path = Path(m1_path)
        self.m2_path = Path(m2_path)
        self.confidence_threshold = confidence_threshold

        self.m1_engine = M1InferenceEngine(self.m1_path, confidence_threshold=self.confidence_threshold)
        self.m2_engine = M2InferenceEngine(self.m2_path)

    def analyze_item(self, item: Union[Item, dict]) -> Dict[str, Any]:
        """Perform comprehensive authoring-time ML analysis and symbolic validation on an item.
        
        Returns structured analysis with explicit provisional status and issue tracking.
        """
        if isinstance(item, Item):
            item_dict = item.model_dump()
        else:
            item_dict = dict(item)

        stem = item_dict.get("stem", "")
        options = item_dict.get("options", [])
        kind = item_dict.get("kind", "static")

        # -------------------------------------------------------------
        # 1. M1 Concept Tagging & Metadata Inference
        # -------------------------------------------------------------
        m1_res = self.m1_engine.predict_one(stem=stem, options=options)
        src = m1_res.get("source", "ml")
        fallback_used = bool(src == "taxonomy_fallback")

        m1_output = {
            "subject": m1_res["subject"],
            "chapter": m1_res["chapter"],
            "concept_tags": m1_res["concept_tags"],
            "cognitive_level": m1_res["cognitive_level"],
            "confidence": float(m1_res.get("subject_confidence", 0.0)),
            "source": src,
            "fallback_used": fallback_used,
        }

        # -------------------------------------------------------------
        # 2. M2 Difficulty & Discrimination Estimation
        # -------------------------------------------------------------
        # Predict difficulty using inferred/existing context
        target_subject = item_dict.get("subject", m1_res["subject"])
        target_chapter = item_dict.get("chapter", m1_res["chapter"])
        target_cognitive = item_dict.get("cognitive_level", m1_res["cognitive_level"])

        m2_res = self.m2_engine.predict_one(
            stem=stem,
            subject=target_subject,
            chapter=target_chapter,
            cognitive_level=target_cognitive,
            options=options,
        )

        m2_output = {
            "a": m2_res["a"],
            "b": m2_res["b"],
            "c": "0.25",
            "provisional": True,
            "model_version": "m2_ridge_v0.1",
            "dataset_version": "curated_mock_v0.1",
            "description": "Predicted provisional IRT estimate (structural proxy)",
        }

        # -------------------------------------------------------------
        # 3. Symbolic Validation (for template and algebraic consistency)
        # -------------------------------------------------------------
        validation_issues: List[str] = []
        symbolic_passed = True

        if kind == "template" or ("params" in item_dict and item_dict["params"]):
            params = item_dict.get("params", {})
            answer_expr = item_dict.get("answer", "")
            distractor_exprs = item_dict.get("distractors", [])
            unit = item_dict.get("unit", "")

            if not params or not answer_expr:
                validation_issues.append("Template item missing required params or answer expression")
                symbolic_passed = False
            else:
                try:
                    val_res = validate_template_algebra(
                        stem=stem,
                        params=params,
                        answer_expr=answer_expr,
                        distractor_exprs=distractor_exprs,
                        unit=unit,
                    )
                    if not val_res["is_valid"]:
                        symbolic_passed = False
                        for col in val_res.get("collisions", []):
                            if "distractor_collision" in col:
                                validation_issues.append(f"Distractor collision with answer at params {col['params']}")
                            if "duplicate_distractors" in col:
                                validation_issues.append(f"Duplicate distractors generated at params {col['params']}")
                except Exception as e:
                    symbolic_passed = False
                    validation_issues.append(f"Symbolic evaluation error: {e}")

        # Check options for static items
        if kind == "static" and options:
            if len(options) != 4:
                validation_issues.append(f"Static item has {len(options)} options, expected exactly 4")
            correct = item_dict.get("correct")
            if correct and correct not in options:
                validation_issues.append(f"Correct answer '{correct}' is not in options list")

        validation_output = {
            "symbolic": symbolic_passed,
            "issues": validation_issues,
        }

        return {
            "m1": m1_output,
            "m2": m2_output,
            "validation": validation_output,
        }


# Global singleton pipeline instance
_PIPELINE_INSTANCE: Optional[AuthoringMLPipeline] = None


def get_authoring_pipeline() -> AuthoringMLPipeline:
    global _PIPELINE_INSTANCE
    if _PIPELINE_INSTANCE is None:
        _PIPELINE_INSTANCE = AuthoringMLPipeline()
    return _PIPELINE_INSTANCE


def analyze_item(item: Union[Item, dict]) -> Dict[str, Any]:
    """Convenience functional interface for item analysis."""
    pipeline = get_authoring_pipeline()
    return pipeline.analyze_item(item)
