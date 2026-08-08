"""
Candidate exam session lifecycle state machine per ROADMAP.md Phase 4 & ARCHITECTURE.md §6.
"""

from enum import Enum


class SessionState(str, Enum):
    REGISTERED = "registered"
    CHECKED_IN = "checked_in"
    PAPER_ISSUED = "paper_issued"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    SEALED = "sealed"


# Valid state transitions
VALID_TRANSITIONS: dict[SessionState, list[SessionState]] = {
    SessionState.REGISTERED: [SessionState.CHECKED_IN],
    SessionState.CHECKED_IN: [SessionState.PAPER_ISSUED],
    SessionState.PAPER_ISSUED: [SessionState.IN_PROGRESS],
    SessionState.IN_PROGRESS: [SessionState.SUBMITTED],
    SessionState.SUBMITTED: [SessionState.SEALED],
    SessionState.SEALED: [],
}


def validate_transition(current: SessionState, target: SessionState) -> bool:
    """
    Validates if transitioning from `current` state to `target` state is legal.
    """
    allowed = VALID_TRANSITIONS.get(current, [])
    return target in allowed
