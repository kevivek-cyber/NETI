"""Inference CLI and module for M1 Concept Tagger.

Loads the saved artifact from ml/artifacts/models/m1_concept_tagger.joblib
and performs offline predictions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dataset.schema import IRTParameters
from ml.m1_tagger.baseline import M1ConceptTaggerBaseline
from ml.m1_tagger.fallback import TaxonomyRuleFallback

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "models" / "m1_concept_tagger.joblib"


class M1InferenceEngine:
    def __init__(self, model_path: Union[str, Path] = DEFAULT_MODEL_PATH, confidence_threshold: float = 0.35) -> None:
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.model = M1ConceptTaggerBaseline.load(self.model_path)
        self.fallback = TaxonomyRuleFallback()

    def predict_one(self, stem: str, options: List[str] = None) -> Dict[str, Any]:
        """Predict metadata for a single question stem + optional options.
        
        Uses ML classifier first; if confidence is below threshold, routes to taxonomy fallback.
        """
        payload = {"stem": stem}
        if options:
            payload["options"] = options
        ml_pred = self.model.predict([payload])[0]

        # Check if ML confidence is sufficient
        if ml_pred["subject_confidence"] >= self.confidence_threshold:
            ml_pred["source"] = "ml"
            return ml_pred

        # Otherwise route to deterministic taxonomy fallback
        fallback_pred = self.fallback.fallback_predict(stem, options)
        return fallback_pred

    def predict_batch(self, questions: List[Union[str, dict]]) -> List[Dict[str, Any]]:
        """Predict metadata for a batch of questions."""
        return self.model.predict(questions)


def main() -> None:
    parser = argparse.ArgumentParser(description="M1 Concept Tagger Inference")
    parser.add_argument("--stem", type=str, required=True, help="Question stem text")
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH), help="Path to saved model")
    args = parser.parse_args()

    engine = M1InferenceEngine(args.model_path)
    result = engine.predict_one(args.stem)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
