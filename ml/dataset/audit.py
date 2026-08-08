"""Dataset audit utility for NETI ML data.

Inspects item counts, class distributions, concept label frequency,
label-to-text correlation, and suitability for supervised learning.
"""

from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Any, Dict, List
import numpy as np

from .schema import Item


def audit_item_dataset(items: List[Item]) -> Dict[str, Any]:
    """Perform a comprehensive audit of a collection of items."""
    total_examples = len(items)
    
    subject_counts = collections.Counter(it.subject.value for it in items)
    chapter_counts = collections.Counter(it.chapter for it in items)
    cognitive_counts = collections.Counter(it.cognitive_level.value for it in items)
    kind_counts = collections.Counter(it.kind.value for it in items)
    
    concept_counts = collections.Counter()
    for it in items:
        for tag in it.concept_tags:
            concept_counts[tag] += 1
            
    # Text length stats
    stem_lengths = [len(it.stem.split()) for it in items]
    
    # Check correlation between stem text and cognitive level / subject
    # Check if stems contain subject-specific keywords
    subject_keywords = {
        "physics": ["force", "velocity", "acceleration", "projectile", "angle", "speed", "energy", "ohm", "resistor"],
        "chemistry": ["mole", "mass", "molar", "reaction", "electron", "orbital", "bond", "acid", "hybridisation"],
        "botany": ["plant", "cell", "chloroplast", "photosynthesis", "wall", "calvin", "cross", "gene", "auxin"],
        "zoology": ["blood", "heart", "ventricle", "artery", "organ", "animal", "selection", "enzyme", "moth"],
    }
    
    subject_keyword_matches = collections.defaultdict(int)
    for it in items:
        stem_lower = it.stem.lower()
        matched = False
        for kw in subject_keywords.get(it.subject.value, []):
            if kw in stem_lower:
                matched = True
                break
        if matched:
            subject_keyword_matches[it.subject.value] += 1
            
    audit_report = {
        "total_examples": total_examples,
        "subject_distribution": dict(subject_counts),
        "num_chapters": len(chapter_counts),
        "chapter_distribution_top10": dict(chapter_counts.most_common(10)),
        "cognitive_level_distribution": dict(cognitive_counts),
        "item_kind_distribution": dict(kind_counts),
        "total_unique_concepts": len(concept_counts),
        "concept_frequency_top10": dict(concept_counts.most_common(10)),
        "concept_frequency_least10": dict(concept_counts.most_common()[:-11:-1]),
        "stem_word_count_stats": {
            "mean": float(np.mean(stem_lengths)) if stem_lengths else 0.0,
            "min": int(np.min(stem_lengths)) if stem_lengths else 0,
            "max": int(np.max(stem_lengths)) if stem_lengths else 0,
        },
        "lexical_grounding_rate": {
            subj: f"{subject_keyword_matches[subj]}/{subject_counts[subj]} ({subject_keyword_matches[subj]/max(1, subject_counts[subj]):.1%})"
            for subj in subject_counts
        },
    }
    return audit_report


def print_audit_report(report: Dict[str, Any]) -> None:
    print("=" * 60)
    print("  NETI ML DATASET AUDIT REPORT")
    print("=" * 60)
    print(f"Total Items:                {report['total_examples']}")
    print(f"Subject Distribution:       {report['subject_distribution']}")
    print(f"Cognitive Level Dist:       {report['cognitive_level_distribution']}")
    print(f"Item Kinds:                 {report['item_kind_distribution']}")
    print(f"Total Unique Concepts:      {report['total_unique_concepts']}")
    print(f"Total Chapters Covered:     {report['num_chapters']}")
    print(f"Average Stem Length:        {report['stem_word_count_stats']['mean']:.1f} words")
    print("\nSubject Lexical Grounding:")
    for subj, rate in report['lexical_grounding_rate'].items():
        print(f"  - {subj.capitalize()}: {rate}")
    print("=" * 60)
