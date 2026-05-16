from src.core.redaction import redact_value


def test_redacts_sensitive_env_values(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_this_is_a_long_fake_secret")

    payload = {"output": "token=ghp_this_is_a_long_fake_secret"}

    assert redact_value(payload) == {"output": "token=[REDACTED]"}


def test_redacts_sensitive_dict_keys():
    payload = {
        "tool_output": {
            "github_token": "ghp_this_is_a_long_fake_secret",
            "message": "safe",
        }
    }

    assert redact_value(payload) == {
        "tool_output": {"github_token": "[REDACTED]", "message": "safe"}
    }


def test_does_not_redact_safe_github_metadata_keys():
    payload = {"github_pr_number": 42, "github_pr_id": 1234}

    assert redact_value(payload) == payload


def test_redacts_credentials_in_urls():
    payload = {"output": "https://token:secret@example.com/repo.git"}

    assert redact_value(payload) == {"output": "https://[REDACTED]@example.com/repo.git"}
