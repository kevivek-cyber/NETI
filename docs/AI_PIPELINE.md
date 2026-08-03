# AI Pipeline — Question Generation & Equating

## The hard constraint

A generated question that is wrong, ambiguous, or unanswerable is worse than no system at all. So the model never has final say. **The LLM proposes; a symbolic validator disposes.** Correctness is established by computation and human review, not by trusting a generative model.

Second hard constraint: 2.4 million *different* papers must be *equally hard*. Uniqueness without equating is just a new kind of unfairness. Section 4 is not optional polish.

## Models

Four trained models. Build them in this order — each one makes the next easier to control.

| # | Model | Input → output | Architecture | Training data | Why it exists |
|---|---|---|---|---|---|
| **M1** | Concept tagger | question text → subject, chapter, concept tags, cognitive level | Encoder (DeBERTa-v3 / SciBERT) + multi-label head | Past papers, hand-labelled seed set of ~2k | Tagging 10 years of items by hand is infeasible; the blueprint needs these labels |
| **M2** | Difficulty predictor | question text (+ tags) → IRT `b`, `a` | Same encoder, regression head | Items with known response statistics; pilot data | **Closes the biggest gap in the project.** Past papers give questions but not how many students got them wrong |
| **M3** | Question generator | concept + difficulty target → new NEET-style item | LoRA fine-tune of an open 7–8B model (Llama 3.1 / Mistral / Qwen 2.5) | Parsed past papers as instruction pairs | Scales the bank beyond what templates cover — Biology, assertion-reason, matching |
| **M4** | Dedup embeddings | question → vector | Sentence-transformer, optionally domain-adapted | Item corpus | Near-duplicate detection; powers exposure caps and hall-collision constraints |

### Build order rationale

M1 and M2 are small, train in minutes on a free Colab GPU, and are useful on day one. M2 is the strategically important one: it lets you estimate difficulty for an item that has never been administered, which is what makes generated questions usable at all.

M3 is the headline model, and it is third on purpose. A generator you cannot steer produces plausible-looking questions of unknown difficulty — worthless for a high-stakes exam. With M2 in place you can generate, score, and keep only what lands in the target band.

### M3 training detail

```
Input  : {"concept": "projectile_range", "difficulty": "b=-0.3", "type": "numerical"}
Output : {"stem": "...", "options": [...], "correct": 0, "solution": "..."}
```

- **Base:** an open 7–8B instruct model. Nothing bigger — this must be reproducible by five students on consumer GPUs or Colab.
- **Method:** LoRA / QLoRA, 4-bit. Full fine-tuning is unnecessary and unaffordable.
- **Data:** ~10 years of parsed papers as instruction pairs, augmented with template instantiations for numericals.
- **Eval:** hold out one year entirely. Metrics in § Evaluation below.

### The constraint that never bends

Every model runs **offline, during authoring**. Output is human-reviewed, then frozen into the approved bank before T=0. No model is ever called during exam-time generation — that would make `generate(seed, bank, blueprint)` non-reproducible and destroy the entire audit guarantee.

The model proposes. The symbolic validator and a subject expert dispose.

## Stage 1 — Ingest past papers

Input: NEET-UG papers and answer keys, ~10 years, plus NCERT-aligned sources.

- PDF → structured text (layout-aware; NEET papers are two-column with inline diagrams)
- Diagram/equation regions extracted as assets, LaTeX where recoverable
- Segmentation into `(stem, options[4], correct_index, solution?)`
- Deduplication by semantic similarity — the same item recurs across years in paraphrase

Output: raw item candidates. Everything downstream is derived from this corpus, so parsing errors are expensive. This stage gets manual spot-check QA at 5% sampling.

## Stage 2 — Tag and calibrate

Each item is tagged with subject → chapter → concept, plus a cognitive level (recall / application / analysis) and the NCERT reference.

**IRT calibration** — a 3-parameter logistic model per item:

```
P(correct | θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
```

- `a` — discrimination (how sharply the item separates strong from weak candidates)
- `b` — difficulty on the same scale as ability `θ`
- `c` — guessing floor (~0.25 for 4-option MCQ)

Calibrated from response data where available (past attempts, mock tests, pilot administrations). Where no response data exists, items enter with **expert-estimated priors** and are flagged `provisional` — provisional items are capped at a small fraction of any live paper until real response data refines them.

This is the piece most student projects skip and the piece a psychometrician will ask about first.

## Stage 3 — Templatise

The core generation trick. A static item becomes a **template** with parameterised values and a symbolic solution.

```
stem:     "A projectile is launched at {{angle}}° with speed {{v}} m/s.
           Find its horizontal range. (g = 10 m/s²)"
params:   angle ∈ {15, 30, 37, 45, 53, 60}
          v     ∈ [10, 50] step 5
solution: R = v**2 * sin(2*radians(angle)) / g
guards:   R must be > 0 and round to ≤ 2 decimals
          answer must not equal any distractor
distractors:
          - v**2 * sin(radians(angle)) / g      # forgot the 2θ
          - v**2 / g                            # ignored angle entirely
          - v * sin(2*radians(angle)) / g       # dropped the square
```

Distractors encode *actual misconceptions*, which is what makes an MCQ discriminate. Randomly wrong numbers produce items everyone gets right.

One template with 6 angles × 9 speeds yields 54 instances — and because the *reasoning* is identical while the numbers differ, all 54 sit in a tight IRT band. That is what lets us generate millions of papers that are genuinely equivalent.

Numericals templatise cleanly (Physics, Physical Chemistry). Biology and conceptual items mostly do not — they rely on Stage 4 and on bank breadth instead.

## Stage 4 — LLM variant generation

Used for the items templates can't cover: assertion-reason, statement-matching, diagram interpretation, and conceptual Biology.

The LLM's job is **paraphrase and recombination within a verified concept**, never invention of new physics. Every generated variant carries the source item id and must preserve its answer semantics.

Gate — a variant reaches the live pool only after passing all of:

| Check | Method |
|---|---|
| Factual grounding | Retrieval against NCERT corpus; claim must be supported by a cited passage |
| Answer uniqueness | Exactly one option defensible; distractors verified non-equivalent |
| Syllabus scope | Concept tag must exist in the NEET syllabus map — no out-of-syllabus items |
| Difficulty estimate | Model-predicted `b` within the source item's band, confirmed by pilot data |
| Language | Clarity check + Hindi/English parity for bilingual delivery |
| **Human review** | A subject expert approves. No exceptions. |

Rejected variants are kept as training signal for what fails, not deleted.

**Critical:** the LLM runs **offline, during authoring**, never at exam time. Exam-time generation is deterministic template instantiation from an already-approved bank. An LLM call during the exam would break determinism (invariant #2 in [CLAUDE.md](../CLAUDE.md)) and make audit impossible.

## Stage 5 — Blueprint

The paper's shape, config-driven so pattern changes don't touch code:

| Subject | Questions | Marks |
|---|---|---|
| Physics | 45 | 180 |
| Chemistry | 45 | 180 |
| Botany | 45 | 180 |
| Zoology | 45 | 180 |
| **Total** | **180** | **720** |

Marking: +4 correct, −1 incorrect, 0 unattempted. Duration 180 minutes. *(Current NEET-UG pattern; verify against the live NTA bulletin each cycle — this has changed twice recently.)*

Beyond counts, the blueprint constrains:

- **Chapter weightage** — must match the historical distribution within tolerance
- **Cognitive mix** — target ratio of recall / application / analysis
- **Difficulty curve** — target Test Information Function across the ability range
- **NCERT coverage** — no chapter over- or under-represented

## Stage 6 — Constrained sampling

For each candidate, seeded and deterministic:

```
1. Seed a ChaCha20 RNG with the candidate's 32-byte seed
2. For each blueprint cell (subject × chapter × cognitive level):
     sample items meeting the cell's difficulty target
3. Apply constraints:
     - no two items sharing a concept_tag triple
     - no item from the candidate's own recent attempts (retakers)
     - hall-collision cap: ≤ k items shared with any co-located candidate
     - provisional-item quota not exceeded
4. Instantiate templates with seeded parameter draws
5. Validate every instance symbolically (recompute the answer)
6. Permute item order and option order
7. Compute the paper's Test Information Function
8. If TIF is outside the tolerance band → reseed step 2 and retry (bounded retries)
9. Canonical-serialise
```

Step 8 is the equating guarantee. Step 5 is the correctness guarantee. Neither is skippable for performance.

## Stage 7 — Post-hoc equating

Even with tight targeting, residual difficulty variance exists. After the exam, IRT scoring converts raw scores to ability estimates `θ` on a common scale, so a candidate is never penalised for having drawn a marginally harder draw.

This must be **published and explained** before the exam, not introduced afterwards. Candidates and courts accept scaling they were told about in advance; they do not accept it as a post-hoc correction.

## Evaluation

The pipeline is judged on:

| Metric | Target |
|---|---|
| Generated-item factual accuracy (expert audit) | > 99.5% |
| Inter-paper difficulty spread (SD of mean `b`) | < 0.05 logits |
| Item exposure rate (max % of candidates seeing one item) | < 5% |
| Hall collision (max shared items between neighbours) | ≤ k, configurable |
| Generation latency per paper | < 500 ms |
| Determinism (same seed → same paper, cross-machine) | 100%, always |

## Open questions

- Minimum viable bank size for 2.4M candidates at < 5% exposure — needs simulation, not guesswork.
- Diagram-based Physics items: generation of *novel diagrams* is unsolved here. Current plan is a curated diagram library with parameterised labels.
- Bilingual (Hindi/English) template parity — machine translation is not acceptable for a high-stakes exam; needs bilingual authoring.
