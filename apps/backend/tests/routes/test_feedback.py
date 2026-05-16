"""
test_feedback.py — Phase 7.4: Tests for the Feedback route.

Covers:
- POST /agent_runs/{id}/feedback with succeeded parent → 201, new child run
- POST /agent_runs/{id}/feedback with non-succeeded parent → 409
- POST /agent_runs/{id}/feedback with non-existent parent → 404
- POST /agent_runs/{id}/feedback with other user's run → 404
"""

import datetime
import uuid

from src.models.agent_run import AgentRun
from src.models.enums import RunStatus


# ---------------------------------------------------------------------------
# POST /agent_runs/{id}/feedback — Happy path
# ---------------------------------------------------------------------------


def test_submit_feedback_succeeded_parent(client, agent_run_with_extras):
    """POST /agent_runs/{id}/feedback creates a new child run (201)."""
    response = client.post(
        f"/agent_runs/{agent_run_with_extras.id}/feedback",
        json={"instruction": "Also fix the edge cases"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert data["parent_run_id"] == str(agent_run_with_extras.id)
    assert data["task_id"] == str(agent_run_with_extras.task_id)
    assert data["follow_up_instruction"] == "Also fix the edge cases"
    assert data["branch_name"] == agent_run_with_extras.branch_name
    assert data["model_id"] == agent_run_with_extras.model_id


def test_submit_feedback_nested_followup_uses_ancestor_pr(
    client, session, agent_run_with_extras
):
    """POST /agent_runs/{id}/feedback accepts a succeeded child run whose PR is on an ancestor."""
    child = AgentRun(
        id=uuid.uuid4(),
        task_id=agent_run_with_extras.task_id,
        parent_run_id=agent_run_with_extras.id,
        status=RunStatus.succeeded,
        branch_name=agent_run_with_extras.branch_name,
        model_id=agent_run_with_extras.model_id,
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(child)
    session.commit()

    response = client.post(
        f"/agent_runs/{child.id}/feedback",
        json={"instruction": "One more refinement"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["parent_run_id"] == str(child.id)
    assert data["branch_name"] == agent_run_with_extras.branch_name


# ---------------------------------------------------------------------------
# POST /agent_runs/{id}/feedback — Error paths
# ---------------------------------------------------------------------------


def test_submit_feedback_non_succeeded_parent(client, agent_run):
    """POST /agent_runs/{id}/feedback with a queued parent returns 409."""
    response = client.post(
        f"/agent_runs/{agent_run.id}/feedback",
        json={"instruction": "Try again"},
    )
    assert response.status_code == 409
    assert "succeeded" in response.json()["detail"].lower()


def test_submit_feedback_succeeded_parent_without_pr_returns_409(
    client, succeeded_agent_run
):
    """POST /agent_runs/{id}/feedback requires an existing open PR."""
    response = client.post(
        f"/agent_runs/{succeeded_agent_run.id}/feedback",
        json={"instruction": "Try again"},
    )
    assert response.status_code == 409
    assert "pull request" in response.json()["detail"].lower()


def test_submit_feedback_blocks_concurrent_followup(
    client, session, agent_run_with_extras
):
    """POST /agent_runs/{id}/feedback rejects a branch with an active follow-up."""
    active_child = AgentRun(
        id=uuid.uuid4(),
        task_id=agent_run_with_extras.task_id,
        parent_run_id=agent_run_with_extras.id,
        status=RunStatus.running,
        branch_name=agent_run_with_extras.branch_name,
        model_id=agent_run_with_extras.model_id,
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(active_child)
    session.commit()

    response = client.post(
        f"/agent_runs/{agent_run_with_extras.id}/feedback",
        json={"instruction": "Try again"},
    )

    assert response.status_code == 409
    assert "already queued or running" in response.json()["detail"].lower()


def test_submit_feedback_not_found(client):
    """POST /agent_runs/{id}/feedback with non-existent run returns 404."""
    response = client.post(
        f"/agent_runs/{uuid.uuid4()}/feedback",
        json={"instruction": "Hello"},
    )
    assert response.status_code == 404


def test_submit_feedback_other_users_run(client, session, other_task):
    """POST /agent_runs/{id}/feedback for another user's run returns 404."""
    other_run = AgentRun(
        id=uuid.uuid4(),
        task_id=other_task.id,
        status=RunStatus.succeeded,
        model_id="test-model",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(other_run)
    session.commit()

    response = client.post(
        f"/agent_runs/{other_run.id}/feedback",
        json={"instruction": "Sneaky"},
    )
    assert response.status_code == 404


def test_submit_feedback_empty_instruction(client, succeeded_agent_run):
    """POST /agent_runs/{id}/feedback with empty instruction returns 422."""
    response = client.post(
        f"/agent_runs/{succeeded_agent_run.id}/feedback",
        json={"instruction": ""},
    )
    assert response.status_code == 422


def test_submit_feedback_whitespace_only_instruction(client, succeeded_agent_run):
    """POST /agent_runs/{id}/feedback with whitespace-only instruction returns 422."""
    response = client.post(
        f"/agent_runs/{succeeded_agent_run.id}/feedback",
        json={"instruction": "   "},
    )
    assert response.status_code == 422
