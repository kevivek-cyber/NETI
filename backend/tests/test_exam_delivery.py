"""Regression tests for the exam-delivery layer.

Written because the router imported names that did not exist on any
module (`derive_candidate_seed`, `MerkleTree`) and nothing caught it: the
existing suite never imports the routers, so the app could not start
while every test passed.

The provenance rule applies here too — a test suite that never loads the
code under test is not evidence of anything.
"""

from __future__ import annotations

import hashlib
import secrets

import pytest

from app.core.keyrelease import CeremonyManager, SimpleShamirGF256
from app.exam.lifecycle import SessionState, validate_transition
from app.exam.seeds import derive_seed, pseudonym
from app.exam.session_store import CandidateSession
from app.ledger.canonical import Domain, canonical_bytes, digest
from app.ledger.hashing import hash_response_initial, hash_response_step


def test_app_and_routers_import():
    """The whole app must construct. This is the check that was missing."""
    from app.main import app

    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/health" in paths


def test_router_routes_are_registered():
    from app.api.ceremony_router import router as ceremony
    from app.api.exam_router import router as exam

    assert {r.path for r in exam.routes} == {
        "/exam/check-in", "/exam/issue-paper", "/exam/submit"
    }
    assert {r.path for r in ceremony.routes} == {"/ceremony/unlock"}


# --- ceremony -------------------------------------------------------------

@pytest.fixture
def unlocked() -> CeremonyManager:
    cm = CeremonyManager(session_id="TEST")
    secret = secrets.token_bytes(32)
    shares = SimpleShamirGF256.split(secret, k=3, n=5)
    cm.perform_unlock_ceremony([(i, s.hex()) for i, s in shares[:3]])
    cm._expected_secret = secret  # type: ignore[attr-defined]
    return cm


def test_shamir_roundtrip(unlocked):
    assert unlocked.bank_key == unlocked._expected_secret


def test_ceremony_generates_a_pepper(unlocked):
    """Without a pepper there is nothing to pseudonymise with, and the
    router falls back to writing roll numbers onto an append-only ledger."""
    assert unlocked.session_pepper is not None
    assert len(unlocked.session_pepper) == 32


def test_ceremony_requires_quorum():
    cm = CeremonyManager(session_id="TEST")
    shares = SimpleShamirGF256.split(secrets.token_bytes(32), k=3, n=5)
    with pytest.raises(ValueError, match="at least k=3"):
        cm.perform_unlock_ceremony([(i, s.hex()) for i, s in shares[:2]])


def test_seal_zeroises_pepper_but_keeps_master_seed(unlocked):
    """master_seed is published at seal so the exam can be verified;
    the pepper never is, so it must not survive."""
    unlocked.zeroise()
    assert unlocked.session_pepper is None
    assert unlocked.bank_key is None
    assert unlocked.master_seed is not None


# --- pseudonymisation -----------------------------------------------------

def test_pseudonym_hides_the_roll_number(unlocked):
    roll = "NEET2026-001042"
    pid = pseudonym(unlocked.session_pepper, roll)
    assert pid != roll
    assert len(pid) == 64
    assert roll not in pid


def test_pseudonym_is_stable_and_unlinkable(unlocked):
    a = pseudonym(unlocked.session_pepper, "NEET2026-001042")
    b = pseudonym(unlocked.session_pepper, "NEET2026-001042")
    c = pseudonym(unlocked.session_pepper, "NEET2026-001043")
    assert a == b, "same candidate must map to the same pseudonym"
    assert a != c, "adjacent roll numbers must not collide"


def test_different_peppers_give_different_pseudonyms():
    """A leaked pseudonym from one session must not identify the same
    candidate in another."""
    roll = "NEET2026-001042"
    assert pseudonym(secrets.token_bytes(32), roll) != pseudonym(
        secrets.token_bytes(32), roll
    )


def test_seed_derives_deterministically_from_pseudonym(unlocked):
    pid = pseudonym(unlocked.session_pepper, "NEET2026-001042")
    a = derive_seed(unlocked.master_seed, "S1", pid)
    b = derive_seed(unlocked.master_seed, "S1", pid)
    assert a == b
    assert len(a) == 32


# --- response chain, INTEGRITY.md section 8 -------------------------------

def test_r0_matches_spec():
    """r_0 = SHA-256(0x03 || paper_hash), with the hash as raw bytes."""
    paper_hash = hashlib.sha256(b"paper").hexdigest()
    expected = digest(Domain.RESPONSE, bytes.fromhex(paper_hash)).hex()
    assert hash_response_initial(paper_hash) == expected


def test_ri_matches_spec():
    """r_i = SHA-256(0x03 || r_{i-1} || canonical_bytes(event)).

    Wrapping prev and event in one object and canonicalising that is a
    valid construction but a different digest, and the verifier follows
    the spec.
    """
    paper_hash = hashlib.sha256(b"paper").hexdigest()
    event = {"q": 1, "opt": 2}
    r0 = hash_response_initial(paper_hash)
    expected = digest(Domain.RESPONSE, bytes.fromhex(r0), canonical_bytes(event)).hex()
    assert hash_response_step(r0, event) == expected


def test_response_chain_detects_tampering():
    from app.exam.response_chain import ResponseChain

    paper_hash = hashlib.sha256(b"paper").hexdigest()
    chain = ResponseChain(paper_hash)
    events = [{"q": 1, "opt": 2}, {"q": 2, "opt": 0}]
    for e in events:
        chain.add_event(e)

    assert ResponseChain.verify_chain(paper_hash, events, chain.current_r_hex)

    tampered = [{"q": 1, "opt": 3}, {"q": 2, "opt": 0}]
    assert not ResponseChain.verify_chain(paper_hash, tampered, chain.current_r_hex)


# --- session --------------------------------------------------------------

def test_session_tracks_leaf_index():
    """Leaves must be one-per-candidate. Without an index the router
    searched for the paper hash, which returns the wrong candidate's proof
    when two papers coincide."""
    s = CandidateSession("pid", "S1")
    assert s.leaf_index is None


def test_lifecycle_rejects_illegal_transitions():
    assert validate_transition(SessionState.REGISTERED, SessionState.CHECKED_IN)
    assert not validate_transition(SessionState.REGISTERED, SessionState.SUBMITTED)
    assert not validate_transition(SessionState.SEALED, SessionState.IN_PROGRESS)
