"""Baseline M1 Concept Tagger using TF-IDF + Multi-Target Classifiers.

Predicts:
1. Subject (Physics, Chemistry, Botany, Zoology)
2. Chapter (e.g. kinematics, mole_concept)
3. Cognitive Level (recall, application, analysis)
4. Concept Tags (multi-label binary vector)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.preprocessing import MultiLabelBinarizer

from ..dataset.schema import CognitiveLevelEnum, Item, SubjectEnum


class M1ConceptTaggerBaseline:
    """Deterministic TF-IDF multi-task classifier for NEET item tagging."""

    def __init__(
        self,
        ngram_range: Tuple[int, int] = (1, 3),
        max_features: int = 10000,
        sublinear_tf: bool = True,
        random_state: int = 42,
    ) -> None:
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.sublinear_tf = sublinear_tf
        self.random_state = random_state

        self.vectorizer = TfidfVectorizer(
            ngram_range=self.ngram_range,
            max_features=self.max_features,
            sublinear_tf=self.sublinear_tf,
            lowercase=True,
            strip_accents="unicode",
        )

        self.clf_subject = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=self.random_state,
        )
        self.clf_chapter = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=self.random_state,
        )
        self.clf_cognitive = LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=1000,
            random_state=self.random_state,
        )
        self.mlb_concepts = MultiLabelBinarizer()
        self.clf_concepts = MultiOutputClassifier(
            LogisticRegression(
                C=1.0,
                class_weight="balanced",
                max_iter=1000,
                random_state=self.random_state,
            )
        )
        self.is_fitted = False

    def _extract_text(self, item: Union[Item, dict, str]) -> str:
        if isinstance(item, str):
            return item
        if isinstance(item, Item):
            text = item.stem
            if item.options:
                text += " " + " ".join(item.options)
            return text
        if isinstance(item, dict):
            text = item.get("stem", "")
            if "options" in item and item["options"]:
                text += " " + " ".join(item["options"])
            return text
        return str(item)

    def fit(self, items: List[Item]) -> M1ConceptTaggerBaseline:
        """Fit all classifiers deterministically on the provided items."""
        texts = [self._extract_text(it) for it in items]
        y_subject = [it.subject.value for it in items]
        y_chapter = [it.chapter for it in items]
        y_cognitive = [it.cognitive_level.value for it in items]
        y_concepts = [it.concept_tags for it in items]

        # 1. Fit TF-IDF
        X = self.vectorizer.fit_transform(texts)

        # 2. Fit single-target classifiers
        self.clf_subject.fit(X, y_subject)
        self.clf_chapter.fit(X, y_chapter)
        self.clf_cognitive.fit(X, y_cognitive)

        # 3. Fit multi-label concept classifier
        Y_concepts_bin = self.mlb_concepts.fit_transform(y_concepts)
        self.clf_concepts.fit(X, Y_concepts_bin)

        self.is_fitted = True
        return self

    def predict(self, questions: List[Union[str, Item, dict]], concept_threshold: float = 0.40) -> List[Dict[str, Any]]:
        """Predict structured metadata for input questions."""
        if not self.is_fitted:
            raise RuntimeError("M1ConceptTaggerBaseline is not fitted yet. Call fit() or load().")

        texts = [self._extract_text(q) for q in questions]
        X = self.vectorizer.transform(texts)

        pred_subject = self.clf_subject.predict(X)
        pred_chapter = self.clf_chapter.predict(X)
        pred_cognitive = self.clf_cognitive.predict(X)

        # Probability scores
        prob_subject = np.max(self.clf_subject.predict_proba(X), axis=1)
        prob_chapter = np.max(self.clf_chapter.predict_proba(X), axis=1)
        prob_cognitive = np.max(self.clf_cognitive.predict_proba(X), axis=1)

        # Predict multi-label concepts with probabilities
        concept_estimators = self.clf_concepts.estimators_
        concept_classes = self.mlb_concepts.classes_
        
        results = []
        for i in range(len(texts)):
            item_concepts = []
            for c_idx, est in enumerate(concept_estimators):
                if hasattr(est, "predict_proba"):
                    classes = list(est.classes_)
                    if 1 in classes:
                        pos_idx = classes.index(1)
                        prob_pos = est.predict_proba(X[i])[0, pos_idx]
                        if prob_pos >= concept_threshold:
                            item_concepts.append((concept_classes[c_idx], float(prob_pos)))
                else:
                    if est.predict(X[i])[0] == 1:
                        item_concepts.append((concept_classes[c_idx], 1.0))
            
            # Sort concepts by confidence
            item_concepts.sort(key=lambda x: x[1], reverse=True)
            tags = [str(c[0]) for c in item_concepts]
            if not tags:  # Fallback if none passed threshold
                tags = [str(pred_chapter[i])]

            results.append({
                "subject": str(pred_subject[i]),
                "subject_confidence": float(prob_subject[i]),
                "chapter": str(pred_chapter[i]),
                "chapter_confidence": float(prob_chapter[i]),
                "cognitive_level": str(pred_cognitive[i]),
                "cognitive_confidence": float(prob_cognitive[i]),
                "concept_tags": tags,
                "concept_confidences": {str(c[0]): float(c[1]) for c in item_concepts},
            })

        return results

    def save(self, path: Union[str, Path]) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, p)

    @classmethod
    def load(cls, path: Union[str, Path]) -> M1ConceptTaggerBaseline:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Model artifact not found at {p}")
        model = joblib.load(p)
        if not isinstance(model, M1ConceptTaggerBaseline):
            raise TypeError(f"Loaded object is {type(model).__name__}, expected M1ConceptTaggerBaseline")
        return model
