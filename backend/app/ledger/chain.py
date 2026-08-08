"""Hash-chained, signed blocks.

Implements INTEGRITY.md §4, with the three-signature quorum from
CUSTODY.md §4.

    block_hash = SHA-256(0x02 ‖ canonical_bytes(header))

Each header carries the previous block's hash, so altering any block
invalidates every block after it. The chain is append-only in the same
sense the database is: there is no operation here that rewrites history,
and `append` refuses a block that does not extend the current head.

## The genesis block

Written during the unlock ceremony, **before any paper exists**. It
carries `leaf_count: 0` and commits four hashes:

    bank_version_hash      which questions exist
    generator_source_hash  which code will build the papers
    blueprint_hash         what shape the papers take
    official_roster_hash   who is permitted to sign

Publishing those before T=0 is what makes the pre-exam commitment
binding. `generator_source_hash` in particular is the defence against a
doctored build: if the deployed generator cannot be reproduced from the
published source, verification fails. That only works if builds are
reproducible, which is a separate deliverable.

The roster commitment is what makes grinding detectable (CUSTODY.md
§2.2) — officials cannot quietly swap themselves in and out to reroll a
candidate's paper, because the permitted set was fixed before the exam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import Domain, canonical_bytes, digest
from .signing import Official, Signature, SigningError, verify_quorum

# The genesis block has no predecessor. 32 zero bytes, never a hash of
# anything — a real hash here would imply a block that does not exist.
GENESIS_PREV = bytes(32)

BLOCK_VERSION = 1


@dataclass(frozen=True)
class BlockHeader:
    """Everything committed by a block's signature.

    Timestamps are strings, not floats: canonical_bytes rejects floats
    because two machines can serialise them differently, which would make
    the same block hash two ways.
    """

    version: int
    session_id: str
    centre_id: str
    height: int
    prev_block_hash: str
    merkle_root: str
    leaf_count: int
    first_leaf_index: int
    bank_version_hash: str
    generator_source_hash: str
    blueprint_hash: str
    official_roster_hash: str
    opened_at: str
    closed_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "session_id": self.session_id,
            "centre_id": self.centre_id,
            "height": self.height,
            "prev_block_hash": self.prev_block_hash,
            "merkle_root": self.merkle_root,
            "leaf_count": self.leaf_count,
            "first_leaf_index": self.first_leaf_index,
            "bank_version_hash": self.bank_version_hash,
            "generator_source_hash": self.generator_source_hash,
            "blueprint_hash": self.blueprint_hash,
            "official_roster_hash": self.official_roster_hash,
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
        }

    def hash(self) -> bytes:
        """block_hash = SHA-256(0x02 ‖ canonical_bytes(header))"""
        return digest(Domain.BLOCK, canonical_bytes(self.as_dict()))


@dataclass(frozen=True)
class Block:
    header: BlockHeader
    signatures: tuple[Signature, ...]

    @property
    def hash(self) -> bytes:
        return self.header.hash()

    def as_dict(self) -> dict[str, Any]:
        return {
            "header": self.header.as_dict(),
            "block_hash": self.hash.hex(),
            "signatures": [s.as_dict() for s in self.signatures],
        }


class ChainError(Exception):
    """A block does not validly extend the chain."""


@dataclass
class Chain:
    """An append-only sequence of signed, hash-linked blocks."""

    session_id: str
    centre_id: str
    roster: dict[str, Official]
    blocks: list[Block] = field(default_factory=list)

    @property
    def height(self) -> int:
        return len(self.blocks)

    @property
    def head_hash(self) -> bytes:
        return self.blocks[-1].hash if self.blocks else GENESIS_PREV

    @property
    def next_leaf_index(self) -> int:
        if not self.blocks:
            return 0
        last = self.blocks[-1].header
        return last.first_leaf_index + last.leaf_count

    def build_header(
        self,
        *,
        merkle_root: str,
        leaf_count: int,
        bank_version_hash: str,
        generator_source_hash: str,
        blueprint_hash: str,
        opened_at: str,
        closed_at: str,
    ) -> BlockHeader:
        """Construct the next header, chained to the current head.

        Callers never set height, prev_block_hash or first_leaf_index —
        those come from the chain, so a caller cannot accidentally fork it.
        """
        from .signing import roster_hash

        return BlockHeader(
            version=BLOCK_VERSION,
            session_id=self.session_id,
            centre_id=self.centre_id,
            height=self.height,
            prev_block_hash=self.head_hash.hex(),
            merkle_root=merkle_root,
            leaf_count=leaf_count,
            first_leaf_index=self.next_leaf_index,
            bank_version_hash=bank_version_hash,
            generator_source_hash=generator_source_hash,
            blueprint_hash=blueprint_hash,
            official_roster_hash=roster_hash(self.roster).hex(),
            opened_at=opened_at,
            closed_at=closed_at,
        )

    def append(self, block: Block) -> None:
        """Add a block, refusing anything that does not extend the head.

        Every check raises. There is no path here that quietly accepts a
        block that fails verification — a ledger that skips a bad block
        rather than rejecting it is worse than no ledger, because it looks
        complete.
        """
        header = block.header

        if header.version != BLOCK_VERSION:
            raise ChainError(f"unknown block version {header.version}")
        if header.session_id != self.session_id:
            raise ChainError(
                f"block belongs to session {header.session_id}, chain is {self.session_id}"
            )
        if header.height != self.height:
            raise ChainError(
                f"block height {header.height} does not follow chain height {self.height}"
            )
        if header.prev_block_hash != self.head_hash.hex():
            raise ChainError(
                "prev_block_hash does not match the current head; this block "
                "belongs to a different chain or history has been rewritten"
            )
        if header.first_leaf_index != self.next_leaf_index:
            raise ChainError(
                f"first_leaf_index {header.first_leaf_index} leaves a gap; "
                f"expected {self.next_leaf_index}"
            )
        if header.leaf_count < 0:
            raise ChainError("leaf_count cannot be negative")
        if self.blocks and header.leaf_count == 0:
            raise ChainError("only the genesis block may carry zero leaves")

        try:
            verify_quorum(block.hash, list(block.signatures), self.roster)
        except SigningError as exc:
            raise ChainError(f"block {header.height} rejected: {exc}") from exc

        self.blocks.append(block)

    def verify(self) -> None:
        """Re-verify the whole chain from genesis.

        What the standalone verifier runs. Deliberately recomputes rather
        than trusting anything cached: the point is to check the record,
        not to check our own bookkeeping about the record.
        """
        prev = GENESIS_PREV
        expected_leaf_index = 0

        for i, block in enumerate(self.blocks):
            header = block.header

            if header.height != i:
                raise ChainError(f"block at position {i} claims height {header.height}")
            if header.prev_block_hash != prev.hex():
                raise ChainError(f"chain broken at height {i}: prev_block_hash mismatch")
            if header.first_leaf_index != expected_leaf_index:
                raise ChainError(f"leaf index gap at height {i}")
            if i == 0 and header.leaf_count != 0:
                raise ChainError("genesis block must carry zero leaves")

            try:
                verify_quorum(block.hash, list(block.signatures), self.roster)
            except SigningError as exc:
                raise ChainError(f"block {i} failed signature check: {exc}") from exc

            prev = block.hash
            expected_leaf_index += header.leaf_count

    def as_bundle(self) -> list[dict[str, Any]]:
        """Block headers plus signatures — the published session bundle."""
        return [b.as_dict() for b in self.blocks]
