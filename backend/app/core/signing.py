"""
Server-side signing authority for the exam timer.
Provides signed drift correction timestamps to prevent local clock manipulation.
"""
import datetime
from cryptography.hazmat.primitives.asymmetric import ed25519

class TimerSigner:
    def __init__(self):
        # Generate an ephemeral Ed25519 key for signing timestamps during this session run.
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

    def sign_time(self) -> tuple[str, str]:
        """Returns (iso_timestamp, hex_signature)."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        signature = self._private_key.sign(now_iso.encode("utf-8"))
        return now_iso, signature.hex()

    def verify_time(self, iso_timestamp: str, hex_signature: str) -> bool:
        """Verifies a signed timestamp returned by the client."""
        try:
            signature = bytes.fromhex(hex_signature)
            self._public_key.verify(signature, iso_timestamp.encode("utf-8"))
            return True
        except Exception:
            return False

# Global signer instance for the server session
timer_signer = TimerSigner()
