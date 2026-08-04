# Custody & Accountability Framework

Supersedes [INTEGRITY.md](INTEGRITY.md) §6 (key custody) and §7 (seed derivation).

## The principle

Every past exam-leak inquiry has ended at "the authority is responsible." That answer has never convicted anyone. This framework is built so the answer is always **five named people**.

Two ideas do the work:

1. **A custody code** binds every paper to the five humans present when it was issued — the student, their attendant, and the three officials above them. It is public, meaningless without a key, and reversible to their exact identities under warrant.
2. **The paper is generated *from* that code.** No custody group, no code. No code, no seed. No seed, no paper. Accountability stops being a rule someone can skip and becomes a physical precondition.

---

## 1. The custody code

### 1.1 Packing

Each identity has a fixed bit width, so the five pack into exactly one 128-bit block — one AES block, no padding.

| Field | Bits | Range | Position |
|---|---|---|---|
| `version` | 4 | 0–15 | 124–127 |
| `centre_id` | 12 | 4,096 centres | 112–123 |
| `student_id` | 32 | 4.3 billion | 80–111 |
| `attendant_id` | 24 | 16 million | 56–79 |
| `official_1` | 20 | 1 million | 36–55 |
| `official_2` | 20 | 1 million | 16–35 |
| `official_3` | 16 | 65,536 | 0–15 |
| **Total** | **128** | | |

The `version` field exists so field widths can change in future cycles without making historical records unparseable. Never remove it.

```
packed = (version << 124) | (centre << 112) | (student << 80)
       | (attendant << 56) | (o1 << 36) | (o2 << 16) | o3
```

### 1.2 Sealing

```
custody_code = AES-256(custody_key, packed)      # 16 bytes in, 16 bytes out
```

- **Public.** Written to the ledger and bound into the paper.
- **Opaque without the key.** Reveals nothing about who.
- **Deterministic.** The same five people always produce the same code — required, or it cannot be looked up.

**On ECB mode.** Single-block, unique-input, determinism-required. ECB's usual weakness — identical plaintext blocks producing identical ciphertext — cannot apply to a single block with no repeats. This is one of the narrow cases where ECB is correct. Say so in a code comment; every reviewer will flinch at it otherwise.

### 1.3 Resolution

```
unpack(AES-256-decrypt(custody_key, custody_code)) → all five identities
```

**Three controls on that key:**

| Control | Mechanism |
|---|---|
| No unilateral use | `custody_key` split across judiciary, exam authority, independent auditor |
| Narrow scope | Per-record derivation: `record_key(i) = HKDF(custody_master, leaf_index_i)`. A warrant for one student unlocks exactly one record. |
| No secret lookups | Every resolution writes a `custody_resolve` event to the append-only ledger — leaf index, warrant reference, who, when |

The third is the cheapest and the most important. Misuse of the custody key becomes permanent public record, and most surveillance abuse depends on being invisible.

### 1.4 The student's share

`student_id` alone is not enough — roll numbers are printed, sequential, and public. The student contributes a **sealed scratch-off code on the admit card**, revealed at the desk.

Chosen over the alternatives because it is genuinely the student's, cannot be used before exam morning, works fully offline, and has an obvious recovery path when damaged.

---

## 2. Generation binds to custody

```
custody_code = AES-256(custody_key, pack(...))
seed         = HKDF-SHA256(ikm=master_seed, salt=session_id,
                           info=b"neti/paper/v1|" + custody_code)
paper        = generate(seed, bank, blueprint)
leaf         = SHA-256(0x00 ‖ canonical(paper))
```

The ledger stores `leaf` and `custody_code`. Both public.

**This replaces the session pepper.** The custody code is already public, deterministic, and unlinkable without a key — it does the pseudonym's job. Two mechanisms collapse into one.

### 2.1 Verification still works

After the exam, `master_seed` is published. Anyone can read `custody_code` from the ledger, derive the seed, regenerate the paper, and check the hash. Full public audit, with no ability to link any paper to a person.

### 2.2 Two attacks this opens, and their fixes

**Re-issue drift.** If a terminal fails and the student checks in again under a different attendant, the custody code changes, so the seed changes, so they receive a *different paper* — with their earlier answers orphaned.

> **Fix:** the paper binds to the *first* custody code. Re-issue reuses it and writes a separate `reissue` event carrying the new attendant. The paper is stable; the custody trail grows.

**Grinding.** Officials now control an input to generation. Three officials could swap themselves in and out, regenerating until a favoured candidate draws an easy paper.

> **Fix — apply all three:**
> - The official roster is committed in the genesis block before T=0. Deviation is visible.
> - Every issue is a ledger leaf. Three papers for one student is a permanent, obvious anomaly.
> - One paper per student is enforced: after the first issue, later attempts return the same paper.

---

## 3. Bank encryption

### 3.1 Per-item keys

```
item_key(id)   = HKDF(bank_master_key, "neti/item/v1|" + item_id)
stem_cipher    = AES-256-GCM(item_key, stem + options)
```

A centre serving 500 candidates derives keys for roughly 5,000 items out of 200,000. **A compromised centre node exposes ~2.5% of the bank, not all of it** — and the bank is the asset that survives across exam cycles.

GCM rather than plain AES because it is authenticated: tampering produces a decryption failure, not a silently corrupted question.

### 3.2 Answers encrypted separately

```
solution_cipher = AES-256-GCM(answer_item_key, solution)
answer_item_key = HKDF(answer_master_key, "neti/answer/v1|" + item_id)
```

`bank_master_key` opens at T=0. `answer_master_key` opens when the exam window closes.

A fully compromised centre node mid-exam therefore leaks **questions, not answers** — the answers are not decryptable yet by anyone, anywhere.

### 3.3 Who opens it

The three officials above the attendant **are** the three custody tiers — provided they come from three different institutions:

| Official | Institution | Tier |
|---|---|---|
| `official_1` | Centre superintendent | Centre |
| `official_2` | District / independent observer | Independent |
| `official_3` | NTA / authority representative | Authority |

`bank_master_key` splits 3-of-3 across those tiers — **all three required** — with a 2-of-3 threshold inside each tier so one absent custodian does not stop a national exam.

> **The load-bearing requirement is institutional separation.** Three people from the same office is one institution holding three shares, and the entire guarantee collapses. This is an administrative decision, not a technical one, and it must be enforced administratively.

| Colluding | Opens the bank? |
|---|---|
| Entire exam authority | **No** — missing centre and independent |
| Authority + all centres | **No** — missing independent |
| Centre + judiciary | **No** — missing authority |
| One quorum from each tier | Yes, as designed |

The student and attendant hold **no bank share**. The student's sealed code gates only their own paper — a stronger property, since without it their paper cannot be generated by anyone.

### 3.4 Time-lock as a second, independent lock

Shares stop the *wrong people* opening the bank. They do not stop the *right people* opening it early.

```
bank_blob = TimeLock(unlock_at = T0, ShamirEncrypted(bank))
```

Even a complete three-tier conspiracy cannot open the bank before the exam moment. Not "should not" — cannot.

| Lock | Prevents |
|---|---|
| Three-tier Shamir | The wrong people opening it |
| Time-lock | Anyone opening it early |

---

## 4. Signing — personal, not institutional

Hashes prove nothing changed. They do not prove **who wrote the record**. Without signatures, a fabricated ledger verifies perfectly.

### 4.1 Officials sign personally

Blocks are signed by the **three officials' own keys**, not by an abstract institutional session key.

```
block_hash = SHA-256(0x02 ‖ canonical(header))
signatures = [Ed25519(official_1_key, block_hash),
              Ed25519(official_2_key, block_hash),
              Ed25519(official_3_key, block_hash)]
```

A block carrying fewer than three valid signatures from three different institutions is invalid.

**Why personal keys:** with an institutional key, "who signed this?" answers "the exam authority" — the same useless answer every past inquiry has produced. With personal keys it answers with three names, and none of them can deny it.

**What this costs:** real PKI for thousands of officials — enrolment, revocation, and a defined response when a key is stolen or handed over under pressure. Smart cards or HSM tokens, realistically. This is an administrative programme, not a code change.

**Known weakness:** a personal key is stealable and shareable in a way an HSM key is not. A corrupt official can simply hand theirs over, and the ledger then names an innocent person. Mitigation is biometric-at-signing, so the key alone is insufficient — at the cost of hardware in every centre. Documented rather than solved.

### 4.2 Block header

```json
{
  "version": 1, "session_id": "...", "centre_id": "...",
  "height": 37, "prev_block_hash": "...", "merkle_root": "...",
  "leaf_count": 4096, "first_leaf_index": 147456,
  "bank_version_hash": "...", "generator_source_hash": "...",
  "blueprint_hash": "...", "official_roster_hash": "...",
  "opened_at": "...", "closed_at": "..."
}
```

The **genesis block** is written during the ceremony, before any paper exists, committing the bank version, generator hash, blueprint, and official roster. That is what makes the pre-exam commitment binding — and what makes roster deviation (the grinding defence) detectable.

---

## 5. Submission

### 5.1 Response chain

```
r₀ = SHA-256(0x03 ‖ paper_hash)
rᵢ = SHA-256(0x03 ‖ rᵢ₋₁ ‖ canonical(event_i))
```

The final `rₙ` is signed into a block at submit. Altering any answer afterwards changes `rₙ`, which is already published and signed.

Events chain locally on the terminal, so a network drop does not break the chain — it syncs later and still verifies.

### 5.2 The receipt carries the custody code

```json
{
  "leaf_index": 147481,
  "paper_hash": "...",
  "response_chain_head": "...",
  "custody_code": "9f2b4e81c07a5d3396e1ba4f2c8d70a5",
  "merkle_root": "...",
  "inclusion_proof": [...],
  "signatures": [...]
}
```

The candidate's own proof therefore records **who was responsible for their exam**. If something goes wrong later, they are not dependent on the authority's records to find out who handled it.

The chain head is displayed on screen before submission, so the student sees what they are committing to.

The attendant **counter-signs the submission** — a witnessed submission, not merely a logged one.

---

## 6. Verification

Standalone, minimal dependencies, **no import from the API** — otherwise the system marks its own homework.

### 6.1 Public mode — no key required

```
1. Verify each official's certificate chain
2. Verify all three signatures on every block; verify prev_hash contiguity from genesis
3. Confirm genesis commitments match what was published pre-exam
4. Recompute generator_source_hash from public source — must match
5. For each ledger entry:
     seed = HKDF(master_seed, custody_code)     # custody_code is public
     regenerate paper → hash → compare to recorded leaf
6. Rebuild every Merkle root; compare to headers
7. Report every mismatch with leaf index and block height
```

Step 4 requires **reproducible builds**. If the deployed binary cannot be rebuilt from public source, `generator_source_hash` proves nothing.

### 6.2 Custody mode — warrant and key required

- Resolve a leaf to its five identities
- **Cross-leak intersection:** given a set of leaked papers, report which custody participants appear across them far above chance

One leak names five people. Two hundred leaks name one. This is how the 2024 inquiry proceeded manually; here it is a query.

Every custody-mode use writes a `custody_resolve` event to the ledger.

### 6.3 Student-facing verifier

A single self-contained web page. The student pastes their receipt; it verifies the inclusion proof in-browser using WebCrypto. No server, works offline, valid forever.

---

## 7. Failure and recovery

**Governing rule: every recovery action is itself a signed, multi-party, ledgered event carrying its own custody code.** Recovery paths are attack surfaces, so each one is made visible and requires more than one person.

| Failure | Recovery |
|---|---|
| Custodian unreachable | 2-of-3 inside the tier covers it. **A whole tier absent means the exam cannot start** — correct behaviour, not a bug. |
| Student's sealed code damaged | Attendant + 2 officials jointly issue a replacement; logged as `code_reissue` with all three signatures. Rate-limited per centre; a spike is an anomaly. |
| Terminal fails mid-exam | The paper regenerates from the custody code — nothing lost. Responses are the risk: autosave the local chain to disk and replay on restart. |
| Network partition | Generation is already local. Blocks queue and sync later; they are self-authenticating, so arrival order is irrelevant. |
| Clock drift | Never rely on wall-clock time for anything security-critical. Ledger sequence for ordering; signed server time for the exam timer only. |
| Centre node compromised | Per-item keys already cap the loss. Revoke that centre's tier share; its subsequent blocks stop validating. |

---

## 8. What this framework does and does not do

**Does:**

- Reduces the pre-exam leak window to zero — the time-lock makes early opening impossible, not merely prohibited
- Ensures no institution can open the bank alone
- Makes a paper unmakeable without its custody group on record
- Names five people from any leaked paper, in seconds
- Narrows to individuals across multiple leaks
- Makes scoring publicly recomputable
- Makes misuse of the deanonymisation key permanently visible

**Does not:**

- **Prevent the first leak.** It identifies who was responsible afterwards. The deterrent is real — the first leak ends careers, making the second far less likely — but it is deterrence, not prevention. The time-lock and per-item keys do the preventing.
- **Convict.** Five names is evidence, not a verdict. The student may be a victim. It narrows an investigation from 2.4 million to five, which is enormous, and no more than that.
- **Stop a photographed screen.** Mitigated procedurally, and partially by per-session screen watermarking (not yet designed).
- **Survive a corrupt official handing over their signing key.** Biometric-at-signing mitigates it; nothing eliminates it.
