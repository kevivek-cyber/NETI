import json
import sys
from pathlib import Path

# Add backend to path so we can import from app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.bank.encryption import encrypt_item

# Fixed keys for development/testing
BANK_MASTER_KEY = b"BANK_MASTER_KEY_32_BYTES_0000000"
ANSWER_MASTER_KEY = b"ANSWER_MASTER_KEY_32_BYTES_00000"

def main():
    bank_path = Path(__file__).resolve().parent.parent / "backend" / "app" / "bank" / "sample_bank.json"
    
    with open(bank_path, "r", encoding="utf-8") as f:
        bank = json.load(f)
        
    encrypted_items = []
    for item in bank.get("items", []):
        encrypted_items.append(encrypt_item(item, BANK_MASTER_KEY, ANSWER_MASTER_KEY))
        
    bank["items"] = encrypted_items
    
    with open(bank_path, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2)
        
    print(f"Successfully encrypted {len(encrypted_items)} items in {bank_path.name}")
    print(f"Bank Key: {BANK_MASTER_KEY.hex()}")
    print(f"Answer Key: {ANSWER_MASTER_KEY.hex()}")

if __name__ == "__main__":
    main()
