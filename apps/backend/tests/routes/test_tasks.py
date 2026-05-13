"""
test_tasks.py — Phase 7.2: Tests for the Tasks routes.

Covers:
- POST /tasks → creates task + run (201)
- POST /tasks with parent_run_id → reuses task, creates child run
- POST /tasks with non-existent repo → 404
- POST /tasks with non-succeeded parent → 422
- GET /tasks → list current user's tasks
- GET /tasks/{id} → returns single task
- GET /tasks/{id} → 404 for other user's task
"""

import uuid


# ---------------------------------------------------------------------------
# POST /tasks — Normal flow
# ---------------------------------------------------------------------------


def test_create_task_normal(client, repository):
    """POST /tasks creates a task + agent run and returns 201."""
    response = client.post(
        "/tasks/",
        json={
            "repository_id": str(repository.id),
            "instruction": "Fix the login bug",
            "target_branch": "main",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert data["model_id"] == "anthropic/claude-sonnet-4.6"
    assert data["parent_run_id"] is None
    assert data["follow_up_instruction"] is None


def test_create_task_repo_not_found(client):
    """POST /tasks with a non-existent repository returns 404."""
    fake_repo_id = str(uuid.uuid4())
    response = client.post(
        "/tasks/",
        json={
            "repository_id": fake_repo_id,
            "instruction": "Do something",
            "target_branch": "main",
        },
    )
    assert response.status_code == 404
    assert "Repository not found" in response.json()["detail"]


def test_create_task_other_users_repo(client, other_repository):
    """POST /tasks with another user's repo returns 404."""
    response = client.post(
        "/tasks/",
        json={
            "repository_id": str(other_repository.id),
            "instruction": "Do something",
            "target_branch": "main",
        },
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks — Follow-up flow
# ---------------------------------------------------------------------------


def test_create_task_followup(client, repository, succeeded_agent_run):
    """POST /tasks with parent_run_id reuses task, creates child run with 201."""
    response = client.post(
        "/tasks/",
        json={
            "repository_id": str(repository.id),
            "instruction": "Now also fix the tests",
            "target_branch": "main",
            "parent_run_id": str(succeeded_agent_run.id),
            "follow_up_instruction": "Also fix tests",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["task_id"] == str(succeeded_agent_run.task_id)
    assert data["parent_run_id"] == str(succeeded_agent_run.id)
    assert data["branch_name"] == succeeded_agent_run.branch_name


def test_create_task_followup_non_succeeded_parent(client, repository, agent_run):
    """POST /tasks with a parent that isn't succeeded returns 422."""
    response = client.post(
        "/tasks/",
        json={
            "repository_id": str(repository.id),
            "instruction": "Follow up",
            "target_branch": "main",
            "parent_run_id": str(agent_run.id),
        },
    )
    assert response.status_code == 422
    assert "succeeded" in response.json()["detail"].lower()


def test_create_task_followup_nonexistent_parent(client, repository):
    """POST /tasks with a non-existent parent_run_id returns 404."""
    response = client.post(
        "/tasks/",
        json={
            "repository_id": str(repository.id),
            "instruction": "Follow up",
            "target_branch": "main",
            "parent_run_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404
    assert "Parent agent run not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------


def test_list_tasks(client, task):
    """GET /tasks returns the user's tasks."""
    response = client.get("/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["id"] == str(task.id)


def test_list_tasks_empty(client):
    """GET /tasks returns empty list when user has no tasks."""
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_with_limit(client, session, test_user, repository):
    """GET /tasks respects the limit query parameter."""
    import datetime

    from src.models.task import Task

    # Create 5 tasks
    for i in range(5):
        t = Task(
            id=uuid.uuid4(),
            user_id=test_user.id,
            repository_id=repository.id,
            title=f"Task {i}",
            instruction=f"Instruction {i}",
            target_branch="main",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(t)
    session.commit()

    response = client.get("/tasks/?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


# ---------------------------------------------------------------------------
# GET /tasks/{task_id}
# ---------------------------------------------------------------------------


def test_get_task(client, task):
    """GET /tasks/{id} returns the task."""
    response = client.get(f"/tasks/{task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(task.id)
    assert data["title"] == task.title
    assert data["instruction"] == task.instruction


def test_get_task_not_found(client):
    """GET /tasks/{id} with non-existent ID returns 404."""
    response = client.get(f"/tasks/{uuid.uuid4()}")
    assert response.status_code == 404


def test_get_task_other_users_task(client, other_task):
    """GET /tasks/{id} for another user's task returns 404."""
    response = client.get(f"/tasks/{other_task.id}")
    assert response.status_code == 404
