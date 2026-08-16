import pytest
from app.core.signing import timer_signer

def test_timer_signer_valid():
    now_iso, sig = timer_signer.sign_time()
    assert timer_signer.verify_time(now_iso, sig) is True

def test_timer_signer_invalid():
    now_iso, sig = timer_signer.sign_time()
    # Tamper with timestamp
    assert timer_signer.verify_time("2025" + now_iso[4:], sig) is False
    # Tamper with signature
    bad_sig = "ff" + sig[2:]
    assert timer_signer.verify_time(now_iso, bad_sig) is False
