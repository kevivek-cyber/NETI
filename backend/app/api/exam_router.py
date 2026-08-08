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
from app.exam.seeds import derive_candidate_seed
from app.exam.session_store import session_store
from app.generation.sampler import generate_paper
from app.ledger.hashing import hash_leaf, hash_receipt
from app.ledger.merkle import MerkleTree
from app.db.connection import get_db

router = APIRouter(prefix="/exam", tags=["Exam Delivery"])

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
    session = await session_store.get_or_create_session(req.candidate_id, req.session_id)
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

    session = await session_store.get_session(req.candidate_id)
    if not session or session.state != SessionState.CHECKED_IN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate must be in 'checked_in' state to issue paper.",
        )

    # 1. Derive candidate seed deterministically via HKDF-SHA256
    candidate_seed = derive_candidate_seed(
        master_seed=ceremony_manager.master_seed,
        session_id=req.session_id,
        candidate_id=req.candidate_id,
    )

    # 2. Pure deterministic paper generation in RAM
    blueprint = {"subjects": ["Physics", "Chemistry", "Botany", "Zoology"], "questions_per_subject": 45}
    paper = generate_paper(
        seed=candidate_seed,
        bank_version="v1.0.0",
        blueprint=blueprint,
    )

    # 3. Compute domain-separated paper leaf hash H_leaf
    paper_leaf = hash_leaf(paper)

    # 4. Store ONLY leaf hash and response chain tracker in session store
    session.paper_hash_hex = paper_leaf
    session.response_chain = ResponseChain(paper_hash_hex=paper_leaf)

    # Record leaf hash in global Merkle leaves batch
    if paper_leaf not in session_leaves:
        session_leaves.append(paper_leaf)
        
        # NOTE: Also save it to ledger_leaves in DB for persistence!
        async for conn in get_db():
            await conn.execute(
                "INSERT INTO ledger_leaves (leaf_index, session_id, candidate_pseudonym, leaf_hash) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                len(session_leaves) - 1, req.session_id, req.candidate_id, paper_leaf
            )

    # 5. Transition state: checked_in -> paper_issued -> in_progress
    await session.transition_to(SessionState.PAPER_ISSUED)
    await session.transition_to(SessionState.IN_PROGRESS)

    # Return paper directly to kiosk client
    return {
        "candidate_id": req.candidate_id,
        "paper_hash": paper_leaf,
        "session_state": session.state.value,
        "paper": paper,
    }


@router.post("/submit")
async def submit_exam(req: SubmitRequest):
    session = await session_store.get_session(req.candidate_id)
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

    # Build Merkle tree over session leaves and produce inclusion proof
    tree = MerkleTree(session_leaves)
    
    # Try to find the leaf_index, fallback to 0 if not found for some reason
    try:
        leaf_index = session_leaves.index(session.paper_hash_hex)
        proof = tree.get_proof(leaf_index)
    except ValueError:
        proof = None

    receipt_payload = {
        "candidate_id": req.candidate_id,
        "session_id": req.session_id,
        "paper_hash": session.paper_hash_hex,
        "response_chain_digest": req.expected_response_chain,
        "merkle_root": tree.root,
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
            req.candidate_id, req.session_id, session.paper_hash_hex, req.expected_response_chain, receipt_h
        )

    return {
        "status": "submitted",
        "candidate_id": req.candidate_id,
        "session_state": session.state.value,
        "receipt": receipt_payload,
        "receipt_hash": receipt_h,
    }
