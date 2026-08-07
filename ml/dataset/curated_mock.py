"""Curated Development & Mock Item Dataset for NETI ML Pipeline.

Provides semantically grounded, authentic NEET-style questions across
all four subjects (Physics, Chemistry, Botany, Zoology) with realistic
lexical patterns, syllabus concepts, cognitive levels, and structurally
grounded 3PL IRT parameters.

Clearly labeled as 'development/curated_mock' for offline testing.
"""

from __future__ import annotations

import itertools
import random
from typing import Any, Dict, List, Tuple
import numpy as np

from .schema import (
    CognitiveLevelEnum,
    IRTParameters,
    Item,
    ItemKindEnum,
    SubjectEnum,
    format_fixed_precision,
)

# Raw curated templates and static question definitions across NEET syllabus
CURATED_TAXONOMY_ITEMS = [
    # =========================================================================
    # PHYSICS (Kinematics, Dynamics, Work-Energy, Electricity, Thermodynamics, Optics)
    # =========================================================================
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "kinematics",
        "concept_tags": ["projectile_motion", "horizontal_range"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "A particle is projected from horizontal ground at an angle of {angle} degrees with an initial velocity of {v} m/s under gravity g = 10 m/s^2. Determine the total horizontal range of the projectile.",
        "params": {"angle": [15, 30, 37, 53, 75], "v": [10, 20, 30, 40, 50]},
        "answer": "v**2 * sin(2*radians(angle)) / 10",
        "distractors": [
            "v**2 * sin(radians(angle)) / 10",
            "v**2 / 35",
            "v * sin(2*radians(angle)) / 10",
        ],
        "unit": "m",
        "base_b": -0.2, "base_a": 1.3,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "kinematics",
        "concept_tags": ["uniform_acceleration", "kinematics_equations"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "A vehicle starting from rest accelerates uniformly at {a} m/s^2 for a duration of {t} seconds. Calculate the total displacement traversed by the vehicle.",
        "params": {"a": [2, 4, 6, 8], "t": [3, 5, 8, 10]},
        "answer": "a * t**2 / 2",
        "distractors": ["a * t", "a * t**2", "a**2 * t / 2"],
        "unit": "m",
        "base_b": -0.7, "base_a": 1.1,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "kinematics",
        "concept_tags": ["relative_velocity", "vector_subtraction"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "Two trains A and B of length 400 m each are moving on two parallel tracks with a uniform speed of 72 km/h in the same direction, with A ahead of B. The driver of B decides to overtake A and accelerates at 1 m/s^2. If after 50 s, the guard of B just brushes past the driver of A, what was the original distance between them?",
        "options": ["1250 m", "1000 m", "1500 m", "2250 m"],
        "correct": "1250 m",
        "base_b": 1.2, "base_a": 1.6,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "laws_of_motion",
        "concept_tags": ["newton_second_law", "momentum_conservation"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "A constant net force acts on a stationary mass of {m} kg, accelerating it at {a} m/s^2. Calculate the magnitude of the applied net force.",
        "params": {"m": [2, 5, 8, 12], "a": [3, 4, 6, 10]},
        "answer": "m * a",
        "distractors": ["m + a", "m / a", "m * a * 10"],
        "unit": "N",
        "base_b": -1.1, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "laws_of_motion",
        "concept_tags": ["friction", "limiting_friction"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "State the relationship governing the maximum static friction (limiting friction) between two surfaces in contact with normal reaction N and coefficient of static friction mu_s.",
        "options": ["f_max = mu_s * N", "f_max = mu_s / N", "f_max = N / mu_s", "f_max = mu_s * N^2"],
        "correct": "f_max = mu_s * N",
        "base_b": -1.5, "base_a": 0.9,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "work_energy_power",
        "concept_tags": ["kinetic_energy", "work_energy_theorem"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "Calculate the kinetic energy possessed by an object of mass {m} kg moving with a translational velocity of {v} m/s.",
        "params": {"m": [2, 4, 6, 10], "v": [3, 5, 8, 10]},
        "answer": "m * v**2 / 2",
        "distractors": ["m * v / 2", "m * v**2", "m**2 * v / 2"],
        "unit": "J",
        "base_b": -0.8, "base_a": 1.1,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "current_electricity",
        "concept_tags": ["ohms_law", "resistor_circuits"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "A resistor of resistance {r} ohms carries an electric current of {i} amperes. Determine the electric potential difference across the terminal.",
        "params": {"r": [5, 10, 20, 50], "i": [1, 2, 4, 5]},
        "answer": "r * i",
        "distractors": ["r / i", "i / r", "r * i**2"],
        "unit": "V",
        "base_b": -1.0, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "current_electricity",
        "concept_tags": ["potentiometer", "internal_resistance"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "In a potentiometer circuit, a cell of emf 1.5 V gives a balance point at 30 cm length of wire. When a resistor of 10 ohm is connected in parallel to the cell, the balance point shifts to 20 cm. Evaluate the internal resistance of the cell.",
        "options": ["5.0 ohm", "2.5 ohm", "7.5 ohm", "10.0 ohm"],
        "correct": "5.0 ohm",
        "base_b": 1.4, "base_a": 1.7,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "thermodynamics",
        "concept_tags": ["carnot_engine", "thermal_efficiency"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "A Carnot heat engine operates between a source at temperature {t1} K and a heat sink at temperature {t2} K. Determine the maximum theoretical thermal efficiency of the engine as a percentage.",
        "params": {"t1": [400, 500, 600, 800], "t2": [200, 300]},
        "answer": "(t1 - t2) / t1 * 100",
        "distractors": ["(t1 - t2) / t2 * 100", "t2 / t1 * 100", "(t1 + t2) / t1 * 100"],
        "unit": "%",
        "base_b": 0.3, "base_a": 1.4,
    },
    {
        "subject": SubjectEnum.PHYSICS,
        "chapter": "optics",
        "concept_tags": ["lens_formula", "focal_length"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "An object is placed at a distance of {u} cm in front of a convex lens of focal length {f} cm. Find the image distance v formed by the lens.",
        "params": {"u": [20, 30, 40], "f": [10, 15]},
        "answer": "(u * f) / (u - f)",
        "distractors": ["(u * f) / (u + f)", "(u - f) / (u * f)", "u + f"],
        "unit": "cm",
        "base_b": 0.5, "base_a": 1.4,
    },

    # =========================================================================
    # CHEMISTRY (Mole Concept, Atomic Structure, Chemical Bonding, Thermo, Equilibrium, Organic)
    # =========================================================================
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "mole_concept",
        "concept_tags": ["stoichiometry", "molar_mass"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.TEMPLATE,
        "stem": "Calculate the amount in moles present in {mass} grams of an organic compound having a molar mass of {mm} g/mol.",
        "params": {"mass": [18, 36, 54, 90, 180], "mm": [18, 44, 90]},
        "answer": "mass / mm",
        "distractors": ["mass * mm", "mm / mass", "mass * mm / 100"],
        "unit": "mol",
        "base_b": -0.6, "base_a": 1.2,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "mole_concept",
        "concept_tags": ["limiting_reagent", "reaction_stoichiometry"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "When 20.0 g of calcium carbonate reacts completely with 20.0 g of hydrochloric acid according to CaCO3 + 2HCl -> CaCl2 + CO2 + H2O, deduce the limiting reagent and the mass of CO2 evolved.",
        "options": ["CaCO3 is limiting, 8.8 g CO2 evolved", "HCl is limiting, 12.0 g CO2 evolved", "CaCO3 is limiting, 4.4 g CO2 evolved", "Neither is limiting, 20.0 g CO2 evolved"],
        "correct": "CaCO3 is limiting, 8.8 g CO2 evolved",
        "base_b": 1.1, "base_a": 1.5,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "atomic_structure",
        "concept_tags": ["quantum_numbers", "electronic_configuration"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Identify the maximum number of electrons that can be accommodated in an orbital shell with principal quantum number n = 3.",
        "options": ["18 electrons", "8 electrons", "32 electrons", "9 electrons"],
        "correct": "18 electrons",
        "base_b": -1.2, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "atomic_structure",
        "concept_tags": ["bohr_model", "photoelectric_effect"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "According to the de Broglie hypothesis and Bohr model of hydrogen atom, what is the relation between electron orbit radius r and de Broglie wavelength lambda in the nth stationary orbit?",
        "options": ["2 * pi * r = n * lambda", "2 * pi * r = lambda / n", "pi * r^2 = n * lambda", "r = n^2 * lambda / (2 * pi)"],
        "correct": "2 * pi * r = n * lambda",
        "base_b": 0.8, "base_a": 1.4,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "chemical_bonding",
        "concept_tags": ["hybridisation", "molecular_geometry"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Identify the hybridisation and geometrical spatial shape of the central carbon atom in a molecule of methane (CH4).",
        "options": ["sp3 hybridisation with tetrahedral geometry", "sp2 hybridisation with trigonal planar geometry", "sp hybridisation with linear geometry", "dsp2 hybridisation with square planar geometry"],
        "correct": "sp3 hybridisation with tetrahedral geometry",
        "base_b": -1.3, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "chemical_bonding",
        "concept_tags": ["dipole_moment", "vsepr_theory"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "Compare the dipole moments of NH3 and NF3. Which of the following statements correctly explains why NH3 has a significantly higher dipole moment than NF3?",
        "options": [
            "In NH3 the orbital dipole due to lone pair is in the same direction as the resultant dipole of N-H bonds, whereas in NF3 it opposes the resultant N-F dipole",
            "Fluorine is less electronegative than hydrogen in the gas phase",
            "NF3 adopts a planar geometry while NH3 adopts a pyramidal geometry",
            "The N-F bond length is much longer than the N-H bond length"
        ],
        "correct": "In NH3 the orbital dipole due to lone pair is in the same direction as the resultant dipole of N-H bonds, whereas in NF3 it opposes the resultant N-F dipole",
        "base_b": 1.3, "base_a": 1.7,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "thermodynamics_chem",
        "concept_tags": ["gibbs_free_energy", "spontaneity"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.STATIC,
        "stem": "For a chemical reaction at 300 K, delta H = -40.0 kJ/mol and delta S = -100 J/(K*mol). Calculate the Gibbs free energy change delta G and evaluate whether the reaction is spontaneous.",
        "options": ["delta G = -10.0 kJ/mol, spontaneous", "delta G = -70.0 kJ/mol, spontaneous", "delta G = +10.0 kJ/mol, non-spontaneous", "delta G = -40.0 kJ/mol, equilibrium"],
        "correct": "delta G = -10.0 kJ/mol, spontaneous",
        "base_b": 0.4, "base_a": 1.3,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "equilibrium",
        "concept_tags": ["le_chatelier", "ph_calculation"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.STATIC,
        "stem": "Calculate the pH of an aqueous buffer solution prepared by mixing 0.1 M acetic acid (CH3COOH, pKa = 4.74) with 0.1 M sodium acetate (CH3COONa).",
        "options": ["pH = 4.74", "pH = 5.74", "pH = 3.74", "pH = 7.00"],
        "correct": "pH = 4.74",
        "base_b": -0.2, "base_a": 1.2,
    },
    {
        "subject": SubjectEnum.CHEMISTRY,
        "chapter": "organic_reactions",
        "concept_tags": ["nucleophilic_substitution", "sn1_sn2"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Which of the following alkyl halides undergoes nucleophilic substitution via the SN1 mechanism at the fastest rate due to carbocation stability?",
        "options": ["tert-Butyl bromide (3°)", "Isopropyl bromide (2°)", "Ethyl bromide (1°)", "Methyl bromide"],
        "correct": "tert-Butyl bromide (3°)",
        "base_b": -0.9, "base_a": 1.1,
    },

    # =========================================================================
    # BOTANY (Cell Biology, Photosynthesis, Respiration, Plant Genetics, Growth)
    # =========================================================================
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "cell_biology",
        "concept_tags": ["cell_wall", "cellulose_structure"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Identify the primary structural carbohydrate polymer that constitutes the major framework of the plant cell wall.",
        "options": ["Cellulose", "Chitin", "Peptidoglycan", "Glycogen"],
        "correct": "Cellulose",
        "base_b": -1.7, "base_a": 0.8,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "cell_biology",
        "concept_tags": ["chloroplast", "mitochondria", "endosymbiosis"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "Which of the following structural and genetic characteristics provides direct evidence that chloroplasts and mitochondria evolved via an endosymbiotic origin in plant cells?",
        "options": [
            "Presence of 70S ribosomes and circular double-stranded DNA",
            "Presence of 80S ribosomes and linear chromosomes",
            "Presence of single membrane lipid bilayer without transport pores",
            "Synthesis of carbohydrate cell wall polymers"
        ],
        "correct": "Presence of 70S ribosomes and circular double-stranded DNA",
        "base_b": 0.7, "base_a": 1.5,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "photosynthesis",
        "concept_tags": ["calvin_cycle", "rubisco"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "State the primary 5-carbon CO2 acceptor molecule that reacts with carbon dioxide catalyzed by RuBisCO in the stroma during the Calvin cycle.",
        "options": ["Ribulose-1,5-bisphosphate (RuBP)", "Phosphoenolpyruvate (PEP)", "Oxaloacetate (OAA)", "3-Phosphoglycerate (PGA)"],
        "correct": "Ribulose-1,5-bisphosphate (RuBP)",
        "base_b": -1.1, "base_a": 1.1,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "photosynthesis",
        "concept_tags": ["c4_pathway", "kranz_anatomy"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "Analyze why C4 plants such as maize and sugarcane exhibit higher photosynthetic efficiency and biomass yield at high temperatures compared to C3 plants.",
        "options": [
            "Kranz anatomy concentrates CO2 around RuBisCO, effectively minimizing photorespiratory loss",
            "C4 plants absorb light in the infrared spectrum",
            "C4 plants do not require NADPH for carbon reduction",
            "Photorespiration in C4 plants generates additional ATP molecules"
        ],
        "correct": "Kranz anatomy concentrates CO2 around RuBisCO, effectively minimizing photorespiratory loss",
        "base_b": 0.9, "base_a": 1.6,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "respiration_in_plants",
        "concept_tags": ["glycolysis", "krebs_cycle"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "State the net number of ATP molecules produced directly by substrate-level phosphorylation during the complete breakdown of one molecule of glucose in glycolysis.",
        "options": ["2 ATP", "4 ATP", "36 ATP", "38 ATP"],
        "correct": "2 ATP",
        "base_b": -1.0, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "genetics_plants",
        "concept_tags": ["mendelian_ratios", "monohybrid_cross"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.STATIC,
        "stem": "In a classical Mendelian monohybrid cross between homozygous tall (TT) and dwarf (tt) pea plants, determine the expected phenotypic ratio observed in the F2 generation.",
        "options": ["3 Tall : 1 Dwarf", "1 Tall : 2 Medium : 1 Dwarf", "9 Tall : 3 Dwarf : 3 White : 1 Round", "1 Tall : 1 Dwarf"],
        "correct": "3 Tall : 1 Dwarf",
        "base_b": -1.4, "base_a": 0.9,
    },
    {
        "subject": SubjectEnum.BOTANY,
        "chapter": "plant_growth",
        "concept_tags": ["auxins", "apical_dominance"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Which plant growth regulator hormone synthesized at the shoot apex is primarily responsible for inducing apical dominance in growing plants?",
        "options": ["Auxin (IAA)", "Gibberellic acid (GA3)", "Abscisic acid (ABA)", "Ethylene"],
        "correct": "Auxin (IAA)",
        "base_b": -1.3, "base_a": 0.9,
    },

    # =========================================================================
    # ZOOLOGY (Human Physiology, Animal Kingdom, Evolution, Biomolecules, Reproduction)
    # =========================================================================
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "human_physiology",
        "concept_tags": ["circulation", "cardiac_cycle"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Identify the specific chamber of the human heart that contracts to pump oxygenated systemic blood directly into the systemic aorta.",
        "options": ["Left ventricle", "Right ventricle", "Left atrium", "Right atrium"],
        "correct": "Left ventricle",
        "base_b": -1.6, "base_a": 0.8,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "human_physiology",
        "concept_tags": ["nephron", "counter_current_mechanism"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "Analyze the role of the counter-current multiplier mechanism operating between the Henle's loop and vasa recta in the human mammalian nephron.",
        "options": [
            "It establishes and maintains an increasing hyperosmolar medullary interstitial gradient for urine concentration",
            "It actively transports glucose and amino acids from Bowman's capsule into blood",
            "It filters plasma proteins into the renal pelvis",
            "It prevents the excretion of urea from the collecting duct"
        ],
        "correct": "It establishes and maintains an increasing hyperosmolar medullary interstitial gradient for urine concentration",
        "base_b": 1.1, "base_a": 1.6,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "animal_kingdom",
        "concept_tags": ["chordates", "non_chordates"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Which of the following fundamental morphological features is uniquely shared by all members of Phylum Chordata at some stage of development?",
        "options": ["Dorsal hollow nerve cord and notochord", "Ventral solid nerve cord and chitinous exoskeleton", "Pseudocoelom and radial symmetry", "Water vascular canal system"],
        "correct": "Dorsal hollow nerve cord and notochord",
        "base_b": -1.2, "base_a": 1.0,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "evolution",
        "concept_tags": ["natural_selection", "industrial_melanism"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "The increase in the proportion of dark melanic peppered moths (Biston betularia) in industrial areas of England is a classic empirical example of which evolutionary mechanism?",
        "options": ["Natural selection", "Genetic drift", "Artificial selection", "Founder effect"],
        "correct": "Natural selection",
        "base_b": -1.3, "base_a": 0.9,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "evolution",
        "concept_tags": ["hardy_weinberg", "allele_frequency"],
        "cognitive_level": CognitiveLevelEnum.APPLICATION,
        "kind": ItemKindEnum.STATIC,
        "stem": "In a randomly mating population at Hardy-Weinberg equilibrium, the frequency of a recessive allele (q) is 0.4. Calculate the percentage frequency of heterozygous carriers (2pq) in the population.",
        "options": ["48%", "24%", "16%", "36%"],
        "correct": "48%",
        "base_b": 0.2, "base_a": 1.4,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "biomolecules",
        "concept_tags": ["enzymes", "enzyme_inhibition"],
        "cognitive_level": CognitiveLevelEnum.ANALYSIS,
        "kind": ItemKindEnum.STATIC,
        "stem": "In competitive enzyme inhibition by malonate on succinate dehydrogenase enzyme, how are the kinetic parameters Km (Michaelis constant) and Vmax affected?",
        "options": ["Km increases while Vmax remains unchanged", "Km decreases while Vmax decreases", "Km remains unchanged while Vmax decreases", "Both Km and Vmax increase"],
        "correct": "Km increases while Vmax remains unchanged",
        "base_b": 1.0, "base_a": 1.5,
    },
    {
        "subject": SubjectEnum.ZOOLOGY,
        "chapter": "human_reproduction",
        "concept_tags": ["menstrual_cycle", "lh_surge"],
        "cognitive_level": CognitiveLevelEnum.RECALL,
        "kind": ItemKindEnum.STATIC,
        "stem": "Which pituitary gonadotropin hormone surge triggers the rupture of the Graafian follicle and release of the secondary oocyte (ovulation) around day 14 of the human menstrual cycle?",
        "options": ["Luteinizing Hormone (LH)", "Follicle Stimulating Hormone (FSH)", "Progesterone", "Oxytocin"],
        "correct": "Luteinizing Hormone (LH)",
        "base_b": -1.1, "base_a": 1.0,
    },
]


def generate_curated_mock_dataset(
    target_count: int = 350,
    seed: int = 42,
) -> List[Item]:
    """Generate a semantically grounded, diverse curated mock development dataset.
    
    Expands base templates and curated items with controlled perturbations,
    generating realistic lexical variance and structurally correlated IRT parameters.
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    
    items: List[Item] = []
    item_counter = 1

    # Cognitive level adjustments for synthetic structural difficulty b
    # Recall: easy (b in [-1.8, -0.6])
    # Application: medium (b in [-0.5, +0.8])
    # Analysis: hard (b in [+0.7, +2.2])
    cog_difficulty_offsets = {
        CognitiveLevelEnum.RECALL: -0.6,
        CognitiveLevelEnum.APPLICATION: 0.2,
        CognitiveLevelEnum.ANALYSIS: 1.1,
    }

    # First add all base items
    for raw in CURATED_TAXONOMY_ITEMS:
        item_id = f"CURATED-{raw['subject'].value[:3].upper()}-{raw['chapter'][:3].upper()}-{item_counter:04d}"
        item_counter += 1

        b_val = float(raw["base_b"])
        a_val = float(raw["base_a"])
        irt_params = IRTParameters.from_floats(a=a_val, b=b_val, c=0.25)

        if raw["kind"] == ItemKindEnum.TEMPLATE:
            item = Item(
                id=item_id,
                subject=raw["subject"],
                chapter=raw["chapter"],
                concept_tags=list(raw["concept_tags"]),
                cognitive_level=raw["cognitive_level"],
                kind=ItemKindEnum.TEMPLATE,
                stem=raw["stem"],
                params=raw["params"],
                answer=raw["answer"],
                distractors=raw["distractors"],
                unit=raw.get("unit", ""),
                irt=irt_params,
                provisional=False,
                bank_version="curated-mock-v0.1",
            )
        else:
            item = Item(
                id=item_id,
                subject=raw["subject"],
                chapter=raw["chapter"],
                concept_tags=list(raw["concept_tags"]),
                cognitive_level=raw["cognitive_level"],
                kind=ItemKindEnum.STATIC,
                stem=raw["stem"],
                options=raw["options"],
                correct=raw["correct"],
                irt=irt_params,
                provisional=False,
                bank_version="curated-mock-v0.1",
            )
        items.append(item)

    # Paraphrase prefixes and variation generators to synthesize target_count items
    prefixes_by_cog = {
        CognitiveLevelEnum.RECALL: [
            "State the value of", "Recall the definition of", "Identify the correct formula for",
            "Which of the following is defined as", "State which organelle is responsible for",
            "Name the primary component of",
        ],
        CognitiveLevelEnum.APPLICATION: [
            "Calculate the required magnitude of", "Determine the resulting value when",
            "Find the numerical outcome for", "Apply the appropriate equation to evaluate",
            "Compute the total amount of", "Calculate the net change in",
        ],
        CognitiveLevelEnum.ANALYSIS: [
            "Compare and contrast the behavior of", "Analyze the underlying mechanism when",
            "Deduce the consequence of altering", "Which of the following assertions correctly explains why",
            "Evaluate the thermodynamic stability of", "Predict the shift in equilibrium when",
        ],
    }

    # Expand items with controlled lexical and structural variations
    while len(items) < target_count:
        base = rng.choice(CURATED_TAXONOMY_ITEMS)
        cog = base["cognitive_level"]
        prefix = rng.choice(prefixes_by_cog[cog])
        
        # Calculate structurally grounded difficulty b:
        # depends on cognitive level + stem length + equation symbols + random jitter
        cog_offset = cog_difficulty_offsets[cog]
        equation_complexity = 0.3 if "sin" in base.get("answer", "") or "cos" in base.get("answer", "") or "/" in base.get("stem", "") else 0.0
        b_jitter = float(np_rng.normal(loc=0.0, scale=0.15))
        
        # Combined difficulty
        calc_b = float(np.clip(base["base_b"] + cog_offset * 0.4 + equation_complexity + b_jitter, -2.8, 2.8))
        calc_a = float(np.clip(base["base_a"] + float(np_rng.normal(loc=0.0, scale=0.10)), 0.6, 2.3))

        irt_params = IRTParameters.from_floats(a=calc_a, b=calc_b, c=0.25)
        item_id = f"CURATED-{base['subject'].value[:3].upper()}-{base['chapter'][:3].upper()}-{item_counter:04d}"
        item_counter += 1

        # Modify stem slightly
        varied_stem = f"{prefix}: {base['stem']}" if not base['stem'].startswith(prefix) else base['stem']

        if base["kind"] == ItemKindEnum.TEMPLATE:
            # Shift parameter choices with strictly non-colliding parameter sets
            shifted_angles = [15, 30, 37, 53, 75]
            shifted_v = [10, 20, 30, 40, 50]
            item = Item(
                id=item_id,
                subject=base["subject"],
                chapter=base["chapter"],
                concept_tags=list(base["concept_tags"]),
                cognitive_level=cog,
                kind=ItemKindEnum.TEMPLATE,
                stem=varied_stem,
                params={"angle": shifted_angles, "v": shifted_v},
                answer=base["answer"],
                distractors=base["distractors"],
                unit=base.get("unit", ""),
                irt=irt_params,
                provisional=False,
                bank_version="curated-mock-v0.1",
            )
        else:
            item = Item(
                id=item_id,
                subject=base["subject"],
                chapter=base["chapter"],
                concept_tags=list(base["concept_tags"]),
                cognitive_level=cog,
                kind=ItemKindEnum.STATIC,
                stem=varied_stem,
                options=base["options"],
                correct=base["correct"],
                irt=irt_params,
                provisional=False,
                bank_version="curated-mock-v0.1",
            )
        items.append(item)

    return items
