"""Deterministic Synthetic 3PL Response-Matrix & Item Generator.

Used for offline testing, IRT calibration bootstrapping, and equating simulation.
Labels synthetic data explicitly to prevent conflation with real empirical NEET data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .schema import (
    CognitiveLevelEnum,
    IRTParameters,
    Item,
    ItemBankContainer,
    ItemKindEnum,
    SubjectEnum,
    format_fixed_precision,
)

# Seed domains and templates for generating diverse synthetic items
SUBJECT_CHAPTER_MAP = {
    SubjectEnum.PHYSICS: [
        ("kinematics", ["projectile", "relative_velocity", "uniform_acceleration"]),
        ("laws_of_motion", ["newton_second_law", "friction", "circular_motion"]),
        ("work_energy_power", ["work_energy_theorem", "kinetic_energy", "potential_energy"]),
        ("current_electricity", ["ohms_law", "kirchhoff_laws", "potentiometer"]),
        ("thermodynamics", ["carnot_engine", "first_law_thermo", "molar_heat_capacity"]),
        ("optics", ["lens_formula", "interference", "total_internal_reflection"]),
    ],
    SubjectEnum.CHEMISTRY: [
        ("mole_concept", ["stoichiometry", "molar_mass", "limiting_reagent"]),
        ("atomic_structure", ["bohr_model", "quantum_numbers", "photoelectric_effect"]),
        ("chemical_bonding", ["hybridisation", "dipole_moment", "vsepr_theory"]),
        ("thermodynamics_chem", ["enthalpy_change", "gibbs_free_energy", "hess_law"]),
        ("equilibrium", ["le_chatelier", "solubility_product", "ph_calculation"]),
        ("organic_reactions", ["nucleophilic_substitution", "electrophilic_addition", "markovnikov"]),
    ],
    SubjectEnum.BOTANY: [
        ("cell_biology", ["cell_wall", "mitochondria", "chloroplast", "ribosomes"]),
        ("photosynthesis", ["calvin_cycle", "light_reactions", "c4_pathway"]),
        ("respiration_in_plants", ["glycolysis", "krebs_cycle", "electron_transport"]),
        ("genetics_plants", ["mendelian_ratios", "monohybrid", "dihybrid_cross"]),
        ("plant_growth", ["auxins", "gibberellins", "photoperiodism"]),
    ],
    SubjectEnum.ZOOLOGY: [
        ("human_physiology", ["circulation", "respiratory_system", "neural_control", "nephron"]),
        ("animal_kingdom", ["chordates", "arthropoda", "mollusca"]),
        ("evolution", ["natural_selection", "homologous_organs", "hardy_weinberg"]),
        ("biomolecules", ["enzymes", "protein_structure", "nucleic_acids"]),
        ("human_reproduction", ["gametogenesis", "embryonic_development", "menstrual_cycle"]),
    ],
}


@dataclass
class SyntheticCalibrationData:
    """Bundle containing synthetic student abilities, true item parameters, and the response matrix."""
    student_ids: List[str]
    student_thetas: np.ndarray  # Shape (N,)
    item_ids: List[str]
    true_a: np.ndarray          # Shape (J,)
    true_b: np.ndarray          # Shape (J,)
    true_c: np.ndarray          # Shape (J,)
    response_matrix: np.ndarray # Shape (N, J) with 0 or 1
    probability_matrix: np.ndarray # Shape (N, J) with probabilities in (0, 1)
    items: List[Item]
    is_synthetic: bool = True
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_synthetic": True,
            "num_students": len(self.student_ids),
            "num_items": len(self.item_ids),
            "mean_theta": float(np.mean(self.student_thetas)),
            "std_theta": float(np.std(self.student_thetas)),
            "mean_true_b": float(np.mean(self.true_b)),
            "mean_true_a": float(np.mean(self.true_a)),
            "mean_true_c": float(np.mean(self.true_c)),
            "overall_accuracy": float(np.mean(self.response_matrix)),
        }


def compute_3pl_probability(theta: np.ndarray, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Vectorized 3PL IRT probability calculation.
    
    P(Y_ij = 1 | theta_i, a_j, b_j, c_j) = c_j + (1 - c_j) / (1 + exp(-a_j * (theta_i - b_j)))
    
    Supports:
      theta: (N, 1) or (N,)
      a, b, c: (1, J) or (J,)
    Returns:
      (N, J) matrix of probabilities.
    """
    # Ensure correct broadcasting shapes: theta as (N, 1), items as (1, J)
    th = np.asarray(theta).reshape(-1, 1)
    a_param = np.asarray(a).reshape(1, -1)
    b_param = np.asarray(b).reshape(1, -1)
    c_param = np.asarray(c).reshape(1, -1)

    logit = -a_param * (th - b_param)
    # Numerical clip to prevent overflow in exp
    logit = np.clip(logit, -35.0, 35.0)
    logistic = 1.0 / (1.0 + np.exp(logit))
    
    probs = c_param + (1.0 - c_param) * logistic
    return np.clip(probs, 0.0, 1.0)


def generate_synthetic_dataset(
    num_students: int = 2000,
    num_items: int = 500,
    seed: int = 42,
    a_range: Tuple[float, float] = (0.6, 2.0),
    b_range: Tuple[float, float] = (-2.5, 2.5),
    c_fixed: float = 0.25,
) -> SyntheticCalibrationData:
    """Generate a fully reproducible synthetic IRT response matrix and corresponding Item objects.
    
    Parameters:
        num_students: Number of examinees (N)
        num_items: Number of exam items (J)
        seed: Deterministic RNG seed
        a_range: Minimum and maximum discrimination parameter
        b_range: Minimum and maximum difficulty parameter
        c_fixed: Guessing parameter floor (standard 0.25 for 4-option MCQs)
    """
    rng = np.random.default_rng(seed)

    # 1. Sample student latent ability theta ~ Normal(0, 1)
    thetas = rng.normal(loc=0.0, scale=1.0, size=num_students)

    # 2. Sample item parameters
    # True difficulty b: slightly centered on 0, bounded by b_range
    true_b = rng.uniform(low=b_range[0], high=b_range[1], size=num_items)
    # True discrimination a: log-normal or uniform in a_range
    true_a = rng.uniform(low=a_range[0], high=a_range[1], size=num_items)
    # True guessing c: fixed to 0.25 (or tiny jitter)
    true_c = np.full(num_items, c_fixed)

    # 3. Compute 3PL probabilities and sample Bernoulli responses
    probs = compute_3pl_probability(thetas, true_a, true_b, true_c)
    uniform_draws = rng.uniform(0.0, 1.0, size=(num_students, num_items))
    responses = (uniform_draws < probs).astype(np.int8)

    # 4. Generate structured Item objects conforming to schema
    student_ids = [f"SYNTH-STU-{i:05d}" for i in range(num_students)]
    item_ids = []
    items: List[Item] = []

    subjects = list(SubjectEnum)
    for j in range(num_items):
        subj = subjects[j % len(subjects)]
        chapters = SUBJECT_CHAPTER_MAP[subj]
        chap_idx = (j // len(subjects)) % len(chapters)
        chapter_name, concepts = chapters[chap_idx]
        
        # Pick 1-2 concept tags
        selected_concepts = [concepts[j % len(concepts)]]
        if len(concepts) > 1 and j % 2 == 0:
            selected_concepts.append(concepts[(j + 1) % len(concepts)])

        item_id = f"SYNTH-{subj.value[:3].upper()}-{chapter_name[:3].upper()}-{j+1:04d}"
        item_ids.append(item_id)

        cognitive_level = [
            CognitiveLevelEnum.RECALL,
            CognitiveLevelEnum.APPLICATION,
            CognitiveLevelEnum.ANALYSIS,
        ][j % 3]

        # Determine template vs static
        is_template = (subj in (SubjectEnum.PHYSICS, SubjectEnum.CHEMISTRY)) and (j % 2 == 0)

        # Build IRT parameters with exact 2-decimal strings
        irt_params = IRTParameters.from_floats(true_a[j], true_b[j], true_c[j])

        if is_template:
            stem = f"In a study of {chapter_name.replace('_', ' ')}, a parameter {{v}} is applied at angle {{theta}} degrees. Find the resulting value."
            item = Item(
                id=item_id,
                subject=subj,
                chapter=chapter_name,
                concept_tags=selected_concepts,
                cognitive_level=cognitive_level,
                kind=ItemKindEnum.TEMPLATE,
                stem=stem,
                params={"v": [10, 20, 30, 40], "theta": [15, 30, 45, 60]},
                answer="v * sin(radians(theta)) * 2",
                distractors=[
                    "v * sin(radians(theta)) * 4",
                    "v * sin(radians(theta)) / 2",
                    "v * 3",
                ],
                unit="units",
                irt=irt_params,
                provisional=False,
                bank_version="synthetic-v0.1",
            )
        else:
            stem = f"Which of the following statements is correct regarding {selected_concepts[0].replace('_', ' ')} in {chapter_name.replace('_', ' ')}?"
            options = [
                f"Option A: Principal mechanism of {selected_concepts[0]}",
                f"Option B: Inverse relation in {selected_concepts[0]}",
                f"Option C: Non-reactive state of {selected_concepts[0]}",
                f"Option D: Inapplicable to {chapter_name}",
            ]
            item = Item(
                id=item_id,
                subject=subj,
                chapter=chapter_name,
                concept_tags=selected_concepts,
                cognitive_level=cognitive_level,
                kind=ItemKindEnum.STATIC,
                stem=stem,
                options=options,
                correct=options[0],
                irt=irt_params,
                provisional=False,
                bank_version="synthetic-v0.1",
            )
        items.append(item)

    return SyntheticCalibrationData(
        student_ids=student_ids,
        student_thetas=thetas,
        item_ids=item_ids,
        true_a=true_a,
        true_b=true_b,
        true_c=true_c,
        response_matrix=responses,
        probability_matrix=probs,
        items=items,
        is_synthetic=True,
        metadata={
            "seed": seed,
            "num_students": num_students,
            "num_items": num_items,
            "generated_by": "ml.dataset.synthetic.generate_synthetic_dataset",
        },
    )
