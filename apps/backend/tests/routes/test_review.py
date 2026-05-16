"""
test_review.py — Tests for the auto-review multiagent feature.

Covers:
- GET /agent_runs/{id}/review → 404 when no reviewer run exists
- GET /agent_runs/{id}/review → 404 when run belongs to another user
- GET /agent_runs/{id}/review → 200 with reviewer run + findings
- GET /agent_runs/{id}/review → fix_run_id present when fixer run exists
- GET /agent_runs/{id} → includes run_role and reviewer_run_id fields
- run_review() → parses LLM JSON output into findings list
- run_review() → handles malformed LLM output gracefully
"""

import datetime
import uuid
from unittest.mock import MagicMock, patch

import pytest

# Import reviewer module at collection time so patch() can resolve the target path
import src.ai.reviewer  # noqa: F401
from src.ai.reviewer import run_review
from src.models.agent_run import AgentRun
from src.models.agent_run_event import AgentRunEvent
from src.models.enums import EventType, RunRole, RunStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(name="developer_run_with_reviewer")
def fixture_developer_run_with_reviewer(session, task, repository):
    """A succeeded developer run that has a linked reviewer run with two findings."""
    # Developer run
    dev_run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        run_role=RunRole.developer,
        branch_name="patch/task-abc",
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(dev_run)
    session.flush()

    # Reviewer run
    reviewer_run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        run_role=RunRole.reviewer,
        parent_run_id=dev_run.id,
        model_id="reviewer-model",
        prompt_version="reviewer-v1",
        max_turns=1,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(reviewer_run)
    session.flush()

    # Link reviewer back to developer run
    dev_run.reviewer_run_id = reviewer_run.id
    session.add(dev_run)
    session.flush()

    # Two review_finding events
    findings = [
        {
            "file_path": "src/auth.py",
            "severity": "critical",
            "category": "security",
            "issue": "user_id is not validated",
            "suggestion": "Add isinstance(user_id, int) check",
        },
        {
            "file_path": "src/routes/tasks.py",
            "severity": "high",
            "category": "correctness",
            "issue": "No rate limiting on POST /tasks",
            "suggestion": "Enforce daily_run_quota before creating a run",
        },
    ]
    for seq, finding in enumerate(findings):
        session.add(
            AgentRunEvent(
                id=uuid.uuid4(),
                agent_run_id=reviewer_run.id,
                sequence=seq,
                event_type=EventType.review_finding,
                payload=finding,
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
        )

    session.commit()
    session.refresh(dev_run)
    return dev_run, reviewer_run


@pytest.fixture(name="developer_run_with_fixer")
def fixture_developer_run_with_fixer(session, task, developer_run_with_reviewer):
    """Extends the above fixture with a fixer run linked to the developer run."""
    dev_run, reviewer_run = developer_run_with_reviewer

    fixer_run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.queued,
        run_role=RunRole.fixer,
        parent_run_id=dev_run.id,
        follow_up_instruction="Fix the critical issue in src/auth.py",
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(fixer_run)
    session.commit()
    session.refresh(fixer_run)
    return dev_run, reviewer_run, fixer_run


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}/review — 404 cases
# ---------------------------------------------------------------------------


def test_review_404_no_reviewer_run(client, agent_run):
    """Returns 404 when the developer run has no reviewer run yet."""
    response = client.get(f"/agent_runs/{agent_run.id}/review")
    assert response.status_code == 404
    assert "No review available yet" in response.json()["detail"]


def test_review_404_nonexistent_run(client):
    """Returns 404 for a completely unknown run id."""
    response = client.get(f"/agent_runs/{uuid.uuid4()}/review")
    assert response.status_code == 404


def test_review_404_other_user_run(client, session, other_task):
    """Returns 404 when the run belongs to a different user (ownership isolation)."""
    other_run = AgentRun(
        id=uuid.uuid4(),
        task_id=other_task.id,
        status=RunStatus.succeeded,
        run_role=RunRole.developer,
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(other_run)
    session.commit()
    response = client.get(f"/agent_runs/{other_run.id}/review")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /agent_runs/{id}/review — 200 cases
# ---------------------------------------------------------------------------


def test_review_returns_findings(client, developer_run_with_reviewer):
    """Returns reviewer run status and all findings."""
    dev_run, reviewer_run = developer_run_with_reviewer
    response = client.get(f"/agent_runs/{dev_run.id}/review")
    assert response.status_code == 200

    data = response.json()
    assert data["reviewer_run_id"] == str(reviewer_run.id)
    assert data["status"] == "succeeded"
    assert len(data["findings"]) == 2
    assert data["fix_run_id"] is None

    critical = next(f for f in data["findings"] if f["severity"] == "critical")
    assert critical["file_path"] == "src/auth.py"
    assert critical["category"] == "security"
    assert "user_id" in critical["issue"]
    assert "isinstance" in critical["suggestion"]


def test_review_includes_fix_run_id(client, developer_run_with_fixer):
    """Returns the fixer run id when an auto-fix was dispatched."""
    dev_run, reviewer_run, fixer_run = developer_run_with_fixer
    response = client.get(f"/agent_runs/{dev_run.id}/review")
    assert response.status_code == 200

    data = response.json()
    assert data["fix_run_id"] == str(fixer_run.id)


def test_review_empty_findings(client, session, task):
    """Returns empty findings list when reviewer found no issues."""
    dev_run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        run_role=RunRole.developer,
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(dev_run)
    session.flush()

    reviewer_run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        run_role=RunRole.reviewer,
        parent_run_id=dev_run.id,
        model_id="reviewer-model",
        prompt_version="reviewer-v1",
        max_turns=1,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(reviewer_run)
    session.flush()
    dev_run.reviewer_run_id = reviewer_run.id
    session.commit()

    response = client.get(f"/agent_runs/{dev_run.id}/review")
    assert response.status_code == 200
    data = response.json()
    assert data["findings"] == []
    assert data["fix_run_id"] is None


# ---------------------------------------------------------------------------
# GET /agent_runs/{id} — run_role and reviewer_run_id fields
# ---------------------------------------------------------------------------


def test_agent_run_includes_run_role(client, agent_run):
    """GET /agent_runs/{id} includes run_role defaulting to 'developer'."""
    response = client.get(f"/agent_runs/{agent_run.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["run_role"] == "developer"
    assert data["reviewer_run_id"] is None


def test_agent_run_includes_reviewer_run_id(client, developer_run_with_reviewer):
    """GET /agent_runs/{id} exposes reviewer_run_id when linked."""
    dev_run, reviewer_run = developer_run_with_reviewer
    response = client.get(f"/agent_runs/{dev_run.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["reviewer_run_id"] == str(reviewer_run.id)
    assert data["run_role"] == "developer"


# ---------------------------------------------------------------------------
# run_review() — unit tests (no DB, no HTTP)
# ---------------------------------------------------------------------------


def test_run_review_parses_valid_json():
    """run_review() returns findings when the LLM produces valid JSON."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """{
        "findings": [
            {
                "file_path": "app.py",
                "severity": "high",
                "category": "correctness",
                "issue": "Division by zero possible",
                "suggestion": "Add a check for zero before dividing"
            }
        ]
    }"""

    with patch("src.ai.reviewer.litellm.completion", return_value=mock_response):
        findings = run_review("--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n+x = 1/y", "Fix division")

    assert len(findings) == 1
    assert findings[0]["severity"] == "high"
    assert findings[0]["file_path"] == "app.py"
    assert findings[0]["category"] == "correctness"


def test_run_review_strips_markdown_fences():
    """run_review() handles models that wrap output in ```json ... ``` fences."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = '```json\n{"findings": []}\n```'

    with patch("src.ai.reviewer.litellm.completion", return_value=mock_response):
        findings = run_review("small diff", "Clean PR")

    assert findings == []


def test_run_review_drops_malformed_entries():
    """run_review() silently drops findings missing required keys."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """{
        "findings": [
            {"file_path": "ok.py", "severity": "low", "category": "style",
             "issue": "nitpick", "suggestion": "rename it"},
            {"file_path": "bad.py", "severity": "critical"}
        ]
    }"""

    with patch("src.ai.reviewer.litellm.completion", return_value=mock_response):
        findings = run_review("diff", "PR")

    assert len(findings) == 1
    assert findings[0]["file_path"] == "ok.py"


def test_run_review_returns_empty_on_llm_failure():
    """run_review() returns [] instead of raising when the LLM call fails."""
    with patch("src.ai.reviewer.litellm.completion", side_effect=Exception("network error")):
        findings = run_review("diff", "PR")

    assert findings == []
