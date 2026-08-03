"""Merkle and canonicalisation tests.

These guard the properties an attacker would target. If one fails, the
audit guarantee is gone — do not "fix" it by relaxing the assertion.
"""

from __future__ import annotations

import pytest

from app.ledger import merkle
from app.ledger.canonical import Domain, NonCanonical, canonical_bytes, hash_object


def leaves(n: int) -> list[bytes]:
    return [hash_object(Domain.LEAF, {"i": i}) for i in range(n)]


def test_key_order_does_not_change_the_hash():
    assert canonical_bytes({"a": 1, "b": 2}) == canonical_bytes({"b": 2, "a": 1})


def test_floats_are_rejected():
    with pytest.raises(NonCanonical):
        canonical_bytes({"difficulty": 0.1})


def test_domain_separation():
    """The same bytes under different tags must not collide."""
    payload = {"x": 1}
    assert hash_object(Domain.LEAF, payload) != hash_object(Domain.NODE, payload)


def test_empty_tree_has_a_defined_root():
    assert merkle.root([]) == merkle.EMPTY_ROOT


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 9, 16, 33, 100])
def test_every_leaf_proves(n):
    ls = leaves(n)
    root = merkle.root(ls)
    for i in range(n):
        assert merkle.verify(merkle.prove(ls, i), root), f"leaf {i} of {n} failed"


def test_tampering_with_a_leaf_changes_the_root():
    ls = leaves(8)
    before = merkle.root(ls)
    ls[3] = hash_object(Domain.LEAF, {"i": "tampered"})
    assert merkle.root(ls) != before


def test_proof_fails_against_the_wrong_root():
    ls = leaves(8)
    proof = merkle.prove(ls, 2)
    assert not merkle.verify(proof, merkle.root(leaves(9)))


def test_order_is_part_of_the_record():
    ls = leaves(4)
    assert merkle.root(ls) != merkle.root(list(reversed(ls)))


def test_odd_node_is_promoted_not_duplicated():
    """The CVE-2012-2459 defence.

    With duplication, a 3-leaf tree [a,b,c] and a 4-leaf tree [a,b,c,c]
    produce the same root, so an attacker can forge a leaf set. With
    promotion they must differ.
    """
    three = leaves(3)
    four = three + [three[2]]
    assert merkle.root(three) != merkle.root(four)
