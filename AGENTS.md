# NETI — Non-Exploitable Test Integrity

**Canonical context file.** Read this before touching code, whichever AI tool or editor you're using.
`CLAUDE.md`, `.github/copilot-instructions.md`, and `.cursor/rules/` all defer to this file — edit this one, not those.

## What this project is

NETI is an examination system designed so that **a question paper does not exist, in any form, anywhere, before the exam begins.**

The NEET paper leak problem is not a hacking problem. It is a *logistics* problem: one paper is authored months early, printed, boxed, trucked, and parked in bank vaults across the country. Every one of those steps is a human with physical access to the answer key. No amount of encryption fixes a printed page in a van.

NETI removes the artifact. Each candidate receives a **unique paper, generated on the spot** at exam start, from an encrypted item bank whose unlock key does not exist in assembled form until T=0. Every paper is hashed into a **tamper-evident Merkle ledger** so that after the exam anyone — press, courts, a student — can independently verify that the paper they sat is exactly the paper the authority committed to, and that nobody was quietly handed an easier one.

Two properties define the whole system:

1. **Nothing to leak before T=0.** No pre-assembled paper. No decryptable bank. No single custodian holding the unlock key.
2. **Everything provable after T=0.** Every paper, every seed, every score is reproducible and publicly auditable from a signed chain.

## Non-negotiable invariants

If a change violates any of these, it is wrong regardless of how well it works:

- **No assembled paper is ever persisted.** Papers are generated in memory, served, and discarded. Only the hash survives. If you find yourself writing `papers` to a table, stop.
- **The generator is deterministic.** `generate(seed, bank_version, blueprint) → paper` must return byte-identical output forever. Audit depends on it. No `random` without an explicit seeded RNG, no wall-clock, no dict iteration order, no unseeded LLM calls at exam time.
- **The ledger is append-only.** No `UPDATE`, no `DELETE` on ledger tables. Ever. Enforced at the DB grant level, not just in code.
- **The item bank is encrypted at rest and the key is split.** No single machine, person, or service can decrypt the bank alone.
- **Every paper must be psychometrically equivalent.** Unique ≠ unfair. See `docs/AI_PIPELINE.md` § Equating. A paper that is 8% harder than another is a lawsuit.
- **Answer keys are derived, never authored alongside the paper at exam time.** Keys stay sealed until the exam window closes.
- **No personally identifying data on the ledger.** The ledger is permanent by construction and cannot honour a deletion request. Pseudonyms and hashes only. See `docs/PRIVACY.md`.

## Architecture at a glance

```
Authoring  →  Item Bank (encrypted, versioned, IRT-calibrated)
                     │
              [T-0: threshold key release, k-of-n]
                     │
Exam start  →  Seed Service ──> per-candidate seed = HKDF(master_seed, pseudonym)
                     │
               Generator (deterministic) ──> paper (in memory only)
                     │              │
                Student client      └──> SHA-256 leaf ──> Merkle tree ──> signed block ──> Ledger
                     │
Post-exam   →  Reveal seeds + bank version ──> anyone re-runs generator ──> verifies root
```

Full detail: `docs/ARCHITECTURE.md`. Crypto spec: `docs/INTEGRITY.md`. Generation: `docs/AI_PIPELINE.md`. Attack surface: `docs/THREAT_MODEL.md`.

## Stack

| Layer | Choice | Why |
|---|---|---|
| API | Python 3.11 + FastAPI | Same language as the ML side, async, typed |
| DB | PostgreSQL 15 | Append-only ledger via table grants; JSONB for items |
| Generation | Templates + seeded RNG + offline LLM paraphrase | Correctness guaranteed by symbolic validation, not by the model |
| Crypto | `hashlib`, `cryptography` (Ed25519), Shamir via `pycryptodome` | Stdlib-first; no bespoke crypto |
| Frontend | React 18 + Vite + TypeScript | Student exam client + invigilator/admin console |
| Infra | Docker Compose (dev), single-node k8s (demo) | Must run offline at an exam centre |

## Repository layout

```
backend/
  app/
    main.py              FastAPI entrypoint
    core/                config, security primitives
    ledger/              merkle.py, chain.py, signing.py  ← integrity core
    generation/          blueprint.py, sampler.py, templates/, validators/
    bank/                item schema, encryption, versioning
    exam/                session orchestration, delivery, scoring
    api/                 routers
  tests/
frontend/                React exam client + admin console
ml/                      past-paper parsing, IRT calibration, LLM variant pipeline
docs/                    design docs (read these before proposing changes)
scripts/                 verify_ledger.py and other operator tools
```

## Working agreements

- **Branches:** `main` is protected. Work on `<name>/<feature>`. PRs need one review; anything under `backend/app/ledger/` or `backend/app/bank/` needs the owner's review.
- **Tests:** `ledger/`, `generation/`, and scoring are non-optional test targets. Determinism gets a property test (same seed → same paper, across processes).
- **Commits:** imperative mood, scope prefix — `ledger: add Merkle inclusion proofs`.
- **Secrets:** never commit. `.env.example` documents every variable; `.env` is gitignored.
- **Docs are part of the diff.** Changing the seed derivation or blueprint without updating `docs/` is an incomplete PR.

## Team

5 people. Owner: Vivek (`kevivek-cyber`) — tech lead, owns the integrity layer. Role split and who to ask about what: `docs/TEAM.md`.

## Current status

Phase 0 — scaffolding. See `docs/ROADMAP.md` for what is actually built vs. planned. Nothing here is production-certified; this is a student capstone demonstrating a viable mechanism, not a deployment for a live national exam.

## Rules for AI assistants

Applies to Claude Code, Cursor, Copilot, Codex, Gemini CLI, or anything else:

- Prefer editing existing modules over adding parallel ones; this codebase is small and should stay legible to five students.
- When touching `ledger/`, show the hash-domain-separation reasoning in the PR description, not just the code.
- **Do not add caching, memoization, parallelism, or retry logic to the generator.** It breaks determinism in ways the tests may not catch, and determinism is the entire audit guarantee.
- If a task seems to require storing a generated paper, re-read the invariants above. The answer is a hash, or regeneration from seed — never a stored blob.
- Do not invent crypto. Use the primitives named in `docs/INTEGRITY.md`. If the spec and the code disagree, the spec is right and the code is a bug.
- Do not weaken a security property to make a test pass. Raise it instead.
