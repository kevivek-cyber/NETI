"""Canonical schema for NETI Item Bank items and datasets.

Normative rules:
1. No floats in serialized JSON! IRT parameters must be fixed-precision strings (e.g. "1.21", "-0.34", "0.25").
2. Strict separation of static items vs parameterized template items.
3. Fully compatible with RFC 8785 JSON Canonicalisation Scheme (JCS) and docs/INTEGRITY.md.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

FIXED_PRECISION_REGEX = re.compile(r"^-?\d+\.\d{2}$")


class SubjectEnum(str, Enum):
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BOTANY = "botany"
    ZOOLOGY = "zoology"


class CognitiveLevelEnum(str, Enum):
    RECALL = "recall"
    APPLICATION = "application"
    ANALYSIS = "analysis"


class ItemKindEnum(str, Enum):
    TEMPLATE = "template"
    STATIC = "static"


def format_fixed_precision(val: Union[float, int, str], decimals: int = 2) -> str:
    """Format a numerical value into an exact fixed-precision decimal string.
    
    Prevents cross-platform IEEE-754 floating-point divergence in Merkle hashing.
    """
    f = float(val)
    rounded = round(f, decimals)
    return f"{rounded:.{decimals}f}"


class IRTParameters(BaseModel):
    """3-Parameter Logistic (3PL) IRT parameters.
    
    Stored strictly as 2-decimal fixed-precision strings.
    """
    a: str = Field(..., description="Discrimination parameter, typically 0.20 to 2.50")
    b: str = Field(..., description="Difficulty parameter on latent theta scale, typically -3.00 to +3.00")
    c: str = Field(default="0.25", description="Pseudo-guessing floor parameter, typically 0.25 for 4-option MCQ")

    @field_validator("a", "b", "c")
    @classmethod
    def validate_fixed_precision_string(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError(f"IRT parameter must be a string, got {type(v).__name__}")
        if not FIXED_PRECISION_REGEX.match(v):
            raise ValueError(f"IRT parameter '{v}' must be a string with exactly 2 decimal places (e.g. '1.20', '-0.35')")
        return v

    def to_floats(self) -> tuple[float, float, float]:
        """Convenience method for offline arithmetic calculations."""
        return float(self.a), float(self.b), float(self.c)

    @classmethod
    def from_floats(cls, a: float, b: float, c: float = 0.25) -> IRTParameters:
        return cls(
            a=format_fixed_precision(a, 2),
            b=format_fixed_precision(b, 2),
            c=format_fixed_precision(c, 2),
        )


class NCERTReference(BaseModel):
    class_num: Optional[int] = Field(default=None, alias="class", ge=11, le=12)
    book: Optional[str] = None
    chapter: Optional[Union[str, int]] = None
    section: Optional[str] = None


class ReviewMetadata(BaseModel):
    status: Literal["draft", "reviewed", "approved", "rejected"] = "draft"
    by: Optional[str] = None
    at: Optional[str] = None
    notes: Optional[str] = None


class Item(BaseModel):
    """Canonical Item model conforming to NETI Architecture and Bank specification."""
    id: str = Field(..., description="Unique immutable item ID, e.g. PHY-KIN-0001")
    subject: SubjectEnum = Field(..., description="Subject: physics, chemistry, botany, zoology")
    chapter: str = Field(..., description="Standardized chapter identifier")
    concept_tags: List[str] = Field(default_factory=list, description="List of fine-grained concept tags")
    cognitive_level: CognitiveLevelEnum = Field(default=CognitiveLevelEnum.APPLICATION)
    kind: ItemKindEnum = Field(..., description="'template' for parameterized numericals, 'static' for fixed items")
    
    stem: str = Field(..., description="Question stem text (with {param} placeholders for templates)")
    
    # Template-specific fields
    params: Optional[Dict[str, List[Union[int, float]]]] = Field(
        default=None,
        description="Dictionary mapping parameter names to lists of allowed numerical values"
    )
    answer: Optional[str] = Field(
        default=None,
        description="Symbolic/algebraic solution expression for template items"
    )
    distractors: Optional[List[str]] = Field(
        default=None,
        description="List of symbolic expressions (for templates) or static wrong options"
    )
    unit: Optional[str] = Field(default="", description="Unit of measurement for numerical answers (e.g. 'm/s')")

    # Static-specific fields
    options: Optional[List[str]] = Field(
        default=None,
        description="4 static option strings for static MCQs"
    )
    correct: Optional[str] = Field(
        default=None,
        description="The correct option string for static MCQs"
    )

    # Psychometrics and integrity
    irt: IRTParameters = Field(..., description="Calibrated or prior 3PL IRT parameters")
    ncert_ref: Optional[NCERTReference] = None
    provisional: bool = Field(
        default=True,
        description="True if calibrated from priors or predicted by M2; False if calibrated on live response data"
    )
    review: Optional[ReviewMetadata] = Field(default_factory=ReviewMetadata)
    bank_version: str = Field(default="v0.1.0", description="Bank version tag for content addressing")

    @model_validator(mode="after")
    def validate_kind_integrity(self) -> Item:
        if self.kind == ItemKindEnum.TEMPLATE:
            if not self.params:
                raise ValueError("Template items must have a non-empty 'params' dictionary")
            if not self.answer:
                raise ValueError("Template items must have a symbolic 'answer' expression")
            if not self.distractors or len(self.distractors) < 3:
                raise ValueError("Template items must specify at least 3 distractor expressions")
        elif self.kind == ItemKindEnum.STATIC:
            if not self.options or len(self.options) != 4:
                raise ValueError("Static MCQ items must provide exactly 4 options")
            if not self.correct:
                raise ValueError("Static MCQ items must provide a 'correct' answer")
            if self.correct not in self.options:
                raise ValueError(f"Correct answer '{self.correct}' is not in options {self.options}")
        return self

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Convert item to a clean JSON-serializable dictionary with string IRT parameters."""
        d = self.model_dump(by_alias=True, exclude_none=True)
        # Convert enums to raw strings
        d["subject"] = self.subject.value
        d["cognitive_level"] = self.cognitive_level.value
        d["kind"] = self.kind.value
        d["irt"] = {
            "a": self.irt.a,
            "b": self.irt.b,
            "c": self.irt.c,
        }
        return d


class ItemBankContainer(BaseModel):
    """Container holding a collection of items under a specific bank version."""
    bank_version: str
    note: str = ""
    items: List[Item]

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "bank_version": self.bank_version,
            "note": self.note,
            "items": [item.to_canonical_dict() for item in self.items],
        }
