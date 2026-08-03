# Team

Five people. The split follows the architecture: each person owns a layer end-to-end (design → code → tests → docs) so nobody is blocked waiting on someone else's half-finished module.

## Roles

| # | Role | Owns | Primary docs |
|---|---|---|---|
| **1** | **Owner / Tech Lead — Vivek** (`kevivek-cyber`) | Integrity layer: Merkle, hash chain, signing, key ceremony, seed derivation. Architecture decisions, PR review, roadmap, external presentation. | [INTEGRITY.md](INTEGRITY.md), [ARCHITECTURE.md](ARCHITECTURE.md) |
| **2** | **AI / ML Engineer — Krishna** (`me13krishna`) | Past-paper ingestion, item tagging, IRT calibration, templatisation, LLM variant pipeline and its validators. | [AI_PIPELINE.md](AI_PIPELINE.md) |
| **3** | **Backend Engineer** | FastAPI services, Postgres schema, item bank storage and encryption, exam session lifecycle, scoring. | [ARCHITECTURE.md](ARCHITECTURE.md) §1, §6 |
| **4** | **Frontend Engineer — Sakshi** (`Sakshi-Pathare`) | Student exam client (kiosk, offline-tolerant), invigilator console, ceremony UI, receipt/verification views. | [ARCHITECTURE.md](ARCHITECTURE.md) §7 |
| **5** | **QA / DevOps / Security** | CI, Docker, centre-node deployment, the standalone verifier, threat-model testing, determinism test suite. | [THREAT_MODEL.md](THREAT_MODEL.md) |

Roles 2–5 are unassigned in this doc — fill in names as the team forms, and keep this table as the single source of truth for "who do I ask."

## Interfaces between roles

The contracts that let people work in parallel. Agree these in week 1 and change them only by PR:

| Boundary | Contract | Between |
|---|---|---|
| Item schema | The `Item` JSON shape in [ARCHITECTURE.md](ARCHITECTURE.md) §1 | 2 ↔ 3 |
| `generate(seed, bank_version, blueprint) → Paper` | Pure, deterministic, no I/O | 1 ↔ 2 |
| Paper canonical form | RFC 8785 JCS; the exact bytes that get hashed | 1 ↔ 2 ↔ 3 |
| REST API surface | OpenAPI schema, generated from FastAPI | 3 ↔ 4 |
| Session bundle format | What the verifier consumes | 1 ↔ 5 |

If two people need to change a contract, that's a conversation before it's a commit.

## Ownership rules

- **Anything under the integrity layer or bank encryption requires the owner's review.** Not gatekeeping — a subtle hashing mistake silently voids the entire guarantee, and it won't fail a test.
- Everything else: one reviewer from any other role. Cross-role review is how the team stays able to cover for each other.
- The owner has the tiebreak on architecture. Disagreement gets recorded as a rejected-alternative row in [ARCHITECTURE.md](ARCHITECTURE.md), not lost in chat.

## Workflow

- **Branches:** `<name>/<short-feature>`. `main` is protected — no direct pushes.
- **PRs:** small, one concern each. Description states which threat-model row or roadmap item it moves.
- **Definition of done:** code + tests + docs updated + PR reviewed. A PR that changes behaviour without touching `docs/` is incomplete.
- **Cadence:** weekly sync — each person gives blockers and what changed at the interfaces. Async otherwise.
- **Demo discipline:** every phase in [ROADMAP.md](ROADMAP.md) ends with something runnable. No phase is "done" as a design document.

## Governance

- **Repository owner:** Vivek. Controls `main`, releases, and merge rights.
- **Licence:** to be decided before any public push. The verifier must be open source — the entire accountability argument collapses if the public cannot run it. Recommendation: Apache-2.0 for the whole repo (patent grant matters if this is ever pitched to an examination body).
- **Attribution:** every contributor listed in the README at first release. Academic submissions name the full team regardless of who wrote which module.
- **External claims:** nobody publicly claims this is deployed, certified, or endorsed by NTA or any examination body. It is a student capstone demonstrating a mechanism. Overclaiming is the fastest way to discredit genuinely good work.
