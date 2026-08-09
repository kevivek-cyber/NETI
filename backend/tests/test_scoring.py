import pytest
import asyncio
from app.api.ceremony_router import ceremony_manager
from app.exam.scoring import compute_score
from app.db.connection import get_db

@pytest.mark.asyncio
async def test_compute_score(monkeypatch):
    # Mock get_db to return a mock connection
    class MockConnection:
        async def fetchrow(self, query, *args):
            # We mock the responses to match the correct answers
            # We know from test_determinism that item_id PHY-KIN-0001 answer index might be 0, 1, 2, or 3
            # We will just return a mock response that gets scored
            
            import json
            mock_events = [
                {"question_id": "PHY-KIN-0001", "selected_option_index": 2, "timestamp_iso": "2026-08-09T10:00:00Z"},
                {"question_id": "CHE-ATM-0002", "selected_option_index": -1, "timestamp_iso": "2026-08-09T10:01:00Z"},
                {"question_id": "BOT-CEL-0001", "selected_option_index": 1, "timestamp_iso": "2026-08-09T10:02:00Z"}
            ]
            return {"responses": json.dumps(mock_events)}
            
    async def mock_get_db():
        yield MockConnection()
        
    monkeypatch.setattr("app.exam.scoring.get_db", mock_get_db)
    
    # Mock keys
    ceremony_manager.master_seed = b"test_master_seed_32_bytes_long_1"
    ceremony_manager.bank_key = b"BANK_MASTER_KEY_32_BYTES_0000000"
    ceremony_manager.answer_key = b"ANSWER_MASTER_KEY_32_BYTES_00000"
    
    score_result = await compute_score("mock_pseudonym", "test_session_id")
    
    assert "score" in score_result
    assert "correct" in score_result
    assert "incorrect" in score_result
    assert "omitted" in score_result
