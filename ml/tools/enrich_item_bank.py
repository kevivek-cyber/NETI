"""Offline Item Bank Enrichment Tool for NETI.

Enriches an Item Bank with authoring-time ML predictions and SymPy validation.
Preserves existing human-approved metadata as authoritative.
Never overwrites the original item bank file.
Produces a deterministic enriched bank container with a SHA-256 commitment hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add repository root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.pipeline import analyze_item

DEFAULT_BANK_PATH = ROOT_DIR / "backend" / "app" / "bank" / "sample_bank.json"
DEFAULT_ENRICHED_OUTPUT = ROOT_DIR / "ml" / "artifacts" / "enriched_banks" / "sample_bank_enriched.json"


def enrich_item_bank(
    input_bank_path: Path = DEFAULT_BANK_PATH,
    output_bank_path: Path = DEFAULT_ENRICHED_OUTPUT,
) -> Dict[str, Any]:
    """Enrich an item bank offline while preserving human metadata authority."""
    if not input_bank_path.exists():
        raise FileNotFoundError(f"Input bank not found at: {input_bank_path}")

    # Safety guard: Never overwrite original bank file
    if output_bank_path.resolve() == input_bank_path.resolve():
        raise ValueError("Safety violation: output_bank_path cannot be identical to input_bank_path")

    raw_bank = json.loads(input_bank_path.read_text(encoding="utf-8"))
    items = raw_bank.get("items", [])
    bank_version = raw_bank.get("bank_version", "unknown")

    enriched_items: List[Dict[str, Any]] = []

    for item in items:
        # 1. Preserve complete original item dictionary
        enriched_item = dict(item)

        # 2. Run authoring-time ML & validation
        analysis = analyze_item(item)

        # 3. Attach under separate 'ml_analysis' field
        enriched_item["ml_analysis"] = {
            "model_version": "m1_tfidf_v0.1+m2_ridge_v0.1",
            "m1": analysis["m1"],
            "m2": analysis["m2"],
            "validation": analysis["validation"],
        }
        enriched_items.append(enriched_item)

    # 4. Construct enriched container
    enriched_container = {
        "bank_version": f"enriched-{bank_version}",
        "original_bank_version": bank_version,
        "note": f"Enriched with authoring-time ML analysis and symbolic verification. Original human metadata preserved.",
        "item_count": len(enriched_items),
        "items": enriched_items,
    }

    # 5. Compute SHA-256 checksum over canonical serialization
    serialized_bytes = json.dumps(enriched_container, sort_keys=True, indent=2).encode("utf-8")
    content_hash = hashlib.sha256(serialized_bytes).hexdigest()
    enriched_container["content_hash"] = content_hash

    # 6. Save to new destination
    output_bank_path.parent.mkdir(parents=True, exist_ok=True)
    output_bank_path.write_bytes(json.dumps(enriched_container, indent=2).encode("utf-8"))

    return {
        "input_bank": str(input_bank_path),
        "output_bank": str(output_bank_path),
        "item_count": len(enriched_items),
        "content_hash": content_hash,
        "enriched_version": enriched_container["bank_version"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich NETI Item Bank Offline")
    parser.add_argument("--input-bank", type=str, default=str(DEFAULT_BANK_PATH), help="Path to input item bank JSON")
    parser.add_argument("--output-bank", type=str, default=str(DEFAULT_ENRICHED_OUTPUT), help="Path to output enriched JSON")
    args = parser.parse_args()

    summary = enrich_item_bank(
        input_bank_path=Path(args.input_bank),
        output_bank_path=Path(args.output_bank),
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
