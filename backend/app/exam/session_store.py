"""
PostgreSQL-backed candidate session store.
"""

import json
from typing import Any
from app.exam.lifecycle import SessionState, validate_transition
from app.exam.response_chain import ResponseChain
from app.db.connection import get_db

class CandidateSession:
    def __init__(self, candidate_pseudonym: str, session_id: str):
        self.candidate_pseudonym: str = candidate_pseudonym
        self.session_id: str = session_id
        self.state: SessionState = SessionState.REGISTERED
        self.paper_hash_hex: str | None = None
        self.response_chain: ResponseChain | None = None
        self.receipt: dict[str, Any] | None = None
        # Position of this candidate's leaf in the session's Merkle tree.
        # Held so re-issuing a paper reuses the existing leaf instead of
        # appending a duplicate, and so the receipt can prove inclusion by
        # index rather than by searching for a hash that may repeat.
        self.leaf_index: int | None = None

    async def transition_to(self, new_state: SessionState):
        if not validate_transition(self.state, new_state):
            raise ValueError(
                f"Invalid session state transition for candidate {self.candidate_pseudonym}: "
                f"cannot transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state
        await self._save()

    async def _save(self):
        receipt_json = json.dumps(self.receipt) if self.receipt else None
        
        async for conn in get_db():
            await conn.execute(
                """
                INSERT INTO candidate_sessions (candidate_pseudonym, session_id, state, paper_hash_hex, receipt)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (candidate_pseudonym) DO UPDATE SET
                    state = EXCLUDED.state,
                    paper_hash_hex = EXCLUDED.paper_hash_hex,
                    receipt = EXCLUDED.receipt,
                    updated_at = CURRENT_TIMESTAMP
                """,
                self.candidate_pseudonym,
                self.session_id,
                self.state.value,
                self.paper_hash_hex,
                receipt_json
            )

class SessionStore:
    """
    Persistent session manager backed by Postgres.
    """
    
    async def get_or_create_session(self, candidate_pseudonym: str, session_id: str) -> CandidateSession:
        session = await self.get_session(candidate_pseudonym)
        if session is None:
            session = CandidateSession(candidate_pseudonym, session_id)
            await session._save()
        return session

    async def get_session(self, candidate_pseudonym: str) -> CandidateSession | None:
        async for conn in get_db():
            row = await conn.fetchrow(
                "SELECT session_id, state, paper_hash_hex, receipt FROM candidate_sessions WHERE candidate_pseudonym = $1",
                candidate_pseudonym
            )
            if row is None:
                return None
            
            session = CandidateSession(candidate_pseudonym, row['session_id'])
            session.state = SessionState(row['state'])
            session.paper_hash_hex = row['paper_hash_hex']
            if row['receipt']:
                session.receipt = json.loads(row['receipt'])
            if session.paper_hash_hex:
                session.response_chain = ResponseChain(paper_hash_hex=session.paper_hash_hex)
            
            return session

# Global singleton instance
session_store = SessionStore()
