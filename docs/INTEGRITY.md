# Integrity Layer — Specification

This is the normative spec. Code in `backend/app/ledger/` implements it. If they disagree, this document is right and the code is a bug.

## 1. Canonicalisation

Hashing an object requires exactly one byte representation of it. We use **RFC 8785 JSON Canonicalisation Scheme (JCS)**:

- UTF-8, no insignificant whitespace
- Object keys sorted by UTF-16 code unit
- Numbers in ECMAScript shortest round-trip form
- No floats anywhere in hashed structures — IRT parameters are serialised as fixed-precision strings

```python
canonical_bytes(obj) -> bytes    # ledger/canonical.py
```

Never hash a Python `repr`, a pickled object, or `json.dumps` with default settings.

## 2. Domain separation

Every hash is prefixed with a domain tag, so a value valid in one position can never be replayed in another. This is the classic Merkle second-preimage defence and it is not optional.

| Domain | Tag byte | Input |
|---|---|---|
| Paper leaf | `0x00` | `canonical_bytes(paper)` |
| Internal node | `0x01` | `left ‖ right` |
| Block header | `0x02` | `canonical_bytes(header)` |
| Response entry | `0x03` | `canonical_bytes(response)` |
| Receipt | `0x04` | `canonical_bytes(receipt)` |

```
H_leaf(p)      = SHA-256(0x00 ‖ canonical_bytes(p))
H_node(l, r)   = SHA-256(0x01 ‖ l ‖ r)
```

## 3. Merkle tree

- Binary, built bottom-up over leaves **in insertion order** (insertion order is itself part of the record — do not sort).
- Odd node at a level is **promoted**, not duplicated. Duplicating the last node enables the CVE-2012-2459 style forgery where two distinct leaf sets yield the same root. Promote.
- Empty tree root is `SHA-256(0x01)` — defined so the empty case is unambiguous.

### Inclusion proof

A proof for leaf `i` is the sibling path root-ward, each step tagged with the side:

```json
{ "index": 41, "leaf": "…", "path": [{"side": "R", "hash": "…"}, {"side": "L", "hash": "…"}] }
```

Verification recomputes to the root. Proof size is `⌈log2(n)⌉` hashes — for 2.4 million candidates that is 22 hashes, ~700 bytes. Small enough to print on a candidate's receipt slip.

## 4. Block structure

```json
{
  "version": 1,
  "session_id": "2026-NEET-UG",
  "centre_id": "MH-PUNE-014",
  "height": 37,
  "prev_block_hash": "…",
  "merkle_root": "…",
  "leaf_count": 4096,
  "first_leaf_index": 147456,
  "opened_at": "2026-05-03T10:00:00Z",
  "closed_at": "2026-05-03T10:04:11Z",
  "bank_version_hash": "…",
  "generator_source_hash": "…",
  "blueprint_hash": "…",
  "ceremony_id": "…"
}
```

```
block_hash = SHA-256(0x02 ‖ canonical_bytes(header))
signature  = Ed25519_sign(session_key, block_hash)
```

`prev_block_hash` of the genesis block is 32 zero bytes. The genesis block is written by the unlock ceremony and carries `leaf_count: 0`; it commits the bank, generator, and blueprint hashes **before any paper is generated**, which is what makes the pre-exam commitment binding.

`generator_source_hash` is the hash of the source tree that produced the papers. If the deployed generator differs from the published one, verification fails. This is the defence against a doctored build (T15).

## 5. Key hierarchy

```
Authority Root Key (Ed25519, offline, in HSM or air-gapped)
        │ certifies
   Session Key (Ed25519, generated per exam session in the ceremony)
        │ signs
   Blocks
```

Session keys are ephemeral and destroyed at seal. Compromising one session key cannot forge another session's history, and cannot forge past blocks in its own session because those are already published and chained.

## 6. Bank key custody

Shamir's Secret Sharing over GF(2^8), `n = 5`, `k = 3`.

| Holder | Shares |
|---|---|
| Exam authority (two separate custodians) | 2 |
| Exam centre cluster (two separate custodians) | 2 |
| Independent observer / auditor | 1 |

No single institution holds `k`. Authority + centre requires 3 people across 2 institutions; authority alone maxes out at 2. The observer share means a 2-institution collusion still leaves a third party who can testify the ceremony happened.

The ceremony:

1. Custodians present shares → `K` reconstructed **in RAM**
2. `master_seed = CSPRNG(32)` — generated now, never earlier
3. Session key generated, certified by the root key
4. Genesis block written and signed
5. `K` and `master_seed` held in a `mlock`ed region for the exam window
6. At seal: zeroise `K`; **publish** `master_seed`

Ceremony events (share presented, quorum reached, zeroise) are themselves ledgered.

## 7. Seed derivation

```
seed(candidate) = HKDF-SHA256(
    ikm  = master_seed,
    salt = session_id,
    info = b"neti/paper/v1|" + candidate_id,
    L    = 32
)
```

Properties: deterministic, independent across candidates (learning one seed reveals nothing about another), and reproducible by the public once `master_seed` is revealed.

The `info` string carries a version tag. If seed derivation ever changes, bump `v1` — old sessions must stay verifiable forever.

## 8. Response chain

Per candidate, each answer event extends a chain:

```
r_0 = SHA-256(0x03 ‖ paper_hash)
r_i = SHA-256(0x03 ‖ r_{i-1} ‖ canonical_bytes(event_i))
```

Final `r_n` goes into the submission record. Any retroactive edit to any response changes `r_n`, which is signed into a block. Post-hoc mark alteration (T8) becomes detectable rather than a matter of trusting the database.

## 9. Candidate receipt

Issued at submit, signed, and printable:

```json
{
  "candidate_id": "…", "session_id": "…",
  "paper_hash": "…", "response_chain_head": "…",
  "block_height": 37, "leaf_index": 147481,
  "inclusion_proof": [...],
  "signature": "…"
}
```

The candidate can verify this offline against the published root. It answers "what paper did I actually sit?" without needing to trust anyone.

## 10. Publication & anchoring

At seal, the authority publishes a **session bundle**: all block headers + signatures, `master_seed`, bank version hash, generator source hash, blueprint. Mirrored to independent hosts.

Optional anchoring of the final root to a public chain or a newspaper's classified section provides an external timestamp — useful, not load-bearing. The system's guarantee comes from publication + signatures + reproducibility, all of which work offline.

## 11. Verification algorithm

```
1. Check root key cert on session key
2. Check every block signature; check prev_hash chain is contiguous from genesis
3. Confirm genesis commitments match the pre-exam published commitment
4. Recompute generator_source_hash from the public source tree — must match
5. For each candidate:
     seed = HKDF(master_seed, candidate_id)
     paper = generate(seed, bank_version, blueprint)     # deterministic
     leaf = H_leaf(paper)
     assert leaf == ledger leaf at that index
6. Rebuild each Merkle tree; assert root == header root
7. Report: any mismatch, with candidate id and block height
```

Step 5 is what makes substitution (T6) impossible to hide: a favoured candidate's easier paper would produce a leaf that does not match the committed one.

## 12. Rules for implementers

- **No `UPDATE`/`DELETE` on ledger tables.** Enforce with `REVOKE` on the app role, not just discipline.
- **Constant-time comparison** for all hash/signature equality (`hmac.compare_digest`).
- **No custom crypto.** `hashlib`, `cryptography`, `pycryptodome` only.
- **Never log** `master_seed`, `K`, or shares. Add them to the log redaction list explicitly.
- **Determinism is a test target**, not an aspiration: same seed must yield the same paper across processes, machines, and Python patch versions.
