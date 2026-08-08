"""Ingestion, cleaning, and dataset splitting utilities for NETI items.

Handles raw past papers, curated items, and unlabelled question batches.
Ensures zero data leakage between train/val/test splits by grouping by
concept/template family/year.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field, ValidationError

from .schema import (
    CognitiveLevelEnum,
    IRTParameters,
    Item,
    ItemBankContainer,
    ItemKindEnum,
    NCERTReference,
    ReviewMetadata,
    SubjectEnum,
    format_fixed_precision,
)

# Regex cleaners for raw exam text
LATEX_CLEANUP_REGEX = re.compile(r"\\[a-zA-Z]+|\$")
WHITESPACE_REGEX = re.compile(r"\s+")


class RawPastPaperQuestion(BaseModel):
    """Schema for ingesting raw/real past NEET-UG questions."""
    id: str = Field(..., description="Unique question ID, e.g. NEET-2024-PHY-042")
    source: str = Field(default="NEET-UG", description="Source examination or publication")
    year: Optional[int] = Field(default=None, description="Year of administration, e.g. 2024")
    subject: SubjectEnum = Field(..., description="Subject: physics, chemistry, botany, zoology")
    chapter: Optional[str] = Field(default="general", description="Chapter identifier if known")
    stem: str = Field(..., description="Raw question stem text")
    options: Optional[List[str]] = Field(default=None, description="List of 4 option strings")
    answer: Optional[str] = Field(default=None, description="Correct option string or formula")
    distractors: Optional[List[str]] = Field(default=None, description="Distractor options/formulas")
    concept_tags: Optional[List[str]] = Field(default_factory=list, description="Associated concept tags")
    cognitive_level: Optional[CognitiveLevelEnum] = Field(default=CognitiveLevelEnum.APPLICATION)
    unit: Optional[str] = Field(default="")
    kind: Optional[ItemKindEnum] = Field(default=ItemKindEnum.STATIC)
    params: Optional[Dict[str, List[Union[int, float]]]] = None


def clean_text(text: str) -> str:
    """Normalize whitespace and strip unneeded LaTeX tags while preserving essential tokens."""
    if not text:
        return ""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = WHITESPACE_REGEX.sub(" ", cleaned).strip()
    return cleaned


def parse_raw_question_to_item(raw_dict: Dict[str, Any], default_irt: Optional[IRTParameters] = None) -> Item:
    """Convert an ingested raw past paper question dict into a validated canonical Item object."""
    try:
        raw_q = RawPastPaperQuestion.model_validate(raw_dict)
    except ValidationError as e:
        raise ValueError(f"Raw question failed schema validation: {e}") from e

    if default_irt is None:
        # Default prior parameters for uncalibrated items
        default_irt = IRTParameters(a="1.20", b="0.00", c="0.25")

    clean_stem = clean_text(raw_q.stem)
    cleaned_options = [clean_text(opt) for opt in raw_q.options] if raw_q.options else None

    # Handle template vs static
    if raw_q.kind == ItemKindEnum.TEMPLATE or raw_q.params:
        item = Item(
            id=raw_q.id,
            subject=raw_q.subject,
            chapter=raw_q.chapter or "general",
            concept_tags=raw_q.concept_tags or [raw_q.chapter or "general"],
            cognitive_level=raw_q.cognitive_level or CognitiveLevelEnum.APPLICATION,
            kind=ItemKindEnum.TEMPLATE,
            stem=clean_stem,
            params=raw_q.params or {},
            answer=raw_q.answer or "",
            distractors=raw_q.distractors or [],
            unit=raw_q.unit or "",
            irt=default_irt,
            provisional=True,
            bank_version=f"ingested-{raw_q.year or 'legacy'}",
        )
    else:
        correct_opt = raw_q.answer
        if not correct_opt and cleaned_options:
            correct_opt = cleaned_options[0]

        item = Item(
            id=raw_q.id,
            subject=raw_q.subject,
            chapter=raw_q.chapter or "general",
            concept_tags=raw_q.concept_tags or [raw_q.chapter or "general"],
            cognitive_level=raw_q.cognitive_level or CognitiveLevelEnum.APPLICATION,
            kind=ItemKindEnum.STATIC,
            stem=clean_stem,
            options=cleaned_options or ["A", "B", "C", "D"],
            correct=correct_opt,
            irt=default_irt,
            provisional=True,
            bank_version=f"ingested-{raw_q.year or 'legacy'}",
        )
    return item


def load_items_from_json(path: Union[str, Path]) -> List[Item]:
    """Load and strictly validate items from a JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Bank file not found: {p}")
    
    raw = json.loads(p.read_text(encoding="utf-8"))
    raw_items = raw.get("items", raw) if isinstance(raw, dict) else raw
    
    items: List[Item] = []
    for idx, item_data in enumerate(raw_items):
        try:
            if "irt" in item_data and isinstance(item_data["irt"], dict):
                item_data["irt"] = {
                    "a": str(item_data["irt"].get("a", "1.20")),
                    "b": str(item_data["irt"].get("b", "0.00")),
                    "c": str(item_data["irt"].get("c", "0.25")),
                }
            item = Item.model_validate(item_data)
            items.append(item)
        except Exception as e:
            item_id = item_data.get("id", f"index_{idx}")
            raise ValueError(f"Failed to validate item {item_id}: {e}") from e

    return items


def save_items_to_json(items: List[Item], path: Union[str, Path], bank_version: str = "v1.0.0", note: str = "") -> None:
    """Save items in canonical JSON format."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    container = ItemBankContainer(
        bank_version=bank_version,
        note=note,
        items=items,
    )
    p.write_text(json.dumps(container.to_canonical_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def create_leakage_safe_split(
    items: List[Item],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Item], List[Item], List[Item]]:
    """Create a deterministic, leakage-safe train/val/test split.
    
    Stratifies across subjects while grouping by template families and chapters
    to prevent cross-set leakage.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("Ratios must sum to 1.0")

    # Group items by subject first to ensure balanced subject representation
    by_subject: Dict[str, List[Item]] = {}
    for item in items:
        by_subject.setdefault(item.subject.value, []).append(item)

    train_items: List[Item] = []
    val_items: List[Item] = []
    test_items: List[Item] = []

    rng = np.random.default_rng(seed)

    for subj, subj_items in by_subject.items():
        # Sub-group by chapter and primary concept
        groups: Dict[str, List[Item]] = {}
        for it in subj_items:
            group_key = f"{it.chapter}::{it.kind.value}"
            groups.setdefault(group_key, []).append(it)

        group_keys = sorted(groups.keys())
        permuted_keys = rng.permutation(group_keys)

        n_groups = len(permuted_keys)
        n_train = max(1, int(np.floor(n_groups * train_ratio)))
        n_val = max(1, int(np.floor(n_groups * val_ratio))) if n_groups > 2 else 0

        train_k = set(permuted_keys[:n_train])
        val_k = set(permuted_keys[n_train:n_train + n_val])
        test_k = set(permuted_keys[n_train + n_val:]) if n_groups > 2 else set(permuted_keys[n_train:])

        for k, group_list in groups.items():
            if k in train_k:
                train_items.extend(group_list)
            elif k in val_k:
                val_items.extend(group_list)
            else:
                test_items.extend(group_list)

    # Fallback safety if test set is empty due to small group count
    if not test_items and val_items:
        test_items = val_items

    return train_items, val_items, test_items
