"""Canonical serialisation and domain-separated hashing.

Implements docs/INTEGRITY.md sections 1 and 2. Every hash in NETI goes
through this module so that one object has exactly one byte representation
and a value valid in one position can never be replayed in another.

Owner: integrity layer (role 1). Changes here invalidate every existing
ledger, so treat the spec as normative.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any

SEP = (",", ":")


class Domain(bytes, Enum):
    """Domain separation tags. See INTEGRITY.md section 2."""

    LEAF = b"\x00"
    NODE = b"\x01"
    BLOCK = b"\x02"
    RESPONSE = b"\x03"
    RECEIPT = b"\x04"


class NonCanonical(ValueError):
    """Raised when a value has no single unambiguous representation."""


def _reject_floats(obj: Any, path: str = "$") -> None:
    """Floats are banned in hashed structures.

    Two machines can serialise the same float differently, which would make
    the same paper hash to two different leaves. IRT parameters are carried
    as fixed-precision strings instead.
    """
    if isinstance(obj, float):
        raise NonCanonical(f"float at {path}; use a fixed-precision string")
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise NonCanonical(f"non-string key at {path}")
            _reject_floats(value, f"{path}.{key}")
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            _reject_floats(value, f"{path}[{index}]")


def canonical_bytes(obj: Any) -> bytes:
    """Serialise to the one byte form that gets hashed.

    Approximates RFC 8785 (JCS): sorted keys, no insignificant whitespace,
    UTF-8. Sufficient because we forbid floats, which is where JCS and
    json.dumps actually diverge.

    TODO(role 1): swap for a full RFC 8785 implementation before any exam
    that must stay verifiable across language runtimes.
    """
    _reject_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=SEP, ensure_ascii=False).encode()


def digest(domain: Domain, *parts: bytes) -> bytes:
    """SHA-256 over a domain tag followed by the given byte strings."""
    h = hashlib.sha256()
    h.update(domain.value)
    for part in parts:
        h.update(part)
    return h.digest()


def hash_object(domain: Domain, obj: Any) -> bytes:
    """Canonicalise an object and hash it under a domain tag."""
    return digest(domain, canonical_bytes(obj))


def hex_of(value: bytes) -> str:
    return value.hex()
