"""Deterministic Taxonomy & Keyword-Aware Rule Fallback for M1 Concept Tagger.

Used offline during authoring when ML classifier confidence is below threshold.
Uses keyword scanning and ontology lookup against ml/taxonomy.json.
Zero LLM, zero random guessing, 100% deterministic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "taxonomy.json"

# Semantic keywords mapped to subjects and chapters
SUBJECT_RULES = {
    "physics": [
        "projectile", "velocity", "acceleration", "force", "friction", "kinetic energy",
        "potential energy", "resistor", "ohm", "current", "voltage", "carnot",
        "thermodynamics", "lens", "focal length", "potentiometer", "mass", "gravity"
    ],
    "chemistry": [
        "mole", "molar mass", "stoichiometry", "quantum", "electron", "orbital",
        "hybridisation", "dipole moment", "gibbs", "enthalpy", "equilibrium",
        "ph", "buffer", "nucleophilic", "carbocation", "hydrochloric", "reaction"
    ],
    "botany": [
        "plant", "cell wall", "cellulose", "chloroplast", "photosynthesis", "calvin cycle",
        "rubisco", "kranz", "c4", "glycolysis", "monohybrid", "mendelian", "auxin",
        "apical dominance", "mitochondria", "stroma", "thylakoid"
    ],
    "zoology": [
        "heart", "ventricle", "atrium", "aorta", "nephron", "kidney", "chordata",
        "chordate", "natural selection", "peppered moth", "hardy weinberg",
        "allele", "enzyme", "malonate", "follicle", "ovulation", "hormone", "lh"
    ],
}

COGNITIVE_RULES = {
    "recall": ["state", "identify", "which of the following is", "name the", "recall", "primary structural", "defined as"],
    "application": ["calculate", "determine", "find", "compute", "evaluate the amount", "magnitude of", "at a distance of"],
    "analysis": ["analyze", "compare and contrast", "deduce", "correctly explains why", "evaluate whether", "consequence of", "mechanism"],
}


class TaxonomyRuleFallback:
    def __init__(self, taxonomy_path: Path = TAXONOMY_PATH) -> None:
        self.taxonomy_path = Path(taxonomy_path)
        self.taxonomy = json.loads(self.taxonomy_path.read_text(encoding="utf-8"))

    def match_subject(self, text: str) -> Tuple[str, float]:
        text_lower = text.lower()
        scores = {}
        for subj, kws in SUBJECT_RULES.items():
            score = sum(1 for kw in kws if kw in text_lower)
            scores[subj] = score

        best_subj = max(scores, key=scores.get)
        total_score = sum(scores.values())
        conf = (scores[best_subj] / max(1, total_score)) if total_score > 0 else 0.25
        return best_subj, float(conf)

    def match_chapter(self, text: str, subject: str) -> Tuple[str, float]:
        text_lower = text.lower()
        chapters = self.taxonomy.get("subjects", {}).get(subject, {}).get("chapters", {})
        chapter_scores = {}
        for chap_name, concepts in chapters.items():
            score = 0
            if chap_name.replace("_", " ") in text_lower:
                score += 3
            for c in concepts:
                if c.replace("_", " ") in text_lower:
                    score += 2
            chapter_scores[chap_name] = score

        if chapter_scores and max(chapter_scores.values()) > 0:
            best_chap = max(chapter_scores, key=chapter_scores.get)
            total = sum(chapter_scores.values())
            return best_chap, float(chapter_scores[best_chap] / total)
        
        # Fallback to first chapter
        first_chap = list(chapters.keys())[0] if chapters else "general"
        return first_chap, 0.30

    def match_cognitive_level(self, text: str) -> Tuple[str, float]:
        text_lower = text.lower()
        scores = {}
        for cog, kws in COGNITIVE_RULES.items():
            score = sum(1 for kw in kws if kw in text_lower)
            scores[cog] = score

        if sum(scores.values()) > 0:
            best_cog = max(scores, key=scores.get)
            return best_cog, float(scores[best_cog] / sum(scores.values()))
        return "application", 0.33

    def match_concepts(self, text: str, subject: str, chapter: str) -> List[str]:
        text_lower = text.lower()
        concepts = self.taxonomy.get("subjects", {}).get(subject, {}).get("chapters", {}).get(chapter, [])
        matched = []
        for c in concepts:
            if c.replace("_", " ") in text_lower or c.replace("_", "") in text_lower:
                matched.append(c)
        if not matched and concepts:
            matched.append(concepts[0])
        return matched

    def fallback_predict(self, stem: str, options: Optional[List[str]] = None) -> Dict[str, Any]:
        combined_text = stem + (" " + " ".join(options) if options else "")
        subj, subj_conf = self.match_subject(combined_text)
        chap, chap_conf = self.match_chapter(combined_text, subj)
        cog, cog_conf = self.match_cognitive_level(combined_text)
        concepts = self.match_concepts(combined_text, subj, chap)

        return {
            "subject": subj,
            "subject_confidence": subj_conf,
            "chapter": chap,
            "chapter_confidence": chap_conf,
            "cognitive_level": cog,
            "cognitive_confidence": cog_conf,
            "concept_tags": concepts,
            "source": "taxonomy_fallback",
        }
