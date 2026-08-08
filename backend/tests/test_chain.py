"""Block signing and chaining — INTEGRITY.md §4, CUSTODY.md §4.

These guard the property that makes the ledger evidence rather than
bookkeeping: that the authority cannot discard the real record and
publish a fabricated one that verifies.
"""

from __future__ import annotations

import pytest

from app.ledger import merkle
from app.ledger.chain import (
    GENESIS_PREV,
    Block,
    Chain,
    ChainError,
)
from app.ledger.signing import (
    Institution,
    Official,
    SigningError,
    generate_keypair,
    roster_hash,
    sign,
    verify_quorum,
)

COMMITMENTS = {
    "bank_version_hash": "aa" * 32,
    "generator_source_hash": "bb" * 32,
    "blueprint_hash": "cc" * 32,
    "opened_at": "2026-05-03T10:00:00Z",
    "closed_at": "2026-05-03T10:04:11Z",
}


@pytest.fixture
def officials():
    """One official per institution, as CUSTODY.md §4 requires."""
    made = {}
    for oid, inst in [
        ("OFF-CENTRE-01", Institution.CENTRE),
        ("OFF-INDEP-01", Institution.INDEPENDENT),
        ("OFF-AUTH-01", Institution.AUTHORITY),
    ]:
        priv, pub = generate_keypair()
        made[oid] = (priv, Official(oid, inst, pub))
    return made


@pytest.fixture
def roster(officials):
    return {oid: o for oid, (_, o) in officials.items()}


@pytest.fixture
def chain(roster):
    return Chain(session_id="2026-NEET-UG", centre_id="MH-PUNE-014", roster=roster)


def sign_all(officials, block_hash, only=None):
    ids = only if only is not None else list(officials)
    return tuple(sign(officials[i][0], officials[i][1], block_hash) for i in ids)


def make_block(chain, officials, *, leaf_count=0, leaves=None, only=None):
    leaves = leaves or []
    header = chain.build_header(
        merkle_root=merkle.root(leaves).hex(),
        leaf_count=leaf_count,
        **COMMITMENTS,
    )
    return Block(header=header, signatures=sign_all(officials, header.hash(), only))


# --- genesis --------------------------------------------------------------

def test_genesis_has_no_predecessor(chain, officials):
    block = make_block(chain, officials)
    assert block.header.prev_block_hash == GENESIS_PREV.hex()
    assert block.header.height == 0
    chain.append(block)


def test_genesis_commits_the_pre_exam_state(chain, officials):
    """Bank, generator and blueprint are pinned before any paper exists —
    that is what makes the commitment binding."""
    block = make_block(chain, officials)
    h = block.header
    assert h.bank_version_hash == COMMITMENTS["bank_version_hash"]
    assert h.generator_source_hash == COMMITMENTS["generator_source_hash"]
    assert h.blueprint_hash == COMMITMENTS["blueprint_hash"]
    assert h.official_roster_hash == roster_hash(chain.roster).hex()
    assert h.leaf_count == 0


def test_only_genesis_may_be_empty(chain, officials):
    chain.append(make_block(chain, officials))
    with pytest.raises(ChainError, match="only the genesis block"):
        chain.append(make_block(chain, officials, leaf_count=0))


# --- chaining -------------------------------------------------------------

def leaves_for(n, offset=0):
    return [bytes([i % 256]) * 32 for i in range(offset, offset + n)]


def test_blocks_chain_and_verify(chain, officials):
    chain.append(make_block(chain, officials))
    for i in range(3):
        ls = leaves_for(4, offset=i * 4)
        chain.append(make_block(chain, officials, leaf_count=len(ls), leaves=ls))

    assert chain.height == 4
    chain.verify()


def test_leaf_indices_are_contiguous(chain, officials):
    chain.append(make_block(chain, officials))
    chain.append(make_block(chain, officials, leaf_count=4, leaves=leaves_for(4)))
    chain.append(make_block(chain, officials, leaf_count=3, leaves=leaves_for(3, 4)))
    assert [b.header.first_leaf_index for b in chain.blocks] == [0, 0, 4]


def test_tampering_with_a_block_breaks_the_chain(chain, officials):
    """The whole point: rewriting history must be detectable."""
    chain.append(make_block(chain, officials))
    chain.append(make_block(chain, officials, leaf_count=4, leaves=leaves_for(4)))
    chain.verify()

    forged_header = chain.blocks[1].header.__class__(
        **{**chain.blocks[1].header.as_dict(), "merkle_root": "de" * 32}
    )
    chain.blocks[1] = Block(forged_header, chain.blocks[1].signatures)

    with pytest.raises(ChainError, match="signature check"):
        chain.verify()


def test_block_from_another_chain_is_rejected(chain, officials, roster):
    chain.append(make_block(chain, officials))
    other = Chain(session_id="2026-NEET-UG", centre_id="KA-BLR-002", roster=roster)
    stray = make_block(other, officials)
    with pytest.raises(ChainError, match="prev_block_hash|height"):
        chain.append(stray)


# --- the quorum rule ------------------------------------------------------

def test_two_signatures_are_not_enough(chain, officials):
    block = make_block(chain, officials, only=["OFF-CENTRE-01", "OFF-INDEP-01"])
    with pytest.raises(ChainError, match="exactly 3 signatures"):
        chain.append(block)


def test_three_officials_from_one_institution_are_rejected(chain):
    """The load-bearing check. Three people from the same office is one
    institution holding three keys, and the separation collapses."""
    officials, roster = {}, {}
    for i in range(3):
        priv, pub = generate_keypair()
        oid = f"OFF-AUTH-{i:02d}"
        o = Official(oid, Institution.AUTHORITY, pub)
        officials[oid] = (priv, o)
        roster[oid] = o

    c = Chain(session_id="S", centre_id="C", roster=roster)
    block = make_block(c, officials)
    with pytest.raises(ChainError, match="all three institutions"):
        c.append(block)


def test_signature_from_an_unlisted_official_is_rejected(chain, officials, roster):
    """Roster is committed in genesis; signing with a key that was not
    committed is exactly the swap the commitment exists to prevent."""
    priv, pub = generate_keypair()
    outsider = Official("OFF-GHOST-99", Institution.AUTHORITY, pub)
    header = chain.build_header(merkle_root=merkle.root([]).hex(), leaf_count=0, **COMMITMENTS)
    sigs = (
        sign(officials["OFF-CENTRE-01"][0], officials["OFF-CENTRE-01"][1], header.hash()),
        sign(officials["OFF-INDEP-01"][0], officials["OFF-INDEP-01"][1], header.hash()),
        sign(priv, outsider, header.hash()),
    )
    with pytest.raises(ChainError, match="not on the committed roster"):
        chain.append(Block(header, sigs))


def test_one_official_cannot_sign_twice(chain, officials):
    header = chain.build_header(merkle_root=merkle.root([]).hex(), leaf_count=0, **COMMITMENTS)
    priv, o = officials["OFF-CENTRE-01"]
    sigs = (sign(priv, o, header.hash()),) * 3
    with pytest.raises(ChainError, match="signed twice"):
        chain.append(Block(header, sigs))


def test_a_signature_over_a_different_block_does_not_verify(chain, officials, roster):
    """Signatures must be bound to this block, not replayable onto another."""
    chain.append(make_block(chain, officials))
    good = make_block(chain, officials, leaf_count=4, leaves=leaves_for(4))

    other_header = chain.build_header(
        merkle_root=merkle.root(leaves_for(9)).hex(), leaf_count=9, **COMMITMENTS
    )
    with pytest.raises(SigningError, match="does not verify"):
        verify_quorum(other_header.hash(), list(good.signatures), roster)


def test_institution_cannot_be_misdeclared(chain, officials):
    """A signer claiming a tier they do not hold would let one institution
    fake the spread."""
    header = chain.build_header(merkle_root=merkle.root([]).hex(), leaf_count=0, **COMMITMENTS)
    priv, o = officials["OFF-CENTRE-01"]
    real = sign(priv, o, header.hash())
    lying = real.__class__(real.official_id, Institution.AUTHORITY, real.signature)
    sigs = (
        lying,
        sign(officials["OFF-INDEP-01"][0], officials["OFF-INDEP-01"][1], header.hash()),
        sign(officials["OFF-AUTH-01"][0], officials["OFF-AUTH-01"][1], header.hash()),
    )
    with pytest.raises(ChainError, match="claims institution"):
        chain.append(Block(header, sigs))


# --- roster commitment ----------------------------------------------------

def test_roster_hash_is_order_independent(roster):
    reversed_roster = dict(reversed(list(roster.items())))
    assert roster_hash(roster) == roster_hash(reversed_roster)


def test_roster_hash_changes_when_an_official_changes(roster):
    before = roster_hash(roster)
    _, pub = generate_keypair()
    roster["OFF-EXTRA-01"] = Official("OFF-EXTRA-01", Institution.CENTRE, pub)
    assert roster_hash(roster) != before
