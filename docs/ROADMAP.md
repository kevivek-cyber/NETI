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
