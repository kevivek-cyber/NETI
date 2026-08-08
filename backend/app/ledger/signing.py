"""Ed25519 signing for ledger blocks.

Implements CUSTODY.md §4, which supersedes INTEGRITY.md §5's single
session key.

## Why blocks carry three personal signatures

Hashes prove nothing changed. They do not prove *who wrote the record*.
Without signatures the exam authority could discard the real ledger and
publish a fabricated one that verifies perfectly — every hash internally
consistent, every Merkle root correct, and entirely fictional.

A single institutional key does not fix this. When a scandal breaks,
"who signed this?" answers "the exam authority", which is the same
useless answer every past inquiry has produced.

So a block is signed by **three named officials, personally**, and is
invalid unless all three come from **different institutions**:

    official_1  centre superintendent      -> centre tier
    official_2  district observer          -> independent tier
    official_3  authority representative   -> authority tier

Three people from the same office is one institution holding three keys,
and the separation collapses. That check is enforced here rather than
left to procedure.

## Known weakness, documented rather than solved

A personal key is stealable and shareable in a way an HSM key is not. A
corrupt official can hand theirs over, and the ledger then names an
innocent person. Binding signature to a biometric at signing time
mitigates it, at the cost of hardware in every centre. Attribution is
not proof of guilt; it narrows an investigation from millions to three.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from enum import Enum

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

REQUIRED_SIGNATURES = 3


class Institution(str, Enum):
    """The three tiers that must each be represented on every block."""

    CENTRE = "centre"
    INDEPENDENT = "independent"
    AUTHORITY = "authority"


class SigningError(Exception):
    """A block's signature set does not satisfy the quorum rule."""


@dataclass(frozen=True)
class Official:
    """A signing official's public identity.

    `official_id` is what appears in the custody code and the roster; the
    ledger stores it so a signature can be traced to a person.
    """

    official_id: str
    institution: Institution
    public_key: Ed25519PublicKey

    def public_key_hex(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()


@dataclass(frozen=True)
class Signature:
    official_id: str
    institution: Institution
    signature: bytes

    def as_dict(self) -> dict:
        return {
            "official_id": self.official_id,
            "institution": self.institution.value,
            "signature": self.signature.hex(),
        }


def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Generate an official's personal signing key.

    In deployment these live on smart cards or HSM tokens and are
    enrolled once; this exists for tests and for the ceremony rehearsal.
    """
    private = Ed25519PrivateKey.generate()
    return private, private.public_key()


def sign(private_key: Ed25519PrivateKey, official: Official, block_hash: bytes) -> Signature:
    """One official signs a block hash."""
    return Signature(
        official_id=official.official_id,
        institution=official.institution,
        signature=private_key.sign(block_hash),
    )


def verify_one(official: Official, block_hash: bytes, signature: bytes) -> bool:
    try:
        official.public_key.verify(signature, block_hash)
        return True
    except InvalidSignature:
        return False


def verify_quorum(
    block_hash: bytes,
    signatures: list[Signature],
    roster: dict[str, Official],
) -> None:
    """Raise unless the block carries a valid three-institution quorum.

    Checked, in order:
      1. exactly three signatures, no more
      2. no official signs twice
      3. every signer is on the committed roster
      4. every signature verifies against that official's key
      5. all three institutions are represented

    Raises rather than returning False so a caller cannot accidentally
    treat a falsy result as success.
    """
    if len(signatures) != REQUIRED_SIGNATURES:
        raise SigningError(
            f"block needs exactly {REQUIRED_SIGNATURES} signatures, got {len(signatures)}"
        )

    seen_officials: set[str] = set()
    seen_institutions: set[Institution] = set()

    for sig in signatures:
        if sig.official_id in seen_officials:
            raise SigningError(f"official {sig.official_id} signed twice")
        seen_officials.add(sig.official_id)

        official = roster.get(sig.official_id)
        if official is None:
            raise SigningError(
                f"official {sig.official_id} is not on the committed roster"
            )
        if official.institution != sig.institution:
            raise SigningError(
                f"official {sig.official_id} claims institution "
                f"{sig.institution.value} but the roster says "
                f"{official.institution.value}"
            )
        if not verify_one(official, block_hash, sig.signature):
            raise SigningError(f"signature from {sig.official_id} does not verify")

        seen_institutions.add(official.institution)

    if len(seen_institutions) != REQUIRED_SIGNATURES:
        present = sorted(i.value for i in seen_institutions)
        raise SigningError(
            "all three institutions must be represented; got "
            f"{present}. Three officials from the same body is one "
            "institution holding three keys."
        )


def roster_hash(roster: dict[str, Official]) -> bytes:
    """Commitment to who is permitted to sign this session.

    Written into the genesis block before any paper exists, so swapping
    in a different set of officials later is visible. This is what makes
    the grinding defence in CUSTODY.md §2.2 enforceable.
    """
    from .canonical import Domain, canonical_bytes, digest

    # Sorted by official_id so the same roster always hashes identically
    # regardless of dict insertion order.
    entries = [
        {
            "official_id": official.official_id,
            "institution": official.institution.value,
            "public_key": official.public_key_hex(),
        }
        for _, official in sorted(roster.items())
    ]
    return digest(Domain.BLOCK, canonical_bytes(entries))


def compare_digest(a: bytes, b: bytes) -> bool:
    """Constant-time comparison (INTEGRITY.md §12)."""
    return hmac.compare_digest(a, b)
