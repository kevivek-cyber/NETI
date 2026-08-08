# Getting started

Read [AGENTS.md](AGENTS.md) first — especially the invariants. Then get it running, then find your role below.

## Run it

Two terminals.

```bash
# terminal 1 — backend
cd backend
pip install -r requirements.txt
pytest                              # 41 tests must pass
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

> **🎯 Current goal — sign the blocks.**
> Leaves accumulate and nothing is ever sealed. Hashes prove nothing changed;
> they do not prove who wrote the record, so the authority could discard the
> ledger and publish a fabricated one that verifies perfectly.
>
> 1. `ledger/chain.py` — block header, `prev_block_hash` chaining, genesis block
>    written at ceremony time committing bank version, generator hash and blueprint
> 2. `ledger/signing.py` — Ed25519, signed by the three officials personally rather
>    than by one institutional key ([CUSTODY.md](docs/CUSTODY.md) §4)
> 3. Sign the receipt so a candidate's proof is verifiable offline
>
> **Done when:** a block with fewer than three valid signatures is rejected, and
> the chain verifies from genesis.

**Start here:** `backend/app/ledger/`.

### Role 2 — AI / ML (Krishna)

> **🎯 Current goal — retrain M1 on real labels.**
> ✅ Done: M1 tagger, M2 difficulty, 3PL IRT, symbolic validator, bank tools — the whole pipeline runs.
>
> **The gap:** every model is trained on `curated_mock.py`, which writes the questions *and* their labels from a formula whose terms are also model features. `m2_metrics.json` now says so explicitly. The scores measure formula recovery, not prediction.
>
> 1. **M1 on real data — do this first, it is a download.** `openlifescienceai/medmcqa` on HuggingFace: 182,822 real AIIMS/NEET-PG questions with human-assigned subject and topic labels. Retrain and report the number against a majority-class floor. Expect roughly 70% on 20 subjects.
> 2. **M2 needs data that must be collected.** No public dataset pairs NEET question text with measured difficulty. Two routes: a pilot (300 questions, 100 volunteers, fit IRT to real responses), or LLM-simulated students — have a model attempt each item repeatedly and fit IRT to the failures. The second is a current research method and works on the questions you already have.
> 3. Then M3 (generator) and M4 (dedup embeddings).
>
> **Done when:** at least one model reports a score against labels it did not generate. A correlation of 0.5 on real data beats 0.93 on generated data.


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

- **Start here:** `ml/dataset/` — swap the mock source for a real one.

### Role 3 — Backend

> **🎯 Current goal — encrypt the bank.**
> ✅ Done: Postgres schema with append-only triggers, Shamir ceremony, session lifecycle, response chain, exam endpoints. Merged and green.
>
> **The gap is your own TODO:** `load_bank()` still reads plaintext JSON. The ceremony reconstructs `bank_key` correctly and then nothing uses it.
>
> 1. **Per-item AES-256-GCM** — `item_key = HKDF(bank_master_key, "neti/item/v1|" + item_id)`, per [CUSTODY.md](docs/CUSTODY.md) §3.1. Per-item rather than one blob so a compromised centre node exposes the items it served, not the whole bank.
> 2. **Answers under a separate key** released at window close, so a mid-exam compromise leaks questions but not answers.
> 3. **Scoring** — +4 / −1 / 0, computed after the window from regenerated papers.
>
> **Done when:** the bank on disk is ciphertext, and paper generation fails cleanly without a completed ceremony.


Full scope: FastAPI services, Postgres schema, item bank storage and
encryption, exam session lifecycle, scoring.

### Role 4 — Frontend

> **🎯 Current goal — the client is broken. Fix the contract first.**
> The backend was rewritten and the endpoints all changed. `api.ts` calls routes that no longer exist:
>
> | api.ts calls | backend now serves |
> |---|---|
> | `/api/session/open` | `/api/ceremony/unlock` |
> | `/api/exam/paper` | `/api/exam/check-in` then `/api/exam/issue-paper` |
> | `/api/ledger/root`, `/api/ledger/receipt/{i}` | gone — the receipt comes back from `/api/exam/submit` |
>
> Nothing in the UI works end to end right now.
>
> 1. **Rewrite `api.ts`** against the real routes. Check-in is now a separate step before a paper is issued.
> 2. **Wire submit properly** — it must send the answer events and the response-chain digest, then render the receipt the server returns.
> 3. Then the original goal: **timer** (server-signed, not the browser clock), **autosave**, **kiosk mode**, **offline tolerance**.
>
> **Done when:** check-in → paper → answer → submit → receipt works in a browser against the live backend.


The exam client works but is not an exam client yet.
- Countdown timer with server-signed drift correction
- Autosave, offline tolerance (service worker), kiosk mode
- Invigilator console: check-in, live session health
- Ceremony UI for custodians
- **Start here:** `frontend/src/`, and `frontend/src/api.ts` is your contract with role 3

### Role 5 — QA / DevOps / Security

> **🎯 Current goal — the security tests.**
> ✅ Done: cross-OS CI on Ubuntu and Windows. It caught nothing yet because it was only added this week — that is the point of it.
>
> Now the part of your role that is a deliverable rather than a chore:
>
> 1. **Secret-redaction logging filter** — scrub `master_seed`, `session_pepper`, `bank_key` from every log line, traceback and error response. Real systems leak through logs far more often than through broken crypto.
> 2. **Leakage tests** — force a crash mid-generation, send garbage to the API, and assert no key material appears anywhere in the output.
> 3. **Append-only enforcement** — actually run `UPDATE` and `DELETE` against `ledger_blocks` and assert the database rejects them. The triggers exist in `schema.sql`; nothing proves they work.
> 4. **Property-based Merkle tests** (Hypothesis) — arbitrary leaf counts, arbitrary tampering, proofs must never verify against a wrong root.
> 5. **Golden-hash test** — pin a known seed to a known paper hash so a refactor cannot silently change generator output.
>
> **Done when:** each of those is a test that fails if the property is removed.


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
