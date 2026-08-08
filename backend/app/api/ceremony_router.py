"""
API router for custodian bank unlock ceremony.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.keyrelease import CeremonyManager

router = APIRouter(prefix="/ceremony", tags=["Ceremony"])

# Global ceremony manager instance for session
ceremony_manager = CeremonyManager(session_id="2026-NEET-UG")


class ShareInput(BaseModel):
    index: int
    share_hex: str


class UnlockRequest(BaseModel):
    session_id: str
    shares: list[ShareInput]


class UnlockResponse(BaseModel):
    status: str
    session_id: str
    message: str


@router.post("/unlock", response_model=UnlockResponse)
def unlock_bank(req: UnlockRequest):
    if req.session_id != ceremony_manager.session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session ID mismatch: expected {ceremony_manager.session_id}",
        )

    shares_tuples = [(s.index, s.share_hex) for s in req.shares]
    try:
        ceremony_manager.perform_unlock_ceremony(shares_tuples)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Key release ceremony failed: {str(e)}",
        )

    return UnlockResponse(
        status="success",
        session_id=req.session_id,
        message="Bank unlocked in memory. Master seed generated for session.",
    )
