# NETI — instructions for GitHub Copilot

**Read `AGENTS.md` at the repository root. It is the canonical context file.**

NETI is an examination system where a question paper does not exist before the exam begins. Each candidate's paper is generated on the spot from an encrypted item bank, and every paper is hashed into a tamper-evident append-only ledger so the exam can be publicly audited afterwards.

## Invariants — a suggestion violating any of these is wrong

- **Never persist an assembled paper.** Papers exist in memory only; only their hash is stored.
- **The generator must stay deterministic.** `generate(seed, bank_version, blueprint)` must return byte-identical output forever. No unseeded randomness, no timestamps, no dict-order dependence, no LLM calls at exam time.
- **Never suggest caching, memoization, parallelism, or retries in the generator.** These break determinism, which is the entire audit guarantee.
- **The ledger is append-only.** Never generate `UPDATE` or `DELETE` against ledger tables.
- **No custom crypto.** Use `hashlib`, `cryptography` (Ed25519), and `pycryptodome` as specified in `docs/INTEGRITY.md`.
- **No personally identifying data on the ledger.** Pseudonyms and hashes only — ledger rows are permanent and cannot be deleted.
- **Never weaken a security property to make a test pass.**

## Stack

Python 3.11 + FastAPI, PostgreSQL 15, React 18 + Vite + TypeScript, Docker Compose.

## Conventions

- Commits: imperative with a scope prefix — `ledger: add Merkle inclusion proofs`
- Branches: `<name>/<feature>`; `main` is protected
- Tests are mandatory for `ledger/`, `generation/`, and scoring
- Docs live in `docs/` and are part of any behaviour-changing diff
