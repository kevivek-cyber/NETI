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
from ..bank.encryption import decrypt_item
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
    """Load the encrypted bank from disk. Decryption happens per-item in generate()."""
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

    options = []
    for expression in item["template_options"]:
        options.append(_format_number(eval(expression, namespace)))  # noqa: S307

    unit = item.get("unit", "")
    res = {
        "stem": item["stem"].format(**values),
        "options": [f"{o} {unit}".strip() for o in options],
    }
    
    if "correct_template_index" in item:
        res["correct"] = res["options"][item["correct_template_index"]]
        
    return res


def _render(item: dict, rng: DeterministicRNG) -> dict:
    """One bank item -> one paper question, with options permuted."""
    if item["kind"] == "template":
        rendered = _instantiate(item, rng)
    else:
        rendered = {
            "stem": item["stem"],
            "options": list(item["options"]),
        }
        if "correct" in item:
            rendered["correct"] = item["correct"]

    options = rng.shuffled(rendered["options"])
    res = {
        "item_id": item["id"],
        "subject": item["subject"],
        "stem": rendered["stem"],
        "options": options,
    }
    if "correct" in rendered:
        res["answer_index"] = options.index(rendered["correct"])
    return res


def generate(seed: bytes, bank: dict, blueprint: Blueprint, bank_key: bytes, answer_key: bytes | None = None) -> dict:
    """Assemble one candidate's paper. Deterministic in `seed`."""
    if not bank_key:
        raise ValueError("Cannot generate paper without valid bank_key")
        
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
        for encrypted_item in rng.sample(pool, section.count):
            # Only decrypt the items we actually serve!
            item = decrypt_item(encrypted_item, bank_key, answer_key)
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
    The hash is always taken over THIS view, never the FULL paper.
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
    return hash_object(Domain.LEAF, sealed(paper))
