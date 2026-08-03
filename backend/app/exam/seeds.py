"""Per-candidate seed derivation.

Implements docs/INTEGRITY.md section 7.

Note the two-step design. The ledger and the seed both key off a
PSEUDONYM, never the roll number:

    pseudonym = HMAC(session_pepper, candidate_id)
    seed      = HKDF(master_seed, salt=session_id, info=pseudonym)

Roll numbers are sequential and enumerable. If the seed keyed off them
directly, publishing master_seed after the exam (which public audit
requires) would let anyone regenerate any named candidate's paper. The
pepper is generated in the unlock ceremony and NEVER published, so the
public can verify all papers were generated correctly without being able
to link one to a person.

Owner: integrity layer (role 1).
"""

from __future__ import annotations

import hmac
import secrets
from hashlib import sha256

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

SEED_BYTES = 32
INFO_PREFIX = b"neti/paper/v1|"  # bump the version if derivation ever changes


def new_master_seed() -> bytes:
    """Generated inside the unlock ceremony at T=0, never before."""
    return secrets.token_bytes(SEED_BYTES)


def new_session_pepper() -> bytes:
    """Generated in the ceremony. Never published, never logged."""
    return secrets.token_bytes(SEED_BYTES)


def pseudonym(session_pepper: bytes, candidate_id: str) -> str:
    """Stable, unlinkable ledger identity for a candidate."""
    return hmac.new(session_pepper, candidate_id.encode(), sha256).hexdigest()


def derive_seed(master_seed: bytes, session_id: str, pseudonym_hex: str) -> bytes:
    """Deterministic 32-byte seed for one candidate's paper."""
    return HKDF(
        algorithm=hashes.SHA256(),
        length=SEED_BYTES,
        salt=session_id.encode(),
        info=INFO_PREFIX + pseudonym_hex.encode(),
    ).derive(master_seed)
