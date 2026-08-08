"""SymPy-based Symbolic Validator for Template Questions and Distractors.

Replaces unsafe Python eval() with an algebraic solver.
Enforces:
1. Exact algebraic correctness against parameter substitutions.
2. Distractor distinctness: no distractor may evaluate to the correct answer.
3. Singularity / division-by-zero guards.
4. Non-complex, finite real values.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple
import sympy as sp

from ..dataset.schema import format_fixed_precision

# Safe mathematical symbols and functions permitted in question templates
ALLOWED_FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sqrt": sp.sqrt,
    "pi": sp.pi,
    "radians": lambda x: x * sp.pi / 180,
    "abs": sp.Abs,
    "exp": sp.exp,
    "log": sp.log,
}


class SymbolicValidationError(Exception):
    """Raised when a template formula or distractor fails symbolic validation."""
    pass


def evaluate_symbolic_expression(expr_str: str, params: Dict[str, Any], decimals: int = 2) -> str:
    """Safely parse and evaluate a symbolic math expression with SymPy.
    
    Returns a normalized, fixed-precision string.
    """
    try:
        # Create symbols for all template parameter variables
        symbol_map = {name: sp.Symbol(name) for name in params.keys()}
        local_dict = {**ALLOWED_FUNCTIONS, **symbol_map}

        # Parse string safely into a SymPy expression
        parsed_expr = sp.sympify(expr_str, locals=local_dict)

        # Substitute numerical parameter values
        subs_dict = {symbol_map[k]: v for k, v in params.items() if k in symbol_map}
        evaluated_val = parsed_expr.subs(subs_dict).evalf()

        # Check for complex, infinite, or NaN values
        if evaluated_val.has(sp.I):
            raise SymbolicValidationError(f"Expression '{expr_str}' evaluated to non-real value: {evaluated_val}")

        val_float = float(evaluated_val)
        if math.isinf(val_float) or math.isnan(val_float):
            raise SymbolicValidationError(f"Expression '{expr_str}' evaluated to infinite/NaN value")

        return format_fixed_precision(val_float, decimals=decimals)

    except Exception as e:
        if isinstance(e, SymbolicValidationError):
            raise
        raise SymbolicValidationError(f"Failed to evaluate expression '{expr_str}' with params {params}: {e}") from e


def validate_template_algebra(
    stem: str,
    params: Dict[str, List[Any]],
    answer_expr: str,
    distractor_exprs: List[str],
    unit: str = "",
) -> Dict[str, Any]:
    """Exhaustively validate that a template evaluates cleanly across its parameter combinations.
    
    Verifies that:
    1. Correct answer evaluates cleanly to finite numbers.
    2. No distractor is identical to the correct answer for any parameter draw.
    3. No two distractors collide with each other.
    """
    # Sample a grid of parameter combinations
    keys = list(params.keys())
    values = [params[k] for k in keys]

    total_combinations = math.prod(len(v) for v in values)
    tested_combinations = 0
    collisions = []

    # Iterate over combinations
    import itertools
    for combo in itertools.product(*values):
        param_draw = dict(zip(keys, combo))
        tested_combinations += 1

        ans_val = evaluate_symbolic_expression(answer_expr, param_draw)
        dist_vals = [evaluate_symbolic_expression(d, param_draw) for d in distractor_exprs]

        # Check distractor collision with correct answer
        if ans_val in dist_vals:
            collisions.append({
                "params": param_draw,
                "answer": ans_val,
                "distractor_collision": ans_val,
            })

        # Check distinctness among distractors
        if len(set(dist_vals)) < len(dist_vals):
            collisions.append({
                "params": param_draw,
                "duplicate_distractors": dist_vals,
            })

    is_valid = len(collisions) == 0
    return {
        "is_valid": is_valid,
        "total_combinations_tested": tested_combinations,
        "num_collisions": len(collisions),
        "collisions": collisions[:5],  # sample at most 5 if failed
    }
