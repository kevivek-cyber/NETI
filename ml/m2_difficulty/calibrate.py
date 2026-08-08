"""Batch IRT calibration tool for NETI Item Bank.

Calibrates response data using 3PL IRT estimation, validates convergence,
formats parameters into RFC 8785 fixed-precision strings, and writes out
the calibrated Item Bank container.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from ..dataset.ingest import load_items_from_json, save_items_to_json
from ..dataset.schema import IRTParameters, Item
from .irt import calibrate_3pl_response_matrix


def calibrate_bank_from_responses(
    items_path: Path,
    response_matrix_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    c_fixed: float = 0.25,
) -> Dict[str, Any]:
    """Calibrate bank items given an empirical response matrix."""
    items = load_items_from_json(items_path)
    item_ids = [it.id for it in items]

    if response_matrix_path and response_matrix_path.exists():
        response_matrix = np.load(response_matrix_path)
    else:
        # If no empirical matrix exists, run cold-start proxy calibration
        raise ValueError("A response matrix NumPy array (.npy) is required for empirical calibration")

    result = calibrate_3pl_response_matrix(
        response_matrix=response_matrix,
        item_ids=item_ids,
        c_fixed=c_fixed,
    )

    # Update item objects with calibrated IRT parameters
    calibrated_items: List[Item] = []
    for item, irt_param in zip(items, result.irt_parameters):
        updated_dict = item.model_dump()
        updated_dict["irt"] = {
            "a": irt_param.a,
            "b": irt_param.b,
            "c": irt_param.c,
        }
        updated_dict["provisional"] = not result.converged
        calibrated_items.append(Item.model_validate(updated_dict))

    if output_path is None:
        output_path = items_path

    save_items_to_json(
        items=calibrated_items,
        path=output_path,
        bank_version=f"calibrated-{items[0].bank_version}",
        note=f"3PL calibrated with {response_matrix.shape[0]} students.",
    )

    return result.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch IRT Calibration")
    parser.add_argument("--items-path", type=str, required=True, help="Path to input items JSON")
    parser.add_argument("--responses-path", type=str, required=True, help="Path to response matrix (.npy)")
    parser.add_argument("--output-path", type=str, default=None, help="Path to save calibrated items JSON")
    args = parser.parse_args()

    summary = calibrate_bank_from_responses(
        items_path=Path(args.items_path),
        response_matrix_path=Path(args.responses_path),
        output_path=Path(args.output_path) if args.output_path else None,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
