"""
Per-candidate response hash chain tracker per INTEGRITY.md §8.
Validates client response history integrity and prevents post-hoc mark alteration.
"""

from typing import Any
from app.ledger.hashing import hash_response_initial, hash_response_step


class ResponseChain:
    def __init__(self, paper_hash_hex: str):
        self.paper_hash_hex: str = paper_hash_hex
        self.current_r_hex: str = hash_response_initial(paper_hash_hex)
        self.events: list[dict[str, Any]] = []

    def add_event(self, event: dict[str, Any]) -> str:
        """
        Appends an event to the chain: r_i = SHA-256(0x03 ‖ r_{i-1} ‖ canonical_bytes(event_i))
        Returns new current_r_hex.
        """
        self.current_r_hex = hash_response_step(self.current_r_hex, event)
        self.events.append(event)
        return self.current_r_hex

    @staticmethod
    def verify_chain(paper_hash_hex: str, events: list[dict[str, Any]], expected_r_n: str) -> bool:
        """
        Verifies that replaying `events` over `paper_hash_hex` produces `expected_r_n`.
        """
        current = hash_response_initial(paper_hash_hex)
        for event in events:
            current = hash_response_step(current, event)
        return current == expected_r_n
