import json
import os
from typing import Any
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _derive_key(master_key: bytes, info: bytes) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=info
    )
    return hkdf.derive(master_key)

def encrypt_item(item: dict[str, Any], bank_key: bytes, answer_key: bytes) -> dict[str, Any]:
    """Encrypts a bank item using AES-256-GCM according to CUSTODY.md §3."""
    item_id = item["id"]
    
    # 1. Derive keys per item
    item_key = _derive_key(bank_key, f"neti/item/v1|{item_id}".encode("utf-8"))
    answer_item_key = _derive_key(answer_key, f"neti/answer/v1|{item_id}".encode("utf-8"))
    
    # 2. Extract public vs private fields
    public_keys = {"id", "subject", "chapter", "concept_tags", "kind", "irt"}
    public_data = {k: v for k, v in item.items() if k in public_keys}
    
    # Question fields (stem, options, params, template_options, unit, etc.)
    question_keys = set(item.keys()) - public_keys - {"correct", "correct_template_index"}
    question_data = {k: item[k] for k in question_keys}
    
    # Answer fields
    answer_keys = {"correct", "correct_template_index"}
    answer_data = {k: item[k] for k in answer_keys if k in item}
    
    # 3. Encrypt
    aesgcm_item = AESGCM(item_key)
    nonce_item = os.urandom(12)
    stem_cipher = aesgcm_item.encrypt(nonce_item, json.dumps(question_data).encode("utf-8"), None)
    
    aesgcm_answer = AESGCM(answer_item_key)
    nonce_answer = os.urandom(12)
    solution_cipher = aesgcm_answer.encrypt(nonce_answer, json.dumps(answer_data).encode("utf-8"), None)
    
    # 4. Construct encrypted item
    return {
        **public_data,
        "stem_cipher": nonce_item.hex() + stem_cipher.hex(),
        "solution_cipher": nonce_answer.hex() + solution_cipher.hex()
    }

def decrypt_item(encrypted_item: dict[str, Any], bank_key: bytes, answer_key: bytes | None = None) -> dict[str, Any]:
    """Decrypts a bank item using AES-256-GCM according to CUSTODY.md §3."""
    item_id = encrypted_item["id"]
    
    # 1. Derive keys per item
    item_key = _derive_key(bank_key, f"neti/item/v1|{item_id}".encode("utf-8"))
    
    # 2. Decrypt
    aesgcm_item = AESGCM(item_key)
    stem_hex = encrypted_item["stem_cipher"]
    nonce_item, cipher_item = bytes.fromhex(stem_hex[:24]), bytes.fromhex(stem_hex[24:])
    question_data = json.loads(aesgcm_item.decrypt(nonce_item, cipher_item, None).decode("utf-8"))
    
    answer_data = {}
    if answer_key is not None:
        answer_item_key = _derive_key(answer_key, f"neti/answer/v1|{item_id}".encode("utf-8"))
        aesgcm_answer = AESGCM(answer_item_key)
        sol_hex = encrypted_item["solution_cipher"]
        nonce_answer, cipher_answer = bytes.fromhex(sol_hex[:24]), bytes.fromhex(sol_hex[24:])
        answer_data = json.loads(aesgcm_answer.decrypt(nonce_answer, cipher_answer, None).decode("utf-8"))
    
    # 3. Reconstruct original item
    public_keys = {"id", "subject", "chapter", "concept_tags", "kind", "irt"}
    result = {k: v for k, v in encrypted_item.items() if k in public_keys}
    result.update(question_data)
    result.update(answer_data)
    
    return result
