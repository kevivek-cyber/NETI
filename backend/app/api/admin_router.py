"""
API router for Invigilator/Admin operations.
"""

from fastapi import APIRouter
from app.exam.session_store import session_store

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/sessions/{session_id}")
async def get_live_sessions(session_id: str):
    """
    Returns the live health and status of all candidates in a given exam session.
    Used by the invigilator console to monitor check-ins and exam progress.
    """
    sessions = await session_store.get_all_sessions(session_id)
    return {
        "session_id": session_id,
        "candidates": sessions,
        "total_active": len(sessions)
    }
