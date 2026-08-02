# Architecture

## Design principle

Three phases, three different security postures:

| Phase | Duration | What exists | Security goal |
|---|---|---|---|
| **Pre-exam** | months | Encrypted bank, blueprint, code | Nothing decryptable exists |
| **Exam window** | ~3 hours | Bank unlocked, papers generated in memory | Nothing persists |
| **Post-exam** | forever | Hashes, seeds, signatures | Everything provable |

Most exam software has one posture for all three. That is the bug.

## Components

### 1. Item Bank (`backend/app/bank/`)

Versioned, immutable-per-version store of atomic questions and question *templates*.

```python
Item = {
  "id": "PHY-KIN-0142",
  "subject": "physics",
  "chapter": "kinematics",
  "concept_tags": ["projectile", "range"],
  "kind": "template" | "static",
  "body": "...",                    # Jinja source for templates
  "params": {...},                  # sampling ranges for template variables
  "solution": "...",                # symbolic; evaluated per instantiation
  "irt": {"a": 1.21, "b": -0.34, "c": 0.20},   # discrimination, difficulty, guessing
  "review": {"status": "approved", "by": "...", "at": "..."},
  "bank_version": "v1.4.2"
}
```

Stored as AES-256-GCM ciphertext. A bank version is content-addressed: `bank_version_hash = SHA-256(canonical_json(sorted(items)))`. That hash is published pre-exam so the bank cannot be swapped afterwards.

### 2. Key Release (`backend/app/core/keyrelease.py`)

The bank key `K` is split with Shamir's Secret Sharing into `n=5` shares, threshold `k=3`:

- 2 shares — exam authority (separate custodians)
- 2 shares — exam centre cluster (separate custodians)
- 1 share — independent observer (auditor / court-appointed)

At T=0 a quorum performs the unlock ceremony. It reconstructs `K` **in memory only**, derives the session `master_seed`, writes the genesis block, and zeroises `K` at the end of the exam window. Every ceremony emits a signed, ledgered event: who, when, which shares.

Consequence: the authority alone cannot open the bank. That is the point.

### 3. Seed Service (`backend/app/exam/seeds.py`)

```
master_seed  = CSPRNG(32 bytes)                 # generated inside the ceremony, never before
seed(cand)   = HKDF-SHA256(ikm=master_seed,
                           salt=session_id,
                           info="neti/paper/v1|" + candidate_id,
                           length=32)
```

Deterministic given `master_seed`, unpredictable without it. Publishing `master_seed` after the exam makes every paper reproducible by anyone, which is exactly what audit needs.

### 4. Generator (`backend/app/generation/`)

Pure function, no I/O, no clock, no network:

```
generate(seed, bank_version, blueprint) -> Paper
```

Pipeline: blueprint → constrained sampling → template instantiation → symbolic validation → option/order permutation → canonical serialisation. Detailed in [AI_PIPELINE.md](AI_PIPELINE.md).

Output lives in memory. It is serialised to the candidate's session and hashed. It is never written to disk or database.

### 5. Ledger (`backend/app/ledger/`)

The integrity core. Per exam session:

- Each paper → canonical JSON → SHA-256 → **leaf**
- Leaves batched (default 4096) → **Merkle tree** → root
- Blocks chained: `block_hash = SHA-256(prev_block_hash ‖ merkle_root ‖ header)`
- Each block signed Ed25519 by the session key; session key certified by the authority root key

Block header carries: session id, bank version hash, generator source hash, blueprint hash, leaf count, timestamp range. Full spec in [INTEGRITY.md](INTEGRITY.md).

### 6. Exam Delivery (`backend/app/exam/`)

Session lifecycle: `registered → checked_in → paper_issued → in_progress → submitted → sealed`.

Responses are hashed and chained per candidate; at submit the candidate receives a **receipt**: their paper hash, response hash, and a Merkle inclusion proof, signed. That receipt is checkable years later, offline, against the published root — which is how a candidate proves what they actually sat.

### 7. Frontend (`frontend/`)

Two apps behind one build:

- **Exam client** — kiosk-mode React, offline-tolerant (service worker caches the issued paper), autosave, timer authority server-side with signed drift correction.
- **Console** — invigilator check-in, ceremony UI, live session health, post-exam publishing and audit views.

### 8. Verifier (`scripts/verify_ledger.py`)

Deliberately standalone — no dependency on the API, minimal imports. Given a published session bundle (roots, signatures, revealed `master_seed`, bank version, generator hash) it re-derives every seed, regenerates every paper, recomputes every leaf, rebuilds the tree, and checks the signatures. Anyone can run it. That is the accountability mechanism.

## Data flow

```
 PRE-EXAM
   authors ──> items ──> IRT calibration ──> bank vN ──> AES-GCM encrypt ──> distribute
                                                │
                                    publish bank_version_hash + generator_hash (commitment)

 T = 0
   k-of-n custodians ──> unlock ceremony ──> K (memory) + master_seed ──> genesis block

 EXAM
   candidate check-in ──> seed = HKDF(master_seed, candidate_id)
                              │
                       generate(seed, bank, blueprint)
                              │
                    ┌─────────┴──────────┐
              deliver to client     SHA-256 leaf ──> Merkle batch ──> signed block
                              │
                          responses ──> per-candidate hash chain
                              │
                          submit ──> signed receipt + inclusion proof to candidate

 POST-EXAM
   seal ──> reveal master_seed ──> publish bundle ──> anyone runs verify_ledger.py
```

## Deployment

Exam centres must work with unreliable connectivity, so:

- Each centre runs a **local node**: API + Postgres + pre-staged encrypted bank shard.
- Generation and delivery are fully local. No round trip to a national server to start an exam.
- Ledger blocks replicate to the national ledger opportunistically; blocks are self-authenticating (signed, chained), so replication order and delay don't matter.
- Centres cross-anchor: each centre's daily root is included in the national block, so a centre cannot fork its own history unnoticed.

## Key decisions & rejected alternatives

| Decision | Chosen | Rejected | Reason |
|---|---|---|---|
| Integrity substrate | Hash chain + Merkle + Ed25519 | Public blockchain | No trust benefit here that signing + publication doesn't give; adds cost, latency, and an internet dependency an exam hall can't guarantee |
| Anchoring | Publish roots to press/RTI/mirrors; optional testnet anchor | Mandatory on-chain | Keeps the offline path viable; anchoring is an enhancement, not a dependency |
| Generation | Templates + validated LLM variants | End-to-end fine-tuned LLM | Generated answers must be provably correct; a fine-tuned model gives no such guarantee |
| Storage of papers | Hash only | Encrypted paper store | A stored paper is a leakable paper. Regeneration from seed replaces retrieval. |
| Key custody | Shamir k-of-n | HSM held by authority | Defends against A7 (the authority itself), which an authority-held HSM does not |
