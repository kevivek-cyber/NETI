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

### Role 1 — Owner / Integrity (Vivek)
Blocks are never sealed. Leaves accumulate but nothing is signed.
- Implement `ledger/chain.py` and `ledger/signing.py` per [INTEGRITY.md](docs/INTEGRITY.md) §4–5
- Ed25519 session key, block header, `prev_block_hash` chaining
- Sign the receipt
- **Start here:** `backend/app/ledger/`, read INTEGRITY.md §4 first

### Role 2 — AI / ML (Krishna)
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
Everything is in memory and resets on reload.
- Postgres schema; ledger tables with `REVOKE UPDATE, DELETE`
- Session lifecycle: `registered → checked_in → paper_issued → in_progress → submitted → sealed`
- `POST /exam/submit` with the response hash chain ([INTEGRITY.md](docs/INTEGRITY.md) §8)
- Bank decryption from the ceremony key
- **Start here:** `backend/app/main.py`, `backend/app/exam/`

### Role 4 — Frontend
The exam client works but is not an exam client yet.
- Countdown timer with server-signed drift correction
- Autosave, offline tolerance (service worker), kiosk mode
- Invigilator console: check-in, live session health
- Ceremony UI for custodians
- **Start here:** `frontend/src/`, and `frontend/src/api.ts` is your contract with role 3

### Role 5 — QA / DevOps / Security
- CI: run `pytest` on Windows **and** Linux — determinism must hold across both
- Golden-hash test pinning a known seed to a known paper hash
- Docker Compose for backend + Postgres
- Work through [THREAT_MODEL.md](docs/THREAT_MODEL.md) row by row and write a test per row
- **Start here:** `.github/workflows/` (does not exist yet), `backend/tests/`

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
