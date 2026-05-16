import pytest
from pydantic import ValidationError

from src.core.config import Settings


def test_agent_runtime_does_not_require_backend_only_secrets(monkeypatch):
    monkeypatch.delenv("FERNET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    settings = Settings(
        database_url="sqlite://",
        redis_url="redis://localhost:6379/0",
        llm_api_key="test-llm-key",
        patch_runtime="agent",
        _env_file=None,
    )

    assert settings.patch_runtime == "agent"
    assert settings.fernet_key == ""
    assert settings.jwt_secret == ""


def test_backend_runtime_requires_auth_and_encryption_secrets(monkeypatch):
    monkeypatch.delenv("FERNET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    with pytest.raises(ValidationError, match="FERNET_KEY, JWT_SECRET"):
        Settings(
            database_url="sqlite://",
            redis_url="redis://localhost:6379/0",
            llm_api_key="test-llm-key",
            patch_runtime="backend",
            _env_file=None,
        )
