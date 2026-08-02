# NETI — context for Claude Code

**→ Read [AGENTS.md](AGENTS.md) first. It is the canonical context file for this repo.**

This file exists so Claude Code auto-loads context. The full project description, stack, layout, and working agreements live in `AGENTS.md` — maintain that file, not this one.

The critical rules are duplicated below so they are always in context even if `AGENTS.md` has not been opened.

## Non-negotiable invariants

- **No assembled paper is ever persisted.** Generated in memory, served, discarded. Only the hash survives.
- **The generator is deterministic.** `generate(seed, bank_version, blueprint) → paper` must be byte-identical forever. No unseeded RNG, no wall-clock, no LLM calls at exam time.
- **The ledger is append-only.** No `UPDATE`/`DELETE` on ledger tables, enforced at the DB grant level.
- **The item bank is encrypted at rest and the key is split k-of-n.** No single party can decrypt it alone.
- **Every paper must be psychometrically equivalent.** Unique ≠ unfair.
- **Answer keys stay sealed** until the exam window closes.
- **No personally identifying data on the ledger.** It is permanent by construction and cannot honour deletion requests.

## Rules for AI assistants

- Do not add caching, memoization, parallelism, or retry logic to the generator — it breaks determinism, which is the entire audit guarantee.
- If a task seems to require storing a generated paper, the answer is a hash or regeneration from seed, never a stored blob.
- Do not invent crypto. Use the primitives in `docs/INTEGRITY.md`; if spec and code disagree, the spec is right.
- Do not weaken a security property to make a test pass.
- Anything under `backend/app/ledger/` or `backend/app/bank/` needs the owner's review.

## Docs map

| Doc | Read when |
|---|---|
| [AGENTS.md](AGENTS.md) | Always, first |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | You need the component and data-flow picture |
| [docs/INTEGRITY.md](docs/INTEGRITY.md) | Touching hashing, Merkle, signing, or key release |
| [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) | Working on question generation or equating |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | Proposing or challenging a security change |
| [docs/TEAM.md](docs/TEAM.md) | You need to know who owns what |
| [docs/ROADMAP.md](docs/ROADMAP.md) | You want to know what's real vs. planned |
