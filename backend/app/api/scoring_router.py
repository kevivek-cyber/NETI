from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.exam.scoring import compute_score
from app.api.ceremony_router import ceremony_manager

router = APIRouter(prefix="/scoring", tags=["Scoring"])

class ScoreResponse(BaseModel):
    candidate_pseudonym: str
    session_id: str
    score: int
    correct: int
    incorrect: int
    omitted: int

@router.get("/score/{candidate_pseudonym}", response_model=ScoreResponse)
async def score_candidate(candidate_pseudonym: str, session_id: str):
    """
    Computes the score for a candidate's submitted responses.
    Must be called after the window has closed and answers are revealed.
    """
    if not ceremony_manager.answer_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Answer key not released. The window close ceremony must be completed first."
        )
        
    try:
        result = await compute_score(candidate_pseudonym, session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing score: {str(e)}"
        )
        
    return ScoreResponse(
        candidate_pseudonym=candidate_pseudonym,
        session_id=session_id,
        score=result["score"],
        correct=result["correct"],
        incorrect=result["incorrect"],
        omitted=result["omitted"]
    )
