"""End-to-End Demo & Verification Script for NETI Role 2 (AI/ML) MVP.

Executes:
1. Curated Mock Dataset Generation (350 items across Physics, Chemistry, Botany, Zoology)
2. Comprehensive Dataset Quality Audit (distribution, grounding, balance)
3. SymPy Symbolic Validation on Numerical Templates
4. 3PL IRT Parameter Calibration Experiment
5. M1 Concept Tagger Training, Evaluation vs Majority Baseline, and Confusion Matrix
6. M2 Difficulty Predictor Training, Evaluation vs Mean Predictor Baseline (R^2, RMSE, Pearson r)
7. Automated Quality Gates Verification
8. Live Offline Multi-Subject Inference on 10 Realistic Exam Questions
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add repository root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROOT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from ml.dataset.audit import audit_item_dataset, print_audit_report
from ml.dataset.curated_mock import generate_curated_mock_dataset
from ml.m1_tagger.infer import M1InferenceEngine
from ml.m1_tagger.train import train_m1_pipeline
from ml.m2_difficulty.infer import M2InferenceEngine
from ml.m2_difficulty.irt import run_synthetic_calibration_experiment
from ml.m2_difficulty.train import train_m2_pipeline
from ml.quality_gates import run_all_quality_gates
from ml.validators.symbolic import validate_template_algebra

MODELS_DIR = ROOT_DIR / "artifacts" / "models"
METRICS_DIR = ROOT_DIR / "artifacts" / "metrics"


SAMPLE_QUESTIONS_10 = [
    # Physics
    {
        "stem": "A particle is projected from horizontal ground at an angle of 30 degrees with an initial velocity of 40 m/s under gravity g = 10 m/s^2. Determine the total horizontal range.",
        "options": ["138.56 m", "80.00 m", "160.00 m", "69.28 m"],
        "expected_subj": "physics",
        "expected_cog": "application",
    },
    {
        "stem": "State the relationship governing the maximum static friction (limiting friction) between two solid surfaces with normal reaction N and coefficient mu_s.",
        "options": ["f_max = mu_s * N", "f_max = mu_s / N", "f_max = N / mu_s", "f_max = mu_s * N^2"],
        "expected_subj": "physics",
        "expected_cog": "recall",
    },
    {
        "stem": "In a potentiometer circuit, evaluate the internal resistance of a 1.5 V cell when connected in parallel to a 10 ohm resistor shifting balance point from 30 cm to 20 cm.",
        "options": ["5.0 ohm", "2.5 ohm", "7.5 ohm", "10.0 ohm"],
        "expected_subj": "physics",
        "expected_cog": "analysis",
    },
    # Chemistry
    {
        "stem": "Calculate the amount in moles present in 90 grams of water (H2O) having a molar mass of 18 g/mol.",
        "options": ["5.0 mol", "10.0 mol", "2.0 mol", "18.0 mol"],
        "expected_subj": "chemistry",
        "expected_cog": "application",
    },
    {
        "stem": "Identify the maximum number of electrons that can be accommodated in an orbital shell with principal quantum number n = 3.",
        "options": ["18 electrons", "8 electrons", "32 electrons", "9 electrons"],
        "expected_subj": "chemistry",
        "expected_cog": "recall",
    },
    {
        "stem": "Compare the dipole moments of NH3 and NF3. Which statement correctly explains why NH3 has a significantly higher dipole moment than NF3?",
        "options": [
            "In NH3 the orbital dipole due to lone pair is in the same direction as the resultant dipole of N-H bonds, whereas in NF3 it opposes the resultant N-F dipole",
            "Fluorine is less electronegative than hydrogen",
            "NF3 adopts a planar geometry",
            "N-F bond length is shorter than N-H"
        ],
        "expected_subj": "chemistry",
        "expected_cog": "analysis",
    },
    # Botany
    {
        "stem": "Identify the primary structural carbohydrate polymer that constitutes the major framework of the plant cell wall.",
        "options": ["Cellulose", "Chitin", "Peptidoglycan", "Glycogen"],
        "expected_subj": "botany",
        "expected_cog": "recall",
    },
    {
        "stem": "In a classical Mendelian monohybrid cross between homozygous tall (TT) and dwarf (tt) pea plants, determine the expected phenotypic ratio in the F2 generation.",
        "options": ["3 Tall : 1 Dwarf", "1 Tall : 2 Medium : 1 Dwarf", "9:3:3:1", "1:1"],
        "expected_subj": "botany",
        "expected_cog": "application",
    },
    # Zoology
    {
        "stem": "Identify the specific chamber of the human heart that contracts to pump oxygenated systemic blood directly into the systemic aorta.",
        "options": ["Left ventricle", "Right ventricle", "Left atrium", "Right atrium"],
        "expected_subj": "zoology",
        "expected_cog": "recall",
    },
    {
        "stem": "Analyze why competitive enzyme inhibition by malonate increases the Michaelis constant Km while leaving Vmax unchanged.",
        "options": [
            "Malonate binds reversibly to the active site, competing with substrate succinate",
            "Malonate irreversibly degrades the catalytic active site",
            "Malonate binds to an allosteric regulatory site",
            "Malonate increases enzyme turnover number kcat"
        ],
        "expected_subj": "zoology",
        "expected_cog": "analysis",
    },
]


def run_full_pipeline_demo() -> None:
    print("=" * 72)
    print("  NETI -- Role 2 (AI/ML) Diagnostic, Repair & Verification Demo")
    print("=" * 72)

    seed = 42
    # -------------------------------------------------------------
    # Step 1: Generate & Audit Curated Mock Dataset
    # -------------------------------------------------------------
    print("\n[Step 1/8] Generating Curated Mock Dataset (350 Items)...")
    curated_items = generate_curated_mock_dataset(target_count=350, seed=seed)
    audit_report = audit_item_dataset(curated_items)
    print_audit_report(audit_report)

    # -------------------------------------------------------------
    # Step 2: Symbolic Algebraic Validation
    # -------------------------------------------------------------
    print("\n[Step 2/8] Running SymPy Symbolic Validator on Templates...")
    template_sample = next(it for it in curated_items if it.kind.value == "template")
    sym_val = validate_template_algebra(
        stem=template_sample.stem,
        params=template_sample.params,
        answer_expr=template_sample.answer,
        distractor_exprs=template_sample.distractors,
        unit=template_sample.unit,
    )
    print(f"  [OK] Checked template {template_sample.id}: {sym_val['total_combinations_tested']} parameter combinations tested.")
    print(f"  [OK] Algebraic validation status: {'PASSED' if sym_val['is_valid'] else 'FAILED'}")

    # -------------------------------------------------------------
    # Step 3: 3PL IRT Parameter Calibration Experiment
    # -------------------------------------------------------------
    print("\n[Step 3/8] Running 3PL IRT Calibration Experiment...")
    irt_exp = run_synthetic_calibration_experiment(num_students=2000, num_items=500, seed=seed)
    print(f"  [OK] Item Difficulty b -- MAE: {irt_exp['difficulty_b']['mae']:.3f}, RMSE: {irt_exp['difficulty_b']['rmse']:.3f}, Pearson r: {irt_exp['difficulty_b']['pearson_r']:.3f}")
    print(f"  [OK] Item Discrimination a -- MAE: {irt_exp['discrimination_a']['mae']:.3f}, RMSE: {irt_exp['discrimination_a']['rmse']:.3f}, Pearson r: {irt_exp['discrimination_a']['pearson_r']:.3f}")

    # -------------------------------------------------------------
    # Step 4: Train M1 Concept Tagger Baseline
    # -------------------------------------------------------------
    print("\n[Step 4/8] Training M1 Concept Tagger Baseline...")
    m1_model_path = MODELS_DIR / "m1_concept_tagger.joblib"
    m1_metrics_path = METRICS_DIR / "m1_metrics.json"
    m1_res = train_m1_pipeline(
        items=curated_items,
        model_output_path=m1_model_path,
        metrics_output_path=m1_metrics_path,
        seed=seed,
    )
    m1_m = m1_res["metrics"]
    s_diag = m1_m["subject"]
    c_diag = m1_m["cognitive_level"]
    print(f"  [OK] Subject Accuracy:         {s_diag['model_accuracy']:.3f} (Majority Baseline: {s_diag['majority_baseline_accuracy']:.3f}, Beats Baseline: {s_diag['beats_majority_baseline']})")
    print(f"  [OK] Subject Macro-F1:         {s_diag['macro_f1']:.3f}, Weighted-F1: {s_diag['weighted_f1']:.3f}")
    print(f"  [OK] Cognitive Level Accuracy: {c_diag['model_accuracy']:.3f} (Majority Baseline: {c_diag['majority_baseline_accuracy']:.3f}, Beats Baseline: {c_diag['beats_majority_baseline']})")
    print(f"  [OK] Cognitive Level Macro-F1: {c_diag['macro_f1']:.3f}, Weighted-F1: {c_diag['weighted_f1']:.3f}")
    print(f"  [OK] Multi-label Concepts:     Micro-F1: {m1_m['concept_tags']['micro_f1']:.3f}, Hamming Loss: {m1_m['concept_tags']['hamming_loss']:.4f}")

    # -------------------------------------------------------------
    # Step 5: Train M2 Difficulty Predictor Baseline
    # -------------------------------------------------------------
    print("\n[Step 5/8] Training M2 Difficulty Predictor Baseline...")
    m2_model_path = MODELS_DIR / "m2_difficulty_predictor.joblib"
    m2_metrics_path = METRICS_DIR / "m2_metrics.json"
    m2_res = train_m2_pipeline(
        items=curated_items,
        model_output_path=m2_model_path,
        metrics_output_path=m2_metrics_path,
        seed=seed,
    )
    m2_m = m2_res["metrics"]
    b_diag = m2_m["difficulty_b"]
    a_diag = m2_m["discrimination_a"]
    print(f"  [OK] Difficulty b -- RMSE: {b_diag['model_rmse']:.3f} vs Mean Baseline: {b_diag['mean_baseline_rmse']:.3f} (Beats Baseline: {b_diag['beats_mean_baseline_rmse']})")
    print(f"  [OK] Difficulty b -- R^2:  {b_diag['r2_score']:.3f}, Pearson r: {b_diag['pearson_r']:.3f}, Spearman rho: {b_diag['spearman_rho']:.3f}")
    print(f"  [OK] Discrimination a -- RMSE: {a_diag['model_rmse']:.3f}, Pearson r: {a_diag['pearson_r']:.3f}")

    # -------------------------------------------------------------
    # Step 6: Automated Quality Gates
    # -------------------------------------------------------------
    print("\n[Step 6/8] Executing Automated Quality Gates...")
    gates_summary = run_all_quality_gates(seed=seed)
    print(f"  [OK] Quality Gates Overall Status: {gates_summary['status']}")

    # -------------------------------------------------------------
    # Step 7: Live Inference on 10 Diverse Questions
    # -------------------------------------------------------------
    print("\n[Step 7/8] Running Live Offline Inferences on 10 NEET Questions...")
    m1_engine = M1InferenceEngine(m1_model_path)
    m2_engine = M2InferenceEngine(m2_model_path)

    print("-" * 72)
    for idx, q in enumerate(SAMPLE_QUESTIONS_10, start=1):
        pred_m1 = m1_engine.predict_one(q["stem"], q["options"])
        pred_m2 = m2_engine.predict_one(
            stem=q["stem"],
            subject=pred_m1["subject"],
            chapter=pred_m1["chapter"],
            cognitive_level=pred_m1["cognitive_level"],
            options=q["options"],
        )

        src = pred_m1.get("source", "ml")
        print(f"Q{idx:02d} [{pred_m1['subject'].upper()}] Stem: {q['stem'][:65]}...")
        print(f"     Pred Subject: {pred_m1['subject']} (Expected: {q['expected_subj']}) | Conf: {pred_m1['subject_confidence']:.1%}")
        print(f"     Pred Chapter: {pred_m1['chapter']} | Cog Level: {pred_m1['cognitive_level']} (Expected: {q['expected_cog']})")
        print(f"     Pred Concepts: {pred_m1['concept_tags']} | Source: {src}")
        print(f"     M2 Predicted IRT: a={pred_m2['a']}, b={pred_m2['b']}, c={pred_m2['c']}")
        print("-" * 72)

    print("\n[Step 8/8] Role 2 Diagnostic, Repair, and Evaluation Completed.")
    print("=" * 72)


if __name__ == "__main__":
    run_full_pipeline_demo()
