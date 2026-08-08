"""
API router for candidate exam delivery, paper issuance, and response submission.
"""

import json
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.api.ceremony_router import ceremony_manager
from app.exam.lifecycle import SessionState
from app.exam.response_chain import ResponseChain
from app.exam.seeds import derive_seed, pseudonym
from app.exam.session_store import session_store
from app.generation.generator import generate, load_bank, sealed
from app.ledger.hashing import hash_leaf, hash_receipt
from app.ledger import merkle
from app.db.connection import get_db

router = APIRouter(prefix="/exam", tags=["Exam Delivery"])

def _pseudonymise(candidate_id: str) -> str:
    """Roll number -> unlinkable session-scoped pseudonym.

    Every persisted row and every ledger entry is keyed by this, never by
    the candidate id. The ledger is append-only, so a roll number written
    there could never be removed (CLAUDE.md invariants, CUSTODY.md §1).
    """
    if not ceremony_manager.unlocked or ceremony_manager.session_pepper is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ceremony has not been performed; no session pepper available.",
        )
    return pseudonym(ceremony_manager.session_pepper, candidate_id)



# In-memory session leaf registry for Merkle tree batching
session_leaves: list[str] = []


class CheckInRequest(BaseModel):
    candidate_id: str
    session_id: str


class IssuePaperRequest(BaseModel):
    candidate_id: str
    session_id: str


class ResponseEvent(BaseModel):
    question_id: str
    selected_option_index: int
    timestamp_iso: str


class SubmitRequest(BaseModel):
    candidate_id: str
    session_id: str
    events: list[dict[str, Any]]
    expected_response_chain: str


@router.post("/check-in")
async def check_in(req: CheckInRequest):
    pid = _pseudonymise(req.candidate_id)
    session = await session_store.get_or_create_session(pid, req.session_id)
    if session.state == SessionState.REGISTERED:
        await session.transition_to(SessionState.CHECKED_IN)

    return {
        "status": "success",
        "candidate_id": req.candidate_id,
        "session_state": session.state.value,
    }


@router.post("/issue-paper")
async def issue_paper(req: IssuePaperRequest):
    if not ceremony_manager.unlocked or not ceremony_manager.master_seed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exam bank is locked. Unlock ceremony must be completed prior to paper issuance.",
        )

    pid = _pseudonymise(req.candidate_id)
    session = await session_store.get_session(pid)
    if not session or session.state != SessionState.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate must be in 'checked_in' state to issue paper.",
        )

    # 1. Derive this candidate's seed from the pseudonym, not the roll number,
    #    so publishing master_seed for audit does not let anyone iterate roll
    #    numbers and regenerate a named candidate's paper (INTEGRITY.md §7).
    candidate_seed = derive_seed(
        master_seed=ceremony_manager.master_seed,
        session_id=req.session_id,
        pseudonym_hex=pid,
    )

    # 2. Pure deterministic paper generation in RAM
    from app.generation.blueprint import DEMO
    blueprint = DEMO
    bank = load_bank() # TODO: Decrypt using ceremony_manager.bank_key
    paper = generate(
        seed=candidate_seed,
        bank=bank,
        blueprint=blueprint,
    )

    # 3. Compute domain-separated paper leaf hash H_leaf
    paper_leaf = hash_leaf(paper)

    # 4. Store ONLY leaf hash and response chain tracker in session store
    session.paper_hash_hex = paper_leaf
    session.response_chain = ResponseChain(paper_hash_hex=paper_leaf)

    # Record the leaf. One leaf per candidate, never deduplicated by hash:
    # two candidates drawing identical papers is possible with a small bank,
    # and dropping the second would leave them with no ledger entry, no
    # receipt, and no way to prove what they sat.
    #
    # Keyed by pseudonym so re-issuing a paper to the same candidate (a
    # terminal crash, say) reuses their existing leaf rather than appending
    # a duplicate.
    if session.leaf_index is None:
        session.leaf_index = len(session_leaves)
        session_leaves.append(paper_leaf)

        async for conn in get_db():
            await conn.execute(
                "INSERT INTO ledger_leaves (leaf_index, session_id, candidate_pseudonym, leaf_hash) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                session.leaf_index, req.session_id, pid, paper_leaf
            )

    # 5. Transition state: checked_in -> paper_issued -> in_progress
    await session.transition_to(SessionState.PAPER_ISSUED)
    await session.transition_to(SessionState.IN_PROGRESS)

    # Return paper directly to kiosk client
    return {
        "candidate_id": req.candidate_id,
        "paper_hash": paper_leaf,
        "session_state": session.state.value,
        "paper": sealed(paper),
    }


@router.post("/submit")
async def submit_exam(req: SubmitRequest):
    pid = _pseudonymise(req.candidate_id)
    session = await session_store.get_session(pid)
    if not session or session.state != SessionState.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate session must be in 'in_progress' state to submit exam.",
        )

    if not session.paper_hash_hex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing paper hash for candidate session.",
        )

    # Verify response hash chain per INTEGRITY.md §8
    chain_valid = ResponseChain.verify_chain(
        paper_hash_hex=session.paper_hash_hex,
        events=req.events,
        expected_r_n=req.expected_response_chain,
    )

    if not chain_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Response chain integrity verification failed. Chain digest mismatch.",
        )

    # Transition state: in_progress -> submitted
    await session.transition_to(SessionState.SUBMITTED)

    # Inclusion proof over the session's leaves. Indexed by the candidate's
    # own leaf_index rather than by searching for their paper hash: two
    # candidates can legitimately hold the same hash, and a search would
    # return the first one's proof.
    leaves = [bytes.fromhex(h) for h in session_leaves]
    root_hex = merkle.root(leaves).hex()

    if session.leaf_index is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Candidate has no ledger leaf; paper was never issued.",
        )

    p = merkle.prove(leaves, session.leaf_index)
    proof = {
        "index": p.index,
        "leaf": p.leaf.hex(),
        "path": [{"side": s.side, "hash": s.hash.hex()} for s in p.path],
    }

    receipt_payload = {
        # Pseudonym, not roll number: the receipt is hashed into the ledger
        # and the candidate can still identify it as theirs by paper_hash.
        "candidate_pseudonym": pid,
        "session_id": req.session_id,
        "paper_hash": session.paper_hash_hex,
        "response_chain_digest": req.expected_response_chain,
        "merkle_root": root_hex,
        "inclusion_proof": proof,
    }

    receipt_h = hash_receipt(receipt_payload)
    session.receipt = receipt_payload
    await session._save()  # save the receipt

    # Save to submission_receipts table
    async for conn in get_db():
        await conn.execute(
            """
            INSERT INTO submission_receipts (candidate_pseudonym, session_id, paper_hash, response_chain_digest, receipt_hash)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            """,
            pid, req.session_id, session.paper_hash_hex, req.expected_response_chain, receipt_h
        )

    return {
        "status": "submitted",
        "candidate_id": req.candidate_id,
        "session_state": session.state.value,
        "receipt": receipt_payload,
        "receipt_hash": receipt_h,
    }
