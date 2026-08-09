import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from backend.tests.test_encryption import test_encryption_roundtrip, test_decryption_fails_with_wrong_key, test_decryption_fails_if_tampered

try:
    test_encryption_roundtrip()
    test_decryption_fails_with_wrong_key()
    test_decryption_fails_if_tampered()
    print("All tests passed successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
