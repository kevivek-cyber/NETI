# NETI — Non-Exploitable Test Integrity

> A question paper that cannot leak, because it does not exist until the exam starts.

## The problem

The 2024 NEET-UG leak compromised an exam sat by 2.4 million students. The failure was not cryptographic — it was physical. A single paper is authored months in advance, printed, transported, and stored in vaults at thousands of locations. Every step is a person with access. Investigations traced leaks to exactly these seams: transit and storage, days before the exam.

You cannot encrypt your way out of a printed page in a truck.

## The approach

NETI eliminates the leakable artifact.

1. **No paper exists before T=0.** Items live in an encrypted, versioned bank. The decryption key is split k-of-n (Shamir) across the exam authority, the centre, and an independent observer. No single party can open the bank early — not even the authority.
2. **Every candidate gets a different paper**, assembled on the spot by a deterministic generator from a per-candidate seed derived at exam start. Stealing one paper tells you nothing about the next.
3. **Every paper is psychometrically equated.** Item Response Theory calibration keeps every generated paper within a tight difficulty band, so "different" never means "unfair."
4. **Everything is provable afterwards.** Each paper is hashed into a Merkle tree; roots are chained and signed. Post-exam, seeds are revealed and *anyone* can re-run the open-source generator and confirm the ledger. A substituted or softened paper is mathematically visible.

That last property is the "bitcoin-grade" part — not a cryptocurrency, but the thing that actually made Bitcoin work: an append-only, hash-linked, publicly verifiable record that no insider can rewrite.

## What's in the box

| Component | What it does |
|---|---|
| **Item bank** | Encrypted, versioned store of IRT-calibrated questions parsed from past papers and authored fresh |
| **Generator** | Deterministic, seeded assembly of a blueprint-conformant 180-question paper |
| **Ledger** | SHA-256 Merkle tree + Ed25519-signed hash chain, append-only |
| **Exam client** | React app: secure delivery, offline-tolerant, per-candidate |
| **Verifier** | Standalone CLI anyone can run to audit a past exam |

## Quick start

```bash
git clone <repo> && cd NETI
cp .env.example .env

docker compose up -d              # postgres + api
cd backend && pip install -r requirements.txt
pytest                            # ledger + determinism tests must pass

uvicorn app.main:app --reload     # http://localhost:8000/docs
cd ../frontend && npm install && npm run dev
```

Verify a completed exam session end-to-end:

```bash
python scripts/verify_ledger.py --session 2026-NEET-UG --bank-version v1.4.2
```

## Documentation

| Doc | Read it when |
|---|---|
| [CLAUDE.md](CLAUDE.md) | First. Project context and hard invariants. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | You need the component and data-flow picture |
| [docs/INTEGRITY.md](docs/INTEGRITY.md) | You're touching hashing, Merkle, signing, or key release |
| [docs/AI_PIPELINE.md](docs/AI_PIPELINE.md) | You're working on question generation or equating |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | You're proposing a security change, or challenging one |
| [docs/TEAM.md](docs/TEAM.md) | You need to know who owns what |
| [docs/ROADMAP.md](docs/ROADMAP.md) | You want to know what's real vs. planned |

## Status & scope

Academic capstone project, 5-person team. This demonstrates a *mechanism* — it is not certified for, or deployed on, any live examination. Claims in these docs about NEET refer to publicly reported facts about the 2024 leak; the design response is ours.

## License

TBD — see [docs/TEAM.md](docs/TEAM.md) § Governance.
