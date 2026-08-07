"""Feature-based M2 Difficulty & Discrimination Predictor Baseline.

Extracts text, structural, readability, LaTeX, and cognitive features from questions
to predict 3PL IRT parameters:
- b: difficulty in logits [-3.00, +3.00]
- a: discrimination in [0.20, 2.50]
- c: fixed guessing floor "0.25"
"""

from __future__ import annotations

import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge

from ..dataset.schema import (
    CognitiveLevelEnum,
    IRTParameters,
    Item,
    SubjectEnum,
    format_fixed_precision,
)

LATEX_KEYWORDS = [
    r"\frac", r"\sqrt", r"\sin", r"\cos", r"\tan", r"\pi", r"\theta",
    r"\alpha", r"\beta", r"\gamma", r"\Delta", r"\int", r"\sum", r"\pm",
    r"^", r"_", r"=", r"\times", r"\cdot", r"\degree"
]


class M2DifficultyFeatureExtractor:
    """Extracts rich linguistic, equation, readability, and structural features."""

    def __init__(self, max_tfidf_features: int = 300) -> None:
        self.max_tfidf_features = max_tfidf_features
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=self.max_tfidf_features,
            sublinear_tf=True,
            lowercase=True,
        )
        self.is_fitted = False

    def _extract_dense_features(self, item_dict: dict) -> np.ndarray:
        stem = item_dict.get("stem", "")
        options = item_dict.get("options", []) or []
        cognitive = item_dict.get("cognitive_level", "application")
        subject = item_dict.get("subject", "physics")
        kind = item_dict.get("kind", "static")

        # 1. Text length features
        char_count = len(stem)
        words = stem.split()
        word_count = len(words)
        avg_word_len = char_count / max(1, word_count)
        sentence_count = len(re.split(r"[.!?]+", stem))

        # 2. LaTeX & mathematical complexity
        latex_count = sum(stem.count(kw) for kw in LATEX_KEYWORDS)
        math_symbol_count = len(re.findall(r"[\+\-\*\/\=\^\_\<\>]", stem))
        num_count = len(re.findall(r"[-+]?\d*\.?\d+", stem))

        # 3. Option features
        num_options = len(options)
        avg_option_len = sum(len(opt) for opt in options) / max(1, num_options) if options else 0.0

        # 4. Cognitive level one-hot
        is_recall = 1.0 if cognitive == "recall" else 0.0
        is_app = 1.0 if cognitive == "application" else 0.0
        is_analysis = 1.0 if cognitive == "analysis" else 0.0

        # 5. Subject one-hot
        is_phy = 1.0 if subject == "physics" else 0.0
        is_chem = 1.0 if subject == "chemistry" else 0.0
        is_bot = 1.0 if subject == "botany" else 0.0
        is_zoo = 1.0 if subject == "zoology" else 0.0

        # 6. Template indicator
        is_template = 1.0 if kind == "template" else 0.0

        # 7. Structural complexity ratio
        complexity_ratio = (latex_count * 2.0 + math_symbol_count + num_count) / max(1.0, word_count)

        features = [
            char_count / 100.0,
            word_count / 20.0,
            avg_word_len / 5.0,
            sentence_count,
            latex_count,
            math_symbol_count / 5.0,
            num_count / 3.0,
            num_options,
            avg_option_len / 20.0,
            is_recall,
            is_app,
            is_analysis,
            is_phy,
            is_chem,
            is_bot,
            is_zoo,
            is_template,
            complexity_ratio,
        ]
        return np.array(features, dtype=float)

    def fit(self, item_dicts: List[dict]) -> M2DifficultyFeatureExtractor:
        stems = [d.get("stem", "") for d in item_dicts]
        self.vectorizer.fit(stems)
        self.is_fitted = True
        return self

    def transform(self, item_dicts: List[dict]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Extractor must be fitted before transform")
        stems = [d.get("stem", "") for d in item_dicts]
        X_tfidf = self.vectorizer.transform(stems).toarray()
        dense_feats = np.array([self._extract_dense_features(d) for d in item_dicts])
        return np.hstack([dense_feats, X_tfidf])


class M2DifficultyPredictorBaseline:
    """Ridge regression baseline predicting 3PL difficulty b and discrimination a."""

    def __init__(self, alpha: float = 1.0, random_state: int = 42) -> None:
        self.alpha = alpha
        self.random_state = random_state
        self.feature_extractor = M2DifficultyFeatureExtractor()
        self.reg_b = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.reg_a = Ridge(alpha=self.alpha, random_state=self.random_state)
        self.is_fitted = False

    def _item_to_dict(self, item: Union[Item, dict, str]) -> dict:
        if isinstance(item, str):
            return {"stem": item}
        if isinstance(item, Item):
            return {
                "stem": item.stem,
                "options": item.options,
                "subject": item.subject.value,
                "chapter": item.chapter,
                "cognitive_level": item.cognitive_level.value,
                "kind": item.kind.value,
            }
        return item

    def fit(self, items: List[Item]) -> M2DifficultyPredictorBaseline:
        item_dicts = [self._item_to_dict(it) for it in items]
        y_b = [float(it.irt.b) for it in items]
        y_a = [float(it.irt.a) for it in items]

        self.feature_extractor.fit(item_dicts)
        X = self.feature_extractor.transform(item_dicts)

        self.reg_b.fit(X, y_b)
        self.reg_a.fit(X, y_a)
        self.is_fitted = True
        return self

    def predict(
        self,
        questions: List[Union[Item, dict, str]],
        b_bounds: Tuple[float, float] = (-3.0, 3.0),
        a_bounds: Tuple[float, float] = (0.2, 2.5),
        c_fixed: float = 0.25,
    ) -> List[IRTParameters]:
        """Predict clamped, fixed-precision IRT parameters for input questions."""
        if not self.is_fitted:
            raise RuntimeError("M2DifficultyPredictorBaseline is not fitted yet.")

        item_dicts = [self._item_to_dict(q) for q in questions]
        X = self.feature_extractor.transform(item_dicts)

        pred_b_raw = self.reg_b.predict(X)
        pred_a_raw = self.reg_a.predict(X)

        # Clamping to valid psychometric ranges
        pred_b_clamped = np.clip(pred_b_raw, b_bounds[0], b_bounds[1])
        pred_a_clamped = np.clip(pred_a_raw, a_bounds[0], a_bounds[1])

        results = []
        for i in range(len(item_dicts)):
            results.append(
                IRTParameters.from_floats(
                    a=float(pred_a_clamped[i]),
                    b=float(pred_b_clamped[i]),
                    c=c_fixed,
                )
            )
        return results

    def save(self, path: Union[str, Path]) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, p)

    @classmethod
    def load(cls, path: Union[str, Path]) -> M2DifficultyPredictorBaseline:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model artifact not found at {p}")
        model = joblib.load(p)
        if not isinstance(model, M2DifficultyPredictorBaseline):
            raise TypeError(f"Loaded object is {type(model).__name__}, expected M2DifficultyPredictorBaseline")
        return model
