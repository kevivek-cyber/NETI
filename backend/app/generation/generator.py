"""Deterministic paper generation.

    generate(seed, bank, blueprint) -> paper

Pure function. No I/O, no clock, no network, no LLM. Given the same
inputs it must return the byte-identical paper forever, because
docs/INTEGRITY.md section 11 re-runs it years later to audit an exam.

DO NOT add caching, memoisation, parallelism or retries here.

This is a walking skeleton. It samples items and instantiates templates
so the pipeline connects end to end, but it does NOT yet do the things
that make generation fair:

    TODO(role 2): IRT difficulty targeting and test-information-function
                  tolerance with bounded retry (AI_PIPELINE.md section 6 step 8)
    TODO(role 2): chapter weightage and cognitive-level mix
    TODO(role 2): exposure caps and hall-collision constraints
    TODO(role 2): symbolic validation via sympy rather than eval
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ..ledger.canonical import Domain, hash_object
from .blueprint import Blueprint
from .rng import DeterministicRNG

BANK_PATH = Path(__file__).resolve().parents[1] / "bank" / "sample_bank.json"

# Whitelist for template answer expressions. The bank is authored and
# reviewed before encryption, but eval still deserves a narrow namespace.
# TODO(role 2): replace with sympy so solutions are symbolic, not evaluated.
_MATH_NS: dict[str, Any] = {
    "__builtins__": {},
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "pi": math.pi,
    "radians": math.radians,
    "abs": abs,
    "round": round,
}


def load_bank(path: Path = BANK_PATH) -> dict:
    """TODO(role 3): replace with a decrypt-from-ceremony-key loader."""
    return json.loads(path.read_text(encoding="utf-8"))


def _format_number(value: float) -> str:
    """Numbers become strings before hashing — floats are banned in leaves."""
    rounded = round(value, 2)
    if abs(rounded - round(rounded)) < 1e-9:
        return str(int(round(rounded)))
    return f"{rounded:.2f}"


def _instantiate(item: dict, rng: DeterministicRNG) -> dict:
    """Turn a template into one concrete question."""
    values = {name: rng.choice(choices) for name, choices in item["params"].items()}
    namespace = {**_MATH_NS, **values}

    answer = _format_number(eval(item["answer"], namespace))  # noqa: S307
    options = [answer]
    for expression in item["distractors"]:
        candidate = _format_number(eval(expression, namespace))  # noqa: S307
        if candidate not in options:
            options.append(candidate)

    unit = item.get("unit", "")
    return {
        "stem": item["stem"].format(**values),
        "options": [f"{o} {unit}".strip() for o in options],
        "correct": f"{answer} {unit}".strip(),
    }


def _render(item: dict, rng: DeterministicRNG) -> dict:
    """One bank item -> one paper question, with options permuted."""
    if item["kind"] == "template":
        rendered = _instantiate(item, rng)
    else:
        rendered = {
            "stem": item["stem"],
            "options": list(item["options"]),
            "correct": item["correct"],
        }

    options = rng.shuffled(rendered["options"])
    return {
        "item_id": item["id"],
        "subject": item["subject"],
        "stem": rendered["stem"],
        "options": options,
        "answer_index": options.index(rendered["correct"]),
    }


def generate(seed: bytes, bank: dict, blueprint: Blueprint) -> dict:
    """Assemble one candidate's paper. Deterministic in `seed`."""
    rng = DeterministicRNG(seed)
    by_subject: dict[str, list[dict]] = {}
    for item in bank["items"]:
        by_subject.setdefault(item["subject"], []).append(item)

    questions: list[dict] = []
    for section in blueprint.sections:
        pool = sorted(by_subject.get(section.subject, []), key=lambda i: i["id"])
        if len(pool) < section.count:
            raise ValueError(
                f"bank has {len(pool)} {section.subject} items, "
                f"blueprint needs {section.count}"
            )
        for item in rng.sample(pool, section.count):
            questions.append(_render(item, rng))

    return {
        "blueprint": blueprint.name,
        "bank_version": bank["bank_version"],
        "questions": [
            {**q, "number": n} for n, q in enumerate(rng.shuffled(questions), start=1)
        ],
    }


def sealed(paper: dict) -> dict:
    """The candidate's view: answer keys stripped.

    Keys stay sealed until the exam window closes (CLAUDE.md invariants).
    The hash is always taken over the FULL paper, never this view.
    """
    return {
        **paper,
        "questions": [
            {k: v for k, v in q.items() if k != "answer_index"}
            for q in paper["questions"]
        ],
    }


def paper_hash(paper: dict) -> bytes:
    """The ledger leaf for this paper."""
    return hash_object(Domain.LEAF, paper)
