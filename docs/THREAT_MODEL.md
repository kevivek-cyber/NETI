# Threat Model

Written first, deliberately. Every design decision in this repo traces back to a row in these tables. If you propose a change, say which row it moves.

## Assets

| Asset | Why an attacker wants it | Window of exposure in the status quo |
|---|---|---|
| Question paper content | Sell to candidates, coach a syndicate | ~8–12 weeks (authoring → exam) |
| Answer key | Same, higher value | Same |
| Item bank | Reusable across many exam cycles | Permanent |
| Candidate responses | Alter marks post-hoc | Exam → result declaration |
| Scores / ranks | Seat allocation fraud | Result → counselling |
| Generator source + seeds | Predict a candidate's paper in advance | Permanent (source is public by design) |

## Adversaries

| # | Adversary | Capability | Motive |
|---|---|---|---|
| A1 | **Insider — printing/transit/vault** | Physical access to sealed material, days early | Money. Historically the actual leak vector. |
| A2 | **Insider — exam authority staff** | Legitimate system credentials, possibly DB access | Money, coercion |
| A3 | **Centre staff / invigilator** | Physical access to terminals at T=0 | Money |
| A4 | **Candidate** | One terminal, one session, possibly a phone | Personal advantage |
| A5 | **Organised syndicate** | A1–A4 combined, capital, multiple centres | Large-scale resale |
| A6 | **External attacker** | Network access, no credentials | Disruption, ransom, notoriety |
| A7 | **The authority itself** | Total control of infrastructure | Cover up a failure, favour a cohort |

A7 is the one most systems ignore, and the one public verifiability exists for. A design that only defends against A6 is not addressing NEET.

## Attack surface and mitigations

| # | Attack | Mitigation | Where implemented |
|---|---|---|---|
| T1 | Steal printed papers in transit | **No printing.** Papers are generated at the terminal at T=0. | Architecture — no artifact exists |
| T2 | Exfiltrate the item bank from storage | AES-256-GCM at rest; key never present in assembled form outside an unlock ceremony | `bank/encryption.py` |
| T3 | Authority insider decrypts the bank early | Shamir k-of-n split across authority + centre + independent observer; unlock is a logged, quorate ceremony | `core/keyrelease.py` |
| T4 | Steal one candidate's paper, sell it | Every paper is different; a leaked paper has ~0 predictive value for any other candidate | Per-candidate seed derivation |
| T5 | Predict a paper in advance from public source code | Seed = `HKDF(master_seed ‖ candidate_id)`; `master_seed` is generated inside the unlock ceremony at T=0 and has 256 bits of entropy | `INTEGRITY.md` § Seeds |
| T6 | Substitute an easier paper for a favoured candidate | Paper hash is committed to the Merkle tree at generation; post-exam reveal lets anyone regenerate and compare | `ledger/` |
| T7 | Rewrite the ledger after the fact | Append-only grants at DB level + hash chaining + external anchoring of daily roots | `ledger/chain.py`, ops |
| T8 | Tamper with stored responses | Responses hashed and chained per candidate; receipt hash shown to candidate before submit | `exam/session.py` |
| T9 | Deny having received a paper / dispute the paper sat | Signed inclusion proof issued to candidate at submit; verifiable offline | `ledger/merkle.py` proofs |
| T10 | Collusion — candidates in one hall share answers | Sampling constraint: no two candidates in the same hall share more than `k` items; item order and option order permuted per candidate | `generation/sampler.py` |
| T11 | Generated question is wrong / ambiguous / unanswerable | Every generated item passes symbolic validation + a human-reviewed template; unreviewed templates never reach a live pool | `generation/validators/` |
| T12 | Papers differ in difficulty → unfairness challenge | IRT-based blueprint targeting; each paper's test information function must fall inside a tolerance band or generation retries | `generation/blueprint.py` |
| T13 | Centre network goes down mid-exam | Encrypted bank shard is pre-staged locally; generation is local; ledger entries sync when connectivity returns | Offline-first design |
| T14 | Compromised terminal captures the paper as it renders | Out of scope for software; mitigated procedurally (kiosk mode, no external media, camera monitoring). Documented, not solved. | — |
| T15 | Malicious generator build differs from published source | Build reproducibility: generator binary/source hash is committed pre-exam and included in every block header | `ledger/chain.py` block header |

## Explicitly out of scope

Being honest about limits is part of the threat model:

- **Impersonation at the centre** (someone else sits the exam) — biometric/identity problem, orthogonal to paper leaks.
- **Physical surveillance of the screen** (T14) — cameras, procedure.
- **Coercion of a k-of-n quorum** — if the authority, centre, and observer all collude, the bank opens early. The design raises the cost and leaves evidence; it does not make collusion impossible.
- **Bad items in the source bank** — garbage in, garbage out. Mitigated by review, not by cryptography.

## Residual risk statement

NETI reduces the pre-exam leak window from weeks to **zero** and converts post-exam tampering from *undetectable* to *provable*. It does not eliminate insider collusion at exam time, and it does not solve candidate impersonation. Any claim beyond that is overselling, and we don't make it.
