"""Hash helpers over the canonical primitives.

Thin wrappers only — the domain tags and canonicalisation live in
canonical.py and are not reimplemented here.

The response-chain construction below follows INTEGRITY.md §8 *byte for
byte*. It is a permanent public contract: the standalone verifier will
recompute these hashes years from now against the published spec, so any
drift here silently invalidates every receipt ever issued. Change the spec
first, never the code alone.
"""

from typing import Any

from app.ledger.canonical import Domain, canonical_bytes, digest, hash_object, hex_of


def hash_leaf(paper: dict) -> str:
    return hex_of(hash_object(Domain.LEAF, paper))


def hash_receipt(receipt: dict) -> str:
    return hex_of(hash_object(Domain.RECEIPT, receipt))


def hash_response_initial(paper_hash_hex: str) -> str:
    """r_0 = SHA-256(0x03 || paper_hash)

    The paper hash is concatenated as raw bytes, per the spec — not
    wrapped in a JSON object first. Those produce different digests.
    """
    return hex_of(digest(Domain.RESPONSE, bytes.fromhex(paper_hash_hex)))


def hash_response_step(prev_hash_hex: str, event: dict[str, Any]) -> str:
    """r_i = SHA-256(0x03 || r_{i-1} || canonical_bytes(event_i))

    Note the shape: the previous digest is raw bytes and only the *event*
    is canonicalised. Wrapping both in one object would also be a valid
    construction, but it is not the one the spec defines and not the one
    the verifier will implement.
    """
    return hex_of(
        digest(Domain.RESPONSE, bytes.fromhex(prev_hash_hex), canonical_bytes(event))
    )
