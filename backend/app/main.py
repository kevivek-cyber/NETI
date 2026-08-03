"""FastAPI entrypoint — walking skeleton.

Wires ceremony -> seed -> generate -> hash -> ledger -> receipt so the
whole pipeline can be exercised from /docs.

Everything here is in-memory and single-session on purpose. It exists to
pin the interfaces down, not to be the real service.

    TODO(role 3): Postgres, append-only grants, real session lifecycle,
                  bank decryption from the ceremony key
    TODO(role 1): Ed25519 block signing and chaining (INTEGRITY.md 4-5);
                  right now leaves accumulate but no block is ever sealed
    TODO(role 5): real k-of-n ceremony instead of open_session()
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .exam import seeds
from .generation import generator
from .generation.blueprint import BLUEPRINTS, DEMO
from .ledger import merkle

app = FastAPI(
    title="NETI",
    description="Papers that do not exist before the exam begins.",
    version="0.1.0",
)

# Dev only. TODO(role 5): a real exam terminal is same-origin and kiosked;
# this must not survive into any deployed build.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Session:
    """In-memory stand-in for a real exam session. TODO(role 3): persist."""

    def __init__(self) -> None:
        self.id = "DEMO-SESSION"
        self.master_seed = seeds.new_master_seed()
        self.pepper = seeds.new_session_pepper()
        self.blueprint = DEMO
        self.bank = generator.load_bank()
        self.leaves: list[bytes] = []
        self.issued: dict[str, int] = {}  # pseudonym -> leaf index


session = Session()


class PaperRequest(BaseModel):
    candidate_id: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "session": session.id, "leaves": len(session.leaves)}


@app.post("/session/open")
def open_session(blueprint: str = "DEMO") -> dict:
    """Stand-in for the k-of-n unlock ceremony (ARCHITECTURE.md section 2).

    A real ceremony reconstructs the bank key from 3 of 5 custodian
    shares, generates the seed and pepper in memory, and writes a signed
    genesis block. This just resets state.
    """
    if blueprint not in BLUEPRINTS:
        raise HTTPException(404, f"unknown blueprint {blueprint}")
    global session
    session = Session()
    session.blueprint = BLUEPRINTS[blueprint]
    return {
        "session_id": session.id,
        "blueprint": session.blueprint.name,
        "questions": session.blueprint.total_questions,
        "marks": session.blueprint.total_marks,
        "bank_version": session.bank["bank_version"],
        "blueprint_hash": session.blueprint.hash().hex(),
    }


@app.post("/exam/paper")
def issue_paper(request: PaperRequest) -> dict:
    """Generate this candidate's paper, ledger it, return it sealed.

    The assembled paper is never stored — only its hash. Re-requesting
    returns the same paper because generation is deterministic.
    """
    pid = seeds.pseudonym(session.pepper, request.candidate_id)
    seed = seeds.derive_seed(session.master_seed, session.id, pid)
    paper = generator.generate(seed, session.bank, session.blueprint)
    leaf = generator.paper_hash(paper)

    if pid in session.issued:
        index = session.issued[pid]  # idempotent: same candidate, same paper
    else:
        index = len(session.leaves)
        session.leaves.append(leaf)
        session.issued[pid] = index

    return {
        "pseudonym": pid,
        "leaf_index": index,
        "paper_hash": leaf.hex(),
        "paper": generator.sealed(paper),
    }


@app.get("/ledger/root")
def ledger_root() -> dict:
    return {
        "root": merkle.root(session.leaves).hex(),
        "leaf_count": len(session.leaves),
    }


@app.get("/ledger/receipt/{index}")
def receipt(index: int) -> dict:
    """Inclusion proof — the candidate's evidence of what they sat.

    TODO(role 1): sign this, and include block height once blocks exist.
    """
    try:
        proof = merkle.prove(session.leaves, index)
    except IndexError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {
        "leaf_index": proof.index,
        "leaf": proof.leaf.hex(),
        "root": merkle.root(session.leaves).hex(),
        "path": [{"side": s.side, "hash": s.hash.hex()} for s in proof.path],
    }
