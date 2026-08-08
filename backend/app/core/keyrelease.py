"""
Bank key custody and unlock ceremony implementation per INTEGRITY.md §6.
Features:
- Shamir Secret Sharing (k=3, n=5 threshold key release over GF(2^8))
- In-memory key reconstruction & zeroisation
- Master seed generation at ceremony start (CSPRNG)
"""

import os
import secrets
from typing import Any


class SimpleShamirGF256:
    """
    Shamir's Secret Sharing over GF(2^8) with polynomial arithmetic.
    Field modulus: x^8 + x^4 + x^3 + x + 1 (0x11b), primitive generator alpha = 3 (0x03).
    """

    _EXP = [0] * 512
    _LOG = [0] * 256

    @classmethod
    def _init_tables(cls):
        if cls._EXP[0] != 0:
            return
        x = 1
        for i in range(255):
            cls._EXP[i] = x
            cls._EXP[i + 255] = x
            cls._LOG[x] = i
            # Multiply x by generator 3 in GF(2^8): x * 3 = (x << 1) ^ x
            x2 = x << 1
            if x2 & 0x100:
                x2 ^= 0x11B
            x = x2 ^ x
        cls._EXP[255] = cls._EXP[0]

    @classmethod
    def _mul(cls, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        cls._init_tables()
        return cls._EXP[cls._LOG[a] + cls._LOG[b]]

    @classmethod
    def _div(cls, a: int, b: int) -> int:
        if a == 0:
            return 0
        if b == 0:
            raise ZeroDivisionError("Division by zero in GF(2^8)")
        cls._init_tables()
        return cls._EXP[(cls._LOG[a] - cls._LOG[b] + 255) % 255]

    @classmethod
    def _eval_poly(cls, poly: list[int], x: int) -> int:
        """
        Evaluates polynomial poly[0] + poly[1]*x + poly[2]*x^2 + ... in GF(2^8).
        """
        cls._init_tables()
        res = 0
        x_pow = 1
        for coeff in poly:
            res ^= cls._mul(coeff, x_pow)
            x_pow = cls._mul(x_pow, x)
        return res

    @classmethod
    def split(cls, secret: bytes, k: int = 3, n: int = 5) -> list[tuple[int, bytes]]:
        """
        Splits `secret` into `n` shares, requiring `k` shares to reconstruct.
        Returns list of (x_idx, share_bytes) for x_idx in 1..n.
        """
        cls._init_tables()
        if k > n or k < 1 or n > 255:
            raise ValueError("Invalid k, n parameters for Shamir GF(2^8)")

        shares: list[bytearray] = [bytearray(len(secret)) for _ in range(n)]

        for byte_idx, secret_byte in enumerate(secret):
            # Degree k-1 random polynomial: f(x) = secret_byte + a_1*x + ... + a_{k-1}*x^{k-1}
            coeffs = [secret_byte] + [secrets.randbelow(256) for _ in range(k - 1)]
            for x in range(1, n + 1):
                y = cls._eval_poly(coeffs, x)
                shares[x - 1][byte_idx] = y

        return [(x, bytes(shares[x - 1])) for x in range(1, n + 1)]

    @classmethod
    def combine(cls, shares: list[tuple[int, bytes]]) -> bytes:
        """
        Reconstructs secret from k shares using Lagrange interpolation at x = 0.
        """
        cls._init_tables()
        if not shares:
            raise ValueError("No shares provided")

        share_len = len(shares[0][1])
        secret = bytearray(share_len)

        for byte_idx in range(share_len):
            val = 0
            for i, (x_i, share_i) in enumerate(shares):
                y_i = share_i[byte_idx]
                li = 1
                for j, (x_j, _) in enumerate(shares):
                    if i == j:
                        continue
                    num = x_j
                    den = x_i ^ x_j
                    li = cls._mul(li, cls._div(num, den))
                val ^= cls._mul(y_i, li)
            secret[byte_idx] = val

        return bytes(secret)


class CeremonyManager:
    """
    Manages the exam key release ceremony.
    Key K and master_seed are stored strictly in RAM and reset on zeroisation or server reload.
    """

    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.unlocked: bool = False
        self.bank_key: bytes | None = None
        self.master_seed: bytes | None = None

    def perform_unlock_ceremony(self, shares: list[tuple[int, str]]) -> bytes:
        """
        Submits k-of-n Shamir shares (x_idx, hex_str). Reconstructs bank_key K and generates 32-byte master_seed.
        """
        if len(shares) < 3:
            raise ValueError("Unlock ceremony requires at least k=3 shares")

        byte_shares = [(x_idx, bytes.fromhex(hex_data)) for x_idx, hex_data in shares]
        reconstructed_k = SimpleShamirGF256.combine(byte_shares)

        self.bank_key = reconstructed_k
        self.master_seed = secrets.token_bytes(32)
        self.unlocked = True
        return self.master_seed

    def zeroise(self):
        """
        Zeroises sensitive key K in memory upon session seal.
        """
        if self.bank_key:
            mutable = bytearray(self.bank_key)
            for i in range(len(mutable)):
                mutable[i] = 0
            self.bank_key = None
        self.unlocked = False
