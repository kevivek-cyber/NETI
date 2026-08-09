from app.bank.encryption import encrypt_item, decrypt_item
import pytest
from cryptography.exceptions import InvalidTag

def test_encryption_roundtrip():
    bank_key = b"A" * 32
    answer_key = b"B" * 32
    
    original_item = {
        "id": "TEST-0001",
        "subject": "test",
        "chapter": "ch1",
        "concept_tags": ["tag1"],
        "kind": "static",
        "irt": {"a": "1.0", "b": "0.0", "c": "0.2"},
        "stem": "What is 2+2?",
        "options": ["3", "4", "5"],
        "correct": "4",
        "answer": "2 + 2",
        "params": {}
    }
    
    encrypted = encrypt_item(original_item, bank_key, answer_key)
    
    # Public fields should remain
    assert encrypted["id"] == "TEST-0001"
    assert encrypted["subject"] == "test"
    
    # Private fields should be removed
    assert "stem" not in encrypted
    assert "correct" not in encrypted
    
    # Ciphertext should exist
    assert "stem_cipher" in encrypted
    assert "solution_cipher" in encrypted
    
    # Decryption should restore original
    decrypted = decrypt_item(encrypted, bank_key, answer_key)
    assert decrypted["stem"] == "What is 2+2?"
    assert decrypted["correct"] == "4"
    assert decrypted["options"] == ["3", "4", "5"]

def test_decryption_fails_with_wrong_key():
    bank_key = b"A" * 32
    answer_key = b"B" * 32
    wrong_key = b"C" * 32
    
    original_item = {
        "id": "TEST-0001",
        "subject": "test",
        "chapter": "ch1",
        "concept_tags": ["tag1"],
        "kind": "static",
        "irt": {},
        "stem": "What is 2+2?",
        "options": ["3", "4", "5"],
        "correct": "4"
    }
    
    encrypted = encrypt_item(original_item, bank_key, answer_key)
    
    with pytest.raises(InvalidTag):
        decrypt_item(encrypted, wrong_key, answer_key)
        
    with pytest.raises(InvalidTag):
        decrypt_item(encrypted, bank_key, wrong_key)

def test_decryption_fails_if_tampered():
    bank_key = b"A" * 32
    answer_key = b"B" * 32
    
    original_item = {
        "id": "TEST-0001",
        "subject": "test",
        "chapter": "ch1",
        "concept_tags": ["tag1"],
        "kind": "static",
        "irt": {},
        "stem": "What is 2+2?",
        "options": ["3", "4", "5"],
        "correct": "4"
    }
    
    encrypted = encrypt_item(original_item, bank_key, answer_key)
    
    # Tamper with cipher (flip last character of hex)
    original_cipher = encrypted["stem_cipher"]
    last_char = '0' if original_cipher[-1] != '0' else '1'
    encrypted["stem_cipher"] = original_cipher[:-1] + last_char
    
    with pytest.raises(InvalidTag):
        decrypt_item(encrypted, bank_key, answer_key)
