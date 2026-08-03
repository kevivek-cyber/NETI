"""Deterministic RNG for paper generation.

Counter-based: block_i = SHA-256(seed || counter_i). Deliberately NOT
random.Random, whose internals are a CPython implementation detail we
would be betting a decade of auditability on.

Guarantee: same seed produces the same stream on any machine, any OS, any
Python 3.x, forever. docs/INTEGRITY.md section 11 step 5 depends on it.
"""

from __future__ import annotations

import hashlib
from typing import Sequence, TypeVar

T = TypeVar("T")


class DeterministicRNG:
    def __init__(self, seed: bytes) -> None:
        if len(seed) != 32:
            raise ValueError("seed must be 32 bytes")
        self._seed = seed
        self._counter = 0
        self._buffer = b""

    def _refill(self) -> None:
        block = hashlib.sha256(
            self._seed + self._counter.to_bytes(8, "big")
        ).digest()
        self._counter += 1
        self._buffer += block

    def _take(self, n: int) -> bytes:
        while len(self._buffer) < n:
            self._refill()
        out, self._buffer = self._buffer[:n], self._buffer[n:]
        return out

    def below(self, n: int) -> int:
        """Uniform integer in [0, n). Rejection sampling — no modulo bias."""
        if n <= 0:
            raise ValueError("n must be positive")
        if n == 1:
            return 0
        bits = (n - 1).bit_length()
        nbytes = (bits + 7) // 8
        mask = (1 << bits) - 1
        while True:
            candidate = int.from_bytes(self._take(nbytes), "big") & mask
            if candidate < n:
                return candidate

    def choice(self, items: Sequence[T]) -> T:
        return items[self.below(len(items))]

    def shuffled(self, items: Sequence[T]) -> list[T]:
        """Fisher-Yates. Returns a new list; does not mutate the input."""
        out = list(items)
        for i in range(len(out) - 1, 0, -1):
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out

    def sample(self, items: Sequence[T], k: int) -> list[T]:
        if k > len(items):
            raise ValueError(f"cannot sample {k} from {len(items)} items")
        return self.shuffled(items)[:k]
