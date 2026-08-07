"""Inference CLI and module for M2 Difficulty Predictor.

Loads the saved artifact from ml/artifacts/models/m2_difficulty_predictor.joblib
and performs offline predictions of 3PL parameters a, b, c.
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
from ml.m2_difficulty.baseline import M2DifficultyPredictorBaseline

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "models" / "m2_difficulty_predictor.joblib"


class M2InferenceEngine:
    def __init__(self, model_path: Union[str, Path] = DEFAULT_MODEL_PATH) -> None:
        self.model_path = Path(model_path)
        self.model = M2DifficultyPredictorBaseline.load(self.model_path)

    def predict_one(
        self,
        stem: str,
        subject: str = "physics",
        chapter: str = "kinematics",
        cognitive_level: str = "application",
        options: List[str] = None,
    ) -> Dict[str, str]:
        """Predict fixed-precision IRT parameters for a single question."""
        item_dict = {
            "stem": stem,
            "subject": subject,
            "chapter": chapter,
            "cognitive_level": cognitive_level,
            "options": options or [],
        }
        params = self.model.predict([item_dict])[0]
        return {
            "a": params.a,
            "b": params.b,
            "c": params.c,
        }

    def predict_batch(self, questions: List[Union[dict, str]]) -> List[IRTParameters]:
        """Predict IRT parameters for a batch of questions."""
        return self.model.predict(questions)


def main() -> None:
    parser = argparse.ArgumentParser(description="M2 Difficulty Predictor Inference")
    parser.add_argument("--stem", type=str, required=True, help="Question stem text")
    parser.add_argument("--subject", type=str, default="physics", help="Subject")
    parser.add_argument("--chapter", type=str, default="kinematics", help="Chapter")
    parser.add_argument("--cognitive-level", type=str, default="application", help="Cognitive level")
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH), help="Path to saved model")
    args = parser.parse_args()

    engine = M2InferenceEngine(args.model_path)
    result = engine.predict_one(
        stem=args.stem,
        subject=args.subject,
        chapter=args.chapter,
        cognitive_level=args.cognitive_level,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
