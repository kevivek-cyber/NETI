import sys
from unittest.mock import MagicMock
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.middleware.cors'] = MagicMock()
sys.modules['fastapi.staticfiles'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['cryptography'] = MagicMock()
sys.modules['cryptography.hazmat'] = MagicMock()
sys.modules['cryptography.hazmat.primitives'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.kdf'] = MagicMock()
sys.modules['cryptography.hazmat.primitives.kdf.hkdf'] = MagicMock()

import app.main
print("Loaded app.main")
try:
    print(app.main.open_session("DEMO"))
    
    class Req:
        candidate_id = "NEET-001"
    
    print(app.main.issue_paper(Req()))
except Exception as e:
    import traceback
    traceback.print_exc()
