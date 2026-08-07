# NETI — Role 2 (AI/ML) Foundation & Pipeline

This directory contains the machine learning, item tagging, 3PL IRT calibration, and difficulty prediction components for the NETI examination integrity system.

## Invariants & Architecture Rules

1. **The LLM proposes; a symbolic validator disposes.** All generated expressions and options are verified with SymPy.
2. **Zero ML during exam-time generation.** Models execute strictly offline during authoring. Exam-time generation in `backend/app/generation/` is deterministic and pure.
3. **No floats in serialized item representations.** IRT parameters are formatted as RFC 8785 compliant fixed-precision strings (`"a": "1.21"`, `"b": "-0.34"`, `"c": "0.25"`).

## Directory Structure

```
ml/
├── dataset/
│   ├── schema.py             # Canonical Item & IRT parameter schema
│   ├── synthetic.py          # Synthetic 3PL response-matrix generator
│   └── ingest.py             # Data loader, cleaner, and leakage-safe split
├── m1_tagger/
│   ├── baseline.py           # Multi-target TF-IDF classifier
│   ├── train.py              # Training & metric evaluation
│   └── infer.py              # Offline prediction CLI & engine
├── m2_difficulty/
│   ├── irt.py                # 3PL IRT calibration module (MML / quasi-Newton)
│   ├── baseline.py           # Feature-based Ridge regression predictor
│   ├── train.py              # Difficulty & discrimination training pipeline
│   ├── calibrate.py          # Batch bank calibration script
│   └── infer.py              # Offline difficulty prediction CLI
├── validators/
│   └── symbolic.py           # SymPy algebraic & distractor collision checker
├── artifacts/
│   ├── models/               # Serialized .joblib model binaries
│   └── metrics/              # Machine-readable JSON evaluation metrics
├── tests/                    # Dedicated test suite
├── taxonomy.json             # NEET syllabus chapter & concept taxonomy
└── demo.py                   # Single master demo script
```

## Running the Pipeline

### 1. Run the End-to-End Demo

```bash
python ml/demo.py
```

### 2. Run the Unit & Property Test Suite

```bash
python -m pytest ml/tests
```

### 3. Run Individual Training Pipelines

```bash
# Train M1 Concept Tagger
python -m ml.m1_tagger.train

# Train M2 Difficulty Predictor
python -m ml.m2_difficulty.train
```

### 4. Run Offline Inference

```bash
# Predict concept metadata
python -m ml.m1_tagger.infer --stem "Calculate the horizontal range of a projectile."

# Predict difficulty parameters
python -m ml.m2_difficulty.infer --stem "Calculate the horizontal range of a projectile." --subject physics --chapter kinematics
```
