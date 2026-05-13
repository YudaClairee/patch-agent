"""
test_agent_runs.py — Phase 7.3: Tests for Agent Runs routes.

Covers:
- GET /agent_runs/{id} → returns run with tool_calls and pull_request
- GET /agent_runs/{id} → 404 for non-existent or unowned run
- GET /agent_runs/{id}/events → returns ordered events
- GET /agent_runs/{id}/events → 404 for unowned run
- GET /agent_runs/{id}/pull_request → returns PR
- GET /agent_runs/{id}/pull_request → 404 when no PR
- GET /agent_runs/{id}/diff → 501 (credential stub)
"""

import uuid


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}
# ---------------------------------------------------------------------------


def test_get_agent_run(client, agent_run):
    """GET /agent_runs/{id} returns the run."""
    response = client.get(f"/agent_runs/{agent_run.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(agent_run.id)
    assert data["status"] == "queued"
    assert data["model_id"] == "anthropic/claude-sonnet-4.6"


def test_get_agent_run_with_extras(client, agent_run_with_extras):
    """GET /agent_runs/{id} returns run with nested tool_calls and pull_request."""
    response = client.get(f"/agent_runs/{agent_run_with_extras.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(agent_run_with_extras.id)
    assert len(data["tool_calls"]) == 1
    assert data["tool_calls"][0]["tool_name"] == "read_file"
    assert data["pull_request"] is not None
    assert data["pull_request"]["github_pr_number"] == 42


def test_get_agent_run_not_found(client):
    """GET /agent_runs/{id} returns 404 for non-existent ID."""
    response = client.get(f"/agent_runs/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_agent_run_other_user(client, session, other_task):
    """GET /agent_runs/{id} returns 404 for a run owned by another user."""
    import datetime

    from src.models.agent_run import AgentRun
    from src.models.enums import RunStatus

    other_run = AgentRun(
        id=uuid.uuid4(),
        task_id=other_task.id,
        status=RunStatus.queued,
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(other_run)
    session.commit()

    response = client.get(f"/agent_runs/{other_run.id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}/events
# ---------------------------------------------------------------------------


def test_get_agent_run_events(client, agent_run_with_extras):
    """GET /agent_runs/{id}/events returns ordered events."""
    response = client.get(f"/agent_runs/{agent_run_with_extras.id}/events")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Verify ordering by sequence
    sequences = [e["sequence"] for e in data]
    assert sequences == sorted(sequences)


def test_get_agent_run_events_with_limit(client, agent_run_with_extras):
    """GET /agent_runs/{id}/events respects limit parameter."""
    response = client.get(
        f"/agent_runs/{agent_run_with_extras.id}/events?limit=2"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_agent_run_events_not_found(client):
    """GET /agent_runs/{id}/events returns 404 for non-existent run."""
    response = client.get(f"/agent_runs/{uuid.uuid4()}/events")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}/pull_request
# ---------------------------------------------------------------------------


def test_get_pull_request(client, agent_run_with_extras):
    """GET /agent_runs/{id}/pull_request returns the linked PR."""
    response = client.get(
        f"/agent_runs/{agent_run_with_extras.id}/pull_request"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["github_pr_number"] == 42
    assert data["title"] == "Fix the bug"
    assert data["state"] == "open"


def test_get_pull_request_not_found(client, agent_run):
    """GET /agent_runs/{id}/pull_request returns 404 when no PR exists."""
    response = client.get(f"/agent_runs/{agent_run.id}/pull_request")
    assert response.status_code == 404


def test_get_pull_request_run_not_found(client):
    """GET /agent_runs/{id}/pull_request returns 404 for non-existent run."""
    response = client.get(f"/agent_runs/{uuid.uuid4()}/pull_request")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}/diff
# ---------------------------------------------------------------------------


def test_get_diff_returns_501_stub(client, agent_run_with_extras):
    """GET /agent_runs/{id}/diff returns 501 because decrypt_token is a stub."""
    response = client.get(f"/agent_runs/{agent_run_with_extras.id}/diff")
    assert response.status_code == 501
    assert "not integrated" in response.json()["detail"].lower()


def test_get_diff_mocked_github(client, agent_run_with_extras):
    """GET /agent_runs/{id}/diff returns files when GitHub API is mocked."""
    from unittest.mock import patch, MagicMock

    mock_github_response = MagicMock()
    mock_github_response.status_code = 200
    mock_github_response.json.return_value = [
        {
            "filename": "main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "patch": "@@ -1,5 +1,10 @@\n+new line",
        },
        {
            "filename": "tests/test_main.py",
            "status": "added",
            "additions": 20,
            "deletions": 0,
            "patch": None,
        },
    ]

    with patch("src.routes.agent_runs.decrypt_token", return_value="fake-token"):
        with patch("src.routes.agent_runs.httpx.get", return_value=mock_github_response):
            response = client.get(
                f"/agent_runs/{agent_run_with_extras.id}/diff"
            )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["file_path"] == "main.py"
    assert data[0]["status"] == "modified"
    assert data[0]["additions"] == 10
    assert data[1]["file_path"] == "tests/test_main.py"
    assert data[1]["status"] == "added"
    assert data[1]["patch"] is None
