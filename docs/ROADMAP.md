# Roadmap

Six phases. Each ends with something that **runs and can be demoed** — no phase completes on a design document alone.

Status legend: ☐ not started · ◐ in progress · ☑ done

---

## Phase 0 — Foundations ◐

Shared understanding and a repo everyone can work in.

- ☑ Threat model, architecture, integrity spec, AI pipeline spec
- ☑ Team roles and interface contracts
- ☐ Repo scaffolding: backend/frontend/ml skeletons, Docker Compose, CI
- ☐ Interface contracts frozen (item schema, `generate()` signature, canonical form)
- ☐ Past-paper corpus collected — 10 years of NEET-UG papers + answer keys

**Exit:** every member can clone, run, and pass an empty test suite. Everyone has read the threat model.

---

## Infrastructure gaps found in review ☐ *(owner + QA/DevOps)*

Not new feature work — four places where CI structurally cannot catch a
real class of bug that already happened once. Found while reviewing the
Aug 2026 round of PRs (roster-hash gap in `Chain.verify()`, a
non-constant-time comparison in `response_chain.py`, `leaf_index` never
persisted, and `frontend/src/api/api.ts` calling four endpoints that don't
exist on the backend). Each bug maps to one gap below; fixing the gap is
what stops the *next* one, not just this one.

- ☐ **CI never builds or typechecks the frontend.** `.github/workflows/ci.yml`
  runs `pytest backend/tests` and `pytest ml/tests` only — no `npm run
  build`, no `tsc`. A PR that breaks the frontend, or that drifts from the
  backend contract, shows green. *Plan:* add a `frontend` job (single OS —
  no determinism claim depends on frontend cross-OS behaviour): checkout →
  `actions/setup-node` → `npm ci` → `npm run build` (already runs `tsc -b
  && vite build`). *Owner:* role 5 (Varsharani, owns cross-OS/general CI
  per [TEAM.md](TEAM.md)). *Exit:* a PR that fails to typecheck or build
  the frontend fails CI.

- ☐ **No contract check between `api.ts` and the FastAPI routes.**
  [TEAM.md](TEAM.md) already specifies the fix — *"REST API surface:
  OpenAPI schema, generated from FastAPI"* — it was never implemented, so
  `api.ts` was hand-written by role 4 and drifted from what role 3 actually
  built (`/session/open`, `/exam/paper`, `/ledger/receipt/:id`,
  `/ledger/root` were called; none exist). *Plan, in order of effort:*
  (1) short term — a CI step that dumps `app.openapi()["paths"]` from
  `app.main:app` and asserts every path string `api.ts` calls appears in
  it, failing the build on drift; (2) proper fix — generate `api.ts`'s
  request/response types from `/openapi.json` (`openapi-typescript` or
  equivalent) so a removed/renamed backend route is a compile error, not a
  runtime 404. *Owner:* role 3 (backend) proposes the generation step,
  role 4 (Sakshi) adopts it in `api.ts`. *Exit:* deleting or renaming a
  FastAPI route breaks the frontend build, not a demo.

- ☐ **DB-touching code is untestable in CI.** `session_store.py` and the
  leaf-index logic in `exam_router.py` need a live Postgres connection;
  CI has no database service, so this whole layer — including exactly the
  code that had the `leaf_index` persistence bug and the in-memory/DB
  divergence — has zero automated coverage. `test_exam_delivery.py`'s own
  docstring already named this failure shape once for router imports
  (*"a test suite that never loads the code under test is not evidence of
  anything"*); it wasn't extended to the database layer. *Plan:* add a
  `postgres:15` service container to the CI job (Linux runner only — GitHub
  Actions service containers aren't available on `windows-latest`, so this
  job runs on ubuntu-latest alongside, not inside, the cross-OS matrix),
  point `DATABASE_URL` at it, apply `schema.sql` as a setup step, and write
  real tests for `CandidateSession` save/load round-trips and the
  issue-paper → submit leaf flow. *Owner:* role 5 + role 3. *Exit:* the
  `leaf_index` COALESCE behaviour and the DB-sourced Merkle leaf list both
  have a passing test that would have failed against the pre-fix code.

- ☐ **INTEGRITY.md §12's constant-time-comparison rule has no automated
  check.** It's written down and was still violated once
  (`response_chain.py` used bare `==` on a client-supplied digest).
  *Plan:* a small AST-based pytest "meta-test" (no new dependency) that
  walks `backend/app/ledger/` and `backend/app/exam/` for `==`/`!=`
  comparisons where either operand's name contains `hash`, `digest`,
  `signature`, or `_hex`, outside a call to `hmac.compare_digest`, and
  fails listing the file/line. *Owner:* role 1 (owns INTEGRITY.md) with
  role 5 wiring it into CI. *Exit:* reintroducing a bare `==` on a hash
  fails CI at the PR that introduces it, not at the next manual review.

---

## Next up, per person (from the Aug 2026 review)

Grounded in the `TODO(role N)` comments already in the code, not a
restatement of the phase lists above. Cross-reference those phases for
the full scope; this is specifically what's next.

**Vivek (role 1 — owner):**
- `backend/app/ledger/canonical.py:61` — swap the JCS approximation for a
  real RFC 8785 implementation before any exam needing cross-language
  verification; the current shortcut only works because floats are banned.
- `backend/app/api/exam_router.py:147` — leaf-index assignment races: two
  candidates issued at the same instant can both read the same
  `MAX(leaf_index)` before either writes. Needs a per-session advisory
  lock or `SELECT ... FOR UPDATE`.
- `backend/app/db/schema.sql` — the `REVOKE UPDATE, DELETE ... FROM
  PUBLIC` line is commented out. Append-only is currently enforced by
  triggers alone, not "at the DB grant level" as the CLAUDE.md invariant
  requires. Uncomment and apply once an app role exists.
- Own the constant-time-comparison lint definition (infra gaps, above);
  Varsharani wires it into CI.
- Review this branch's ledger changes, especially `chain.py`'s `verify()`
  — integrity-core territory per TEAM.md's ownership rule.

**Krishna (role 2 — AI/ML):**
- `backend/app/generation/generator.py:15-19` — IRT difficulty targeting,
  chapter weightage, cognitive-level mix, exposure caps, and
  hall-collision constraints are all unwired. M1/M2 exist and train in
  `ml/`, but the generation walking-skeleton never calls them.
- `backend/app/generation/generator.py:37` — bigger one: `validators/
  symbolic.py` (SymPy) already exists per `ml/README.md`, but `generator.py`
  still runs answer expressions through raw `eval()`. Wiring in the
  existing validator is integration work, not new modeling.
- Real response data for IRT calibration — `ml/dataset/synthetic.py`
  generates synthetic 3PL matrices only; ROADMAP's risk table already
  flags this (expert priors + a volunteer pilot administration).
- Phase 2/3: PDF→item extraction from real past papers, dedup across
  years, ~200 Physics/Chemistry templates (currently just the `DEMO`
  stub in `blueprint.py`).

**Backend Engineer (role 3):**
- `backend/app/generation/generator.py:52` — `load_bank()` reads
  `sample_bank.json` off disk in plaintext. `backend/app/bank/` is just
  that file plus an empty `__init__.py` — there is no bank encryption at
  all yet, against a named non-negotiable invariant (CLAUDE.md: "item
  bank encrypted at rest, key split k-of-n"). Likely the largest gap
  against the project's own stated invariants right now.
- Scoring + post-hoc IRT equating (Phase 4, unbuilt).
- Pair with Krishna on wiring `validators/symbolic.py` into
  `generator.py` — TODO is tagged role 2 but the integration point is
  this module.
- Emit the OpenAPI schema half of the frontend contract-check fix
  (infra gaps, above) — FastAPI generates it for free at `/openapi.json`.

**Sakshi (role 4 — frontend):**
- Wire the real `api.submitExam` now that `api.ts` matches the backend.
  Needs `ExamClient` to track a timestamped event log per answer change
  (currently only a final-state snapshot survives) — see the TODO block
  at the bottom of `frontend/src/api/api.ts`.
- Client-side response-chain hashing (WebCrypto). CUSTODY.md §6.3
  already specifies this architecture for the standalone receipt
  verifier; the same routine covers the submit-time digest. Needs to
  match `canonical.py`'s serialization byte-for-byte — do this with
  Vivek, not solo, per the "no invented crypto" rule.
- Invigilator console and ceremony UI — both in Phase 4, both
  nonexistent.
- Adopt the generated OpenAPI types once role 3 ships them, so `api.ts`
  stops being hand-maintained and able to drift again.

**Varsharani (role 5 — QA/DevOps/Security):**
- All four infra-gap items above (frontend CI job, Postgres service
  container + DB tests, the contract-check, the constant-time lint).
- `backend/tests/test_determinism.py:7` — already tagged to you: confirm
  the determinism suite specifically runs on both OS legs of the CI
  matrix (not just the general test step), and add a golden-hash
  fixture so a determinism break shows as a diff, not a vague failure.
- `scripts/verify_ledger.py` — the standalone verifier TEAM.md names as
  *"load-bearing... not a testing chore."* The `scripts/` directory
  doesn't exist yet. Arguably the most overdue item against this role's
  own description.
- Phase 6 (load test, partition drill, red-team pass) is correctly last
  — nothing to start until Phase 4 exists.

---

## Phase 1 — Integrity core ☐ *(owner)*

Built first, deliberately. It's the load-bearing claim and it's testable without any of the rest.

- ☐ Canonicalisation (RFC 8785) + domain-separated hashing
- ☐ Merkle tree with node promotion, inclusion proofs, proof verification
- ☐ Hash-chained blocks, Ed25519 signing, key hierarchy
- ☐ Shamir k-of-n split and the unlock ceremony flow
- ☐ HKDF seed derivation
- ☐ Append-only enforcement at the DB grant level
- ☐ `scripts/verify_ledger.py` — standalone, minimal deps

**Exit:** ledger of 100k synthetic leaves builds, signs, and verifies; tampering with any leaf is caught; a candidate receipt verifies offline. Second-preimage and node-promotion cases have tests.

---

## Phase 2 — Item bank ☐ *(ML + backend)*

- ☐ PDF → structured item extraction from past papers
- ☐ Tagging: subject / chapter / concept / cognitive level / NCERT ref
- ☐ Deduplication across years
- ☐ Item schema, Postgres storage, versioning with content-addressed `bank_version_hash`
- ☐ AES-256-GCM encryption at rest
- ☐ Seed bank: target ~2,000 reviewed items across four subjects

**Exit:** an encrypted, versioned bank of 2,000 tagged items; unlock via a 3-of-5 ceremony; version hash reproducible.

---

## Phase 3 — Generation ☐ *(ML + owner)*

- ☐ Blueprint config (180 Q / 720 marks / chapter weightage / cognitive mix)
- ☐ Template format + Jinja instantiation + symbolic solution evaluation
- ☐ ~200 templates for Physics and Physical Chemistry numericals
- ☐ Misconception-based distractor generation
- ☐ Constrained seeded sampler (exposure caps, hall-collision cap, concept spread)
- ☐ Symbolic validator — every instance's answer recomputed
- ☐ IRT calibration on available response data; TIF targeting with bounded retry
- ☐ **Determinism test: same seed → identical paper, across processes and machines**

**Exit:** `generate(seed, bank, blueprint)` produces a valid 180-question paper in < 500 ms, deterministically. 100 generated papers reviewed by a subject expert with > 99% factual accuracy.

---

## Phase 4 — Exam delivery ☐ *(backend + frontend)*

- ☐ Session lifecycle: registered → checked_in → paper_issued → in_progress → submitted → sealed
- ☐ Paper delivery, in memory only — nothing persisted
- ☐ React exam client: kiosk mode, timer, navigation, autosave, offline tolerance
- ☐ Per-candidate response hash chain
- ☐ Signed receipt with inclusion proof at submit
- ☐ Invigilator console: check-in, live session health
- ☐ Ceremony UI for custodians
- ☐ Scoring + post-hoc IRT equating

**Exit:** a full mock exam runs end-to-end for 50 simulated candidates, each with a unique paper, every paper in the ledger, every receipt verifying.

---

## Phase 5 — LLM variant pipeline ☐ *(ML)*

Deliberately last. The system must already work without it; this scales the bank, it doesn't carry the guarantee.

- ☐ Variant generation for assertion-reason, matching, conceptual Biology
- ☐ NCERT retrieval grounding + citation check
- ☐ Automated gates: answer uniqueness, syllabus scope, difficulty band, language
- ☐ Human review workflow — approval queue, no bypass
- ☐ Rejection corpus retained as signal

**Exit:** 500 LLM-generated variants through the full gate; expert audit confirms > 99.5% accuracy on approved items; zero unreviewed items reachable in a live pool.

---

## Phase 6 — Scale, hardening, publication ☐ *(QA/DevOps + all)*

- ☐ Load test: 10,000 concurrent candidates on a centre node
- ☐ Offline centre-node deployment; network-partition drill mid-exam
- ☐ Cross-centre root anchoring
- ☐ Red-team pass against every row in [THREAT_MODEL.md](THREAT_MODEL.md)
- ☐ Public session bundle format + mirror publication
- ☐ Independent verification: someone outside the team runs the verifier and reproduces a full session
- ☐ Paper / capstone writeup, demo video

**Exit:** an outsider reproduces a complete exam session from the published bundle alone.

---

## Critical path

```
Phase 0 ──> Phase 1 (integrity) ──┬──> Phase 3 (generation) ──> Phase 4 (delivery) ──> Phase 6
            Phase 2 (bank) ───────┘                             Phase 5 (LLM) ──────────┘
```

Phases 2 and 3 can overlap once the item schema is frozen. Phase 5 is parallel to Phase 4 and is the first thing to cut if time runs short — the system is complete and defensible without it.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Past-paper corpus is hard to obtain cleanly | Blocks Phase 2 | Start collection in Phase 0; NCERT-derived authoring as fallback |
| No real response data for IRT calibration | Weakens equating claim | Expert priors + a pilot administration with volunteer students |
| Templatisation doesn't cover Biology | Bank too small for exposure targets | Lean on bank breadth + Phase 5; report exposure honestly |
| Determinism breaks across environments | Voids the entire audit story | Pin Python/lib versions; determinism test in CI on two OS images |
| Team bandwidth (5 students, coursework) | Phases slip | Phase 5 and cross-centre anchoring are the declared cut lines |

## Cut lines

If time runs out, drop in this order — the core claim survives all of them: LLM variants (Phase 5) → cross-centre anchoring → offline tolerance → invigilator console polish.

**Never cut:** determinism tests, symbolic validation, append-only enforcement, the standalone verifier. Those four *are* the project.
