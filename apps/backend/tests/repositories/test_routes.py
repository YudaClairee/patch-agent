import sys
from unittest.mock import MagicMock, patch

sys.modules['src.models.agent_run'] = MagicMock()

import uuid
from uuid import UUID
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def client(mock_session):
    from src.main import app
    from src.core.database import get_session
    from src.core.auth import current_user

    def _get_session_override():
        yield mock_session

    def _current_user_override():
        mock_user = MagicMock()
        mock_user.id = UUID("550e8400-e29b-41d4-a716-446655440000")
        return mock_user

    app.dependency_overrides[get_session] = _get_session_override
    app.dependency_overrides[current_user] = _current_user_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def test_get_repositories_returns_empty_list(client: TestClient, mock_session: MagicMock):
    mock_exec = MagicMock()
    mock_exec.all.return_value = []
    mock_session.exec.return_value = mock_exec

    response = client.get("/repositories/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_repositories_returns_user_repos(client: TestClient, mock_session: MagicMock):
    fake_repo = MagicMock()
    fake_repo.id = uuid.uuid4()
    fake_repo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    fake_repo.github_owner = "octocat"
    fake_repo.github_repo = "Hello-World"
    fake_repo.github_repo_id = 1296269
    fake_repo.clone_url = "https://github.com/octocat/Hello-World.git"
    fake_repo.default_branch = "main"
    fake_repo.language = "Python"
    fake_repo.created_at = datetime.now(timezone.utc)
    fake_repo.updated_at = datetime.now(timezone.utc)
    
    def exec_side_effect(*args, **kwargs):
        mock_result = MagicMock()
        if not hasattr(exec_side_effect, "called"):
            exec_side_effect.called = True
            mock_result.all.return_value = [fake_repo]
        else:
            mock_result.first.return_value = None
        return mock_result

    mock_session.exec.side_effect = exec_side_effect

    response = client.get("/repositories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "octocat/Hello-World"
    assert data[0]["index_status"] == "not_indexed"


@patch("src.routes.repositories._to_read")
@patch("src.routes.repositories.CodebaseIndex")
@patch("src.routes.repositories.index_repository")
@patch("src.routes.repositories.connect_repo")
def test_post_repositories_returns_201(
    mock_connect: MagicMock,
    mock_index_task: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_to_read: MagicMock,
    client: TestClient,
    mock_session: MagicMock,
):
    fake_repo = MagicMock()
    fake_repo.id = uuid.uuid4()
    fake_repo.default_branch = "main"
    mock_connect.return_value = fake_repo
    mock_index_task.delay = MagicMock()

    mock_to_read.return_value = {
        "id": str(fake_repo.id),
        "github_owner": "octocat",
        "github_repo": "Hello-World",
        "full_name": "octocat/Hello-World",
        "default_branch": "main",
        "language": "Python",
        "index_status": "pending",
        "chunk_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    response = client.post(
        "/repositories/",
        json={"owner": "octocat", "name": "Hello-World"},
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == "octocat/Hello-World"
    mock_index_task.delay.assert_called_once()

@patch("src.routes.repositories.connect_repo")
def test_post_repositories_returns_422_on_invalid_repo(
    mock_connect: MagicMock,
    client: TestClient,
):
    mock_connect.side_effect = ValueError("Not found")
    response = client.post("/repositories/", json={"owner": "octocat", "name": "ghost"})
    assert response.status_code == 422

def test_post_repositories_requires_body_fields(client: TestClient):
    response = client.post("/repositories/", json={})
    assert response.status_code == 422


@patch("src.routes.repositories.disconnect_repo")
def test_delete_repository_returns_204(
    mock_disconnect: MagicMock,
    client: TestClient,
):
    mock_disconnect.return_value = None
    response = client.delete(f"/repositories/{uuid.uuid4()}")
    assert response.status_code == 204

@patch("src.routes.repositories.disconnect_repo")
def test_delete_repository_returns_403_for_non_owner(
    mock_disconnect: MagicMock,
    client: TestClient,
):
    mock_disconnect.side_effect = PermissionError("not authorized")
    response = client.delete(f"/repositories/{uuid.uuid4()}")
    assert response.status_code == 403

@patch("src.routes.repositories.disconnect_repo")
def test_delete_repository_returns_404_not_found(
    mock_disconnect: MagicMock,
    client: TestClient,
):
    mock_disconnect.side_effect = ValueError("Not found")
    response = client.delete(f"/repositories/{uuid.uuid4()}")
    assert response.status_code == 404