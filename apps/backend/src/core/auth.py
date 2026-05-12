import uuid
from typing import Any

class DummyUser:
    def __init__(self):
        # hardcoded uuid untuk testing, bisa diganti sesuai kebutuhan --- IGNORE ---
        self.id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

def current_user() -> Any:
    """
    STUB: Dependency ini digunakan sementara untuk Stream 2.
    TODO: Akan diganti dengan implementasi asli (JWT/Session) saat Stream 1 di-merge.
    """
    return DummyUser()