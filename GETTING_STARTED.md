# Getting started

Read [AGENTS.md](AGENTS.md) first — especially the invariants. Then get it running, then find your role below.

## Run it

Two terminals.

```bash
# terminal 1 — backend
cd backend
pip install -r requirements.txt
pytest                              # 26 tests must pass
uvicorn app.main:app --reload       # http://localhost:8000/docs

# terminal 2 — frontend
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

Check in with any roll number. You get a paper generated on the spot, and on submit a receipt with a Merkle inclusion proof. Enter a different roll number and you get a different paper. Enter the same one twice and you get the identical paper — that is determinism, and it is what makes the exam auditable.

## What already works

```
check-in → pseudonym → seed → generate → hash → Merkle ledger → receipt
```

Every layer is connected. Most layers are a skeleton. Your job is to replace the skeleton in your layer without breaking the connections.

## Where your work starts

Roles are in [docs/TEAM.md](docs/TEAM.md). Every gap is marked `TODO(role N)` in code — search for it.

### Role 1 — Owner / Tech Lead (Vivek)

Works across every layer. Owns the integrity core outright, and moves into whichever
layer is blocked or behind — no part of this repo is out of scope.

**Owned outright — the integrity core:**
- `ledger/chain.py` and `ledger/signing.py` per [INTEGRITY.md](docs/INTEGRITY.md) §4–5
- Personal Ed25519 official signatures, block header, `prev_block_hash` chaining
- The custody code: packing, sealing, resolution ([CUSTODY.md](docs/CUSTODY.md) §1)
- Seed derivation from the custody code ([CUSTODY.md](docs/CUSTODY.md) §2)
- Key ceremony, three-tier split, time-lock

**Floats across everything else:**
- Architecture decisions and the tiebreak on any design disagreement
- Review on every PR; mandatory review on `ledger/` and `bank/`
- Picks up whichever layer is blocked — backend, frontend, ML, or infrastructure
- Keeps the interface contracts in [TEAM.md](docs/TEAM.md) honest as they shift
- Roadmap, cut lines, and external presentation

**Start here:** `backend/app/ledger/` — blocks are never sealed, leaves accumulate
but nothing is signed, and that is the largest hole in the project.

### Role 2 — AI / ML (Krishna)

> **🎯 Current goal — build M1 and M2.**
> The concept tagger and the difficulty predictor. Both are small encoder models that train in minutes on free Colab.
> 1. Hand-label a seed set of ~2,000 items (subject / chapter / concept / cognitive level)
> 2. **M1** — fine-tune DeBERTa-v3 or SciBERT with a multi-label head
> 3. **M2** — regression head on the same encoder, predicting IRT `b` and `a`
>
> M2 matters most: it estimates difficulty for a question that has never been administered, which is the gap past papers cannot fill. It is also what makes M3 controllable later — build the generator *after* this, not before.
>
> **Done when:** M1 tags a held-out year at usable accuracy, and M2's predicted difficulty correlates with known item difficulty on held-out data. Report the correlation honestly, including if it is weak.

**You build the models.** Four of them, in this order. See [AI_PIPELINE.md](docs/AI_PIPELINE.md) § Models.

| # | Model | Job | Approach |
|---|---|---|---|
| M1 | **Concept tagger** | question text → subject / chapter / concept / cognitive level | Fine-tuned encoder (DeBERTa or SciBERT), multi-label |
| M2 | **Difficulty predictor** | question text → IRT `b` and `a` | Regression head on the same encoder. **Solves the no-response-data gap.** |
| M3 | **Question generator** | concept + difficulty target → new NEET-style question | LoRA fine-tune of an open 7-8B model on parsed past papers |
| M4 | **Dedup embeddings** | detect near-duplicate items | Sentence embeddings + cosine threshold, powers exposure caps |

Order matters: M1 and M2 are small, quick, and immediately useful — and M2's output is what makes M3 controllable. Build the generator third, not first.

Supporting work that feeds them:
- Parse past papers into the item schema ([ARCHITECTURE.md](docs/ARCHITECTURE.md) §1) — this is your training set
- Validation gates on M3 output: NCERT grounding, answer uniqueness, syllabus scope
- TIF targeting with bounded retry in the generator ([AI_PIPELINE.md](docs/AI_PIPELINE.md) §6 step 8)
- Replace `eval` in `generator.py` with sympy

**Hard rule:** models run **offline during authoring**, never at exam time. Their output is frozen into the approved bank before T=0. An LLM call during generation would break determinism and void the audit guarantee.

- **Start here:** create `ml/`, then `backend/app/generation/generator.py`

### Role 3 — Backend

> **🎯 Current goal — rebranch, then Postgres and submit.**
>
> **First, unblock the merge.** The `Chaitanya-dev` branch has *unrelated git history* — it does not descend from `main`, so it cannot be merged and would revert the docs if forced. Fix before anything else:
> 1. Branch fresh from `main`
> 2. Port over the work that is yours: `exam/lifecycle.py`, `exam/response_chain.py`, `exam/session_store.py`, `db/schema.sql`, `core/keyrelease.py`, the routers
> 3. **Drop** the duplicated `ledger/` and `exam/seeds.py` — `main` already has them, tested, and with the privacy fix
> 4. Open a PR
>
> **Then build:**
> - Postgres schema with the append-only triggers already written (they are good — better than what `main` has)
> - `POST /exam/submit` with the response hash chain ([INTEGRITY.md](docs/INTEGRITY.md) §8)
> - Session lifecycle wired to real persistence
>
> **Done when:** the PR is merged and the frontend's submit button actually sends answers.

Everything is in memory and resets on reload.
- Postgres schema; ledger tables with `REVOKE UPDATE, DELETE`
- Session lifecycle: `registered → checked_in → paper_issued → in_progress → submitted → sealed`
- `POST /exam/submit` with the response hash chain ([INTEGRITY.md](docs/INTEGRITY.md) §8)
- Bank decryption from the ceremony key
- **Start here:** `backend/app/main.py`, `backend/app/exam/`

### Role 4 — Frontend

> **🎯 Current goal — make the exam client a real exam client.**
> - **Countdown timer** driven by server-signed time, not the browser clock. The client must not be able to give itself more time.
> - **Autosave** — answers survive a browser crash, a power cut, or a closed tab
> - **Kiosk mode** — no tab switching, no right-click, no dev tools, no copy
> - **Offline tolerance** — a service worker caches the issued paper so a network drop does not end someone's exam
>
> None of this depends on anyone else. Build it all against the existing typed contract in [api.ts](frontend/src/api.ts).
>
> **Done when:** you can kill the network mid-exam, crash the tab, reopen it, and the candidate carries on with their answers intact and the timer correct.

The exam client works but is not an exam client yet.
- Countdown timer with server-signed drift correction
- Autosave, offline tolerance (service worker), kiosk mode
- Invigilator console: check-in, live session health
- Ceremony UI for custodians
- **Start here:** `frontend/src/`, and `frontend/src/api.ts` is your contract with role 3

### Role 5 — QA / DevOps / Security

> **🎯 Current goal — CI first, then the security work from [CUSTODY.md](docs/CUSTODY.md).**
>
> **1. Cross-OS CI (do this first, it is small and protects everyone).**
> GitHub Actions running `pytest` on **Windows and Linux**. Determinism across OS is the project's central claim and nothing currently checks it. Add a golden-hash test pinning a known seed to a known paper hash.
>
> **2. Then the security layer around the custody framework:**
> - **Secret-redaction logging filter** — scrub `master_seed`, `custody_key`, `bank_master_key`, `answer_master_key` and every derived key from all log lines, tracebacks, and error responses. Real systems leak through logs far more often than through broken crypto.
> - **Leakage tests** — assert none of those values can appear in logs, API responses, or crash dumps
> - **Per-record key derivation** ([CUSTODY.md](docs/CUSTODY.md) §1.3) — a warrant for one student must unlock exactly one record, never the whole set
> - **Custody-resolve audit trail** — every deanonymisation writes a ledger event. Test that resolution is impossible without one being written.
> - **Append-only enforcement** — actually attempt `UPDATE` and `DELETE` on ledger tables and assert they fail *at the database level*
> - **Property-based Merkle tests** (Hypothesis) — arbitrary leaf counts, arbitrary tampering, proofs must never verify against a wrong root
> - **Zeroisation checks** — key material actually cleared from memory at seal
>
> **Done when:** CI is green on both OSes, and there is a failing test for every one of those security properties before it is implemented.

Not a support role. Two of the deliverables below — the verifier and reproducible builds — are load-bearing parts of the security argument, not testing chores. Five tracks:

#### T1 — CI and build integrity
- GitHub Actions: `pytest` on **Windows and Linux**. Determinism across OS is the project's central claim and nothing currently checks it.
- **Golden-hash test:** pin a known seed to a known paper hash as a committed constant. Catches silent generator drift across refactors.
- **Reproducible builds.** The block header commits `generator_source_hash` ([INTEGRITY.md](docs/INTEGRITY.md) §4) — if the deployed build cannot be reproduced from public source, verification is meaningless and a doctored build goes undetected. Pin every dependency, make the build byte-stable, publish the hash.
- Dependency scanning, SBOM, secret scanning. `.env` and key shares must be uncommittable.

#### T2 — The verifier
`scripts/verify_ledger.py`, spec in [INTEGRITY.md](docs/INTEGRITY.md) §11. Minimal dependencies, no import from the API. Re-derives every seed, regenerates every paper, rebuilds every Merkle root, checks every signature.

**This is the single most important deliverable in the project.** The public accountability argument collapses if nobody outside the team can run it. Treat it as a product, not a script: usable by a journalist or a court-appointed auditor.

#### T3 — Adversarial testing
- One test per row of [THREAT_MODEL.md](docs/THREAT_MODEL.md) — each should fail if the mitigation is removed
- **Append-only enforcement:** actually attempt `UPDATE` and `DELETE` on ledger tables and assert they fail *at the database level*. Docs claim this; nothing proves it.
- **Property-based testing** (Hypothesis) on the Merkle tree — arbitrary leaf counts, arbitrary tampering, proofs must never verify against a wrong root
- **Secret leakage:** assert `master_seed`, `session_pepper`, and the bank key never appear in logs, error messages, tracebacks, or API responses ([INTEGRITY.md](docs/INTEGRITY.md) §12)
- Zeroisation: verify key material is actually cleared at seal
- Red-team pass before any demo

#### T4 — Operations
- Docker Compose (backend + Postgres) for dev; the [Dockerfile](Dockerfile) already doubles as the offline centre-node image
- **Partition drill:** kill the network mid-exam, prove generation and delivery continue locally, then sync cleanly
- **Load test:** 10,000 concurrent candidates on one node; generation budget is <500 ms per paper
- Ledger backup, restore, and cross-centre replication testing
- **Exam-day runbook:** what an operator does when a node dies, a ceremony custodian is unreachable, or a candidate disputes their paper. Written before it's needed.
- Structured logging with an explicit secret-redaction list

#### T5 — Release and compliance
- Versioning, tagging, changelog
- **Pre-exam commitment publication:** bank version hash + generator hash published *before* T=0, and the process that proves the timestamp
- DPDP Act 2023 checklist — especially the erasure-vs-append-only conflict resolved in [INTEGRITY.md](docs/INTEGRITY.md) §7
- Exam client QA: browser matrix, accessibility, keyboard-only navigation

**Start here:** `.github/workflows/` (does not exist yet) — T1 first, it protects everyone else's work. Then T2.

## Rules that will get a PR rejected

- Storing an assembled paper anywhere
- Anything non-deterministic in `generation/` — caching, `random`, timestamps, parallelism
- `UPDATE` or `DELETE` against a ledger table
- Changing behaviour without updating the doc that describes it

## Workflow

```bash
git checkout -b yourname/what-youre-doing
# work, commit, push
git push -u origin yourname/what-youre-doing
# open a PR against main
```

`main` is protected. `backend/app/ledger/` and `backend/app/bank/` need the owner's review.
