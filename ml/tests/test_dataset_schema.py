"""Unit tests for NETI dataset schema and IRT parameter validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ml.dataset.schema import (
    CognitiveLevelEnum,
    IRTParameters,
    Item,
    ItemBankContainer,
    ItemKindEnum,
    SubjectEnum,
    format_fixed_precision,
)


def test_fixed_precision_formatter():
    assert format_fixed_precision(1.2) == "1.20"
    assert format_fixed_precision(-0.35, decimals=2) == "-0.35"
    assert format_fixed_precision(0) == "0.00"
    assert format_fixed_precision(15) == "15.00"


def test_valid_irt_parameters():
    irt = IRTParameters(a="1.21", b="-0.34", c="0.25")
    assert irt.a == "1.21"
    assert irt.b == "-0.34"
    assert irt.c == "0.25"
    floats = irt.to_floats()
    assert floats == (1.21, -0.34, 0.25)


def test_reject_floating_point_or_invalid_irt():
    with pytest.raises(ValidationError):
        # 3 decimals instead of 2
        IRTParameters(a="1.215", b="-0.34", c="0.25")

    with pytest.raises(ValidationError):
        # Missing decimal part
        IRTParameters(a="1", b="-0.34", c="0.25")

    with pytest.raises(ValidationError):
        # Floating point value instead of string
        IRTParameters(a=1.21, b=-0.34, c=0.25)


def test_valid_template_item():
    item = Item(
        id="PHY-KIN-0001",
        subject=SubjectEnum.PHYSICS,
        chapter="kinematics",
        concept_tags=["projectile", "range"],
        cognitive_level=CognitiveLevelEnum.APPLICATION,
        kind=ItemKindEnum.TEMPLATE,
        stem="A projectile is launched at {angle} deg with speed {v} m/s.",
        params={"angle": [15, 30, 45], "v": [10, 20, 30]},
        answer="v**2 * sin(2*radians(angle)) / 10",
        distractors=["v**2 / 10", "v * sin(angle) / 10", "v**2 * cos(angle) / 10"],
        unit="m",
        irt=IRTParameters(a="1.20", b="-0.30", c="0.25"),
    )
    assert item.kind == ItemKindEnum.TEMPLATE
    canonical = item.to_canonical_dict()
    assert canonical["irt"]["b"] == "-0.30"
    assert canonical["subject"] == "physics"


def test_invalid_template_rejection():
    # Template without params must fail
    with pytest.raises(ValidationError):
        Item(
            id="PHY-KIN-0002",
            subject=SubjectEnum.PHYSICS,
            chapter="kinematics",
            kind=ItemKindEnum.TEMPLATE,
            stem="Test stem",
            params={},
            answer="v * 2",
            distractors=["v", "v/2", "v*3"],
            irt=IRTParameters(a="1.00", b="0.00", c="0.25"),
        )


def test_valid_static_item():
    item = Item(
        id="BOT-CEL-0001",
        subject=SubjectEnum.BOTANY,
        chapter="cell_biology",
        concept_tags=["cell_wall"],
        cognitive_level=CognitiveLevelEnum.RECALL,
        kind=ItemKindEnum.STATIC,
        stem="Which component is primary in plant cell wall?",
        options=["Cellulose", "Chitin", "Peptidoglycan", "Lignin"],
        correct="Cellulose",
        irt=IRTParameters(a="1.10", b="-1.20", c="0.25"),
    )
    assert item.kind == ItemKindEnum.STATIC
    assert item.correct in item.options


def test_invalid_static_rejection():
    # Correct not in options must fail
    with pytest.raises(ValidationError):
        Item(
            id="BOT-CEL-0002",
            subject=SubjectEnum.BOTANY,
            chapter="cell_biology",
            kind=ItemKindEnum.STATIC,
            stem="Question stem",
            options=["A", "B", "C", "D"],
            correct="E",  # Not in options
            irt=IRTParameters(a="1.00", b="0.00", c="0.25"),
        )
