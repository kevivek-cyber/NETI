from app.ledger.canonical import Domain, hash_object, hex_of
from typing import Any

def hash_leaf(paper: dict) -> str:
    return hex_of(hash_object(Domain.LEAF, paper))

def hash_receipt(receipt: dict) -> str:
    return hex_of(hash_object(Domain.RECEIPT, receipt))

def hash_response_initial(paper_hash_hex: str) -> str:
    return hex_of(hash_object(Domain.RESPONSE, {"paper_hash": paper_hash_hex}))

def hash_response_step(prev_hash_hex: str, event: dict[str, Any]) -> str:
    return hex_of(hash_object(Domain.RESPONSE, {"prev": prev_hash_hex, "event": event}))
