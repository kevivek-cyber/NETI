"""Merkle tree over paper leaves.

Implements docs/INTEGRITY.md section 3.

Two details that are easy to get wrong and are the whole point of the
structure:

1. An odd node at a level is PROMOTED, never duplicated. Duplicating the
   last node lets two different leaf sets produce the same root
   (CVE-2012-2459 in Bitcoin).
2. Leaves keep insertion order. Order is part of the record; do not sort.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from .canonical import Domain, digest

EMPTY_ROOT = digest(Domain.NODE)


@dataclass(frozen=True)
class ProofStep:
    side: str  # "L" if the sibling is on the left, else "R"
    hash: bytes


@dataclass(frozen=True)
class InclusionProof:
    index: int
    leaf: bytes
    path: tuple[ProofStep, ...]


def _parent(left: bytes, right: bytes) -> bytes:
    return digest(Domain.NODE, left, right)


def _levels(leaves: list[bytes]) -> list[list[bytes]]:
    """Build every level bottom-up, level 0 being the leaves."""
    if not leaves:
        return [[]]
    levels = [list(leaves)]
    while len(levels[-1]) > 1:
        current = levels[-1]
        nxt: list[bytes] = []
        for i in range(0, len(current) - 1, 2):
            nxt.append(_parent(current[i], current[i + 1]))
        if len(current) % 2:
            nxt.append(current[-1])  # promote, do not duplicate
        levels.append(nxt)
    return levels


def root(leaves: list[bytes]) -> bytes:
    """Merkle root of the given leaves, in insertion order."""
    if not leaves:
        return EMPTY_ROOT
    return _levels(leaves)[-1][0]


def prove(leaves: list[bytes], index: int) -> InclusionProof:
    """Sibling path from leaf `index` up to the root."""
    if not 0 <= index < len(leaves):
        raise IndexError(f"leaf {index} out of range (have {len(leaves)})")

    path: list[ProofStep] = []
    position = index
    for level in _levels(leaves)[:-1]:
        if len(level) % 2 and position == len(level) - 1:
            # Promoted node: rises a level without a sibling, so it
            # contributes no proof step.
            position = len(level) // 2
            continue
        sibling = position ^ 1
        side = "L" if sibling < position else "R"
        path.append(ProofStep(side=side, hash=level[sibling]))
        position //= 2
    return InclusionProof(index=index, leaf=leaves[index], path=tuple(path))


def verify(proof: InclusionProof, expected_root: bytes) -> bool:
    """Recompute the root from a leaf and its sibling path."""
    node = proof.leaf
    for step in proof.path:
        node = (
            _parent(step.hash, node) if step.side == "L" else _parent(node, step.hash)
        )
    return hmac.compare_digest(node, expected_root)
