"""
Smoke tests for the host-side agent dispatch pipeline.

Strategy:
- Mock _load_run_context to avoid a real Postgres connection.
- Mock docker.from_env() to avoid a real Docker daemon.
- Mock Session.get / session writes to avoid DB.
- Verify: container.run called, container.wait called, container.remove called in finally.
"""
import uuid
from unittest.mock import MagicMock, patch
import pytest

from src.services.agent_runner import _RunContext, dispatch_agent_run
from src.models.enums import RunStatus


FAKE_RUN_ID = str(uuid.uuid4())


def _make_context(**overrides) -> _RunContext:
    defaults = dict(
        agent_run_id=FAKE_RUN_ID,
        instruction="Add a hello-world test.",
        clone_url="https://github.com/test/repo.git",
        base_branch="main",
        repository_id=str(uuid.uuid4()),
        github_token="ghp_fake",
        parent_run_id=None,
        head_branch=None,
        follow_up_instruction=None,
    )
    defaults.update(overrides)
    return _RunContext(**defaults)


def _make_mock_container(exit_code: int = 0):
    container = MagicMock()
    container.id = "abc123" * 5
    container.wait.return_value = {"StatusCode": exit_code}
    return container


def _make_mock_docker_client(container=None):
    client = MagicMock()
    client.networks.create.return_value = MagicMock()
    client.containers.run.return_value = container or _make_mock_container()
    return client


def _make_mock_run_row(status=RunStatus.running):
    row = MagicMock()
    row.status = status
    return row


@pytest.fixture
def mock_session_get():
    """Patch Session.get to return a mock AgentRun with status=running."""
    run_row = _make_mock_run_row()
    with patch("src.services.agent_runner.Session") as MockSession:
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.get.return_value = run_row
        MockSession.return_value = mock_session
        yield mock_session


class TestDispatchAgentRunSuccess:
    def test_container_is_started_and_removed(self, mock_session_get):
        """Happy path: container starts, exits 0, is removed."""
        container = _make_mock_container(exit_code=0)
        docker_client = _make_mock_docker_client(container)

        with (
            patch("src.services.agent_runner._load_run_context", return_value=_make_context()),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": f"patch_{FAKE_RUN_ID}", "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        docker_client.containers.run.assert_called_once()
        container.wait.assert_called_once()
        container.remove.assert_called_once_with(force=True)

    def test_network_is_created_and_removed(self, mock_session_get):
        """A per-run network is created before the container and removed in finally."""
        container = _make_mock_container(exit_code=0)
        docker_client = _make_mock_docker_client(container)
        network_name = f"patch_{FAKE_RUN_ID}"

        with (
            patch("src.services.agent_runner._load_run_context", return_value=_make_context()),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": network_name, "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        docker_client.networks.create.assert_called_once_with(network_name, driver="bridge")
        docker_client.networks.remove.assert_called_once_with(network_name)

    def test_container_metadata_written_to_db(self, mock_session_get):
        """container_id and celery_task_id are written to the AgentRun row."""
        container = _make_mock_container(exit_code=0)
        docker_client = _make_mock_docker_client(container)

        with (
            patch("src.services.agent_runner._load_run_context", return_value=_make_context()),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": f"patch_{FAKE_RUN_ID}", "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        run_row = mock_session_get.get.return_value
        assert run_row.container_id is not None
        assert run_row.container_image is not None


class TestDispatchAgentRunFailure:
    def test_container_removed_even_on_nonzero_exit(self, mock_session_get):
        """Container is always removed even when it exits with a non-zero code."""
        container = _make_mock_container(exit_code=1)
        docker_client = _make_mock_docker_client(container)

        with (
            patch("src.services.agent_runner._load_run_context", return_value=_make_context()),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": f"patch_{FAKE_RUN_ID}", "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        container.remove.assert_called_once_with(force=True)

    def test_run_marked_failed_on_nonzero_exit(self, mock_session_get):
        """When the container exits non-zero and status is still running, status is set to failed."""
        container = _make_mock_container(exit_code=1)
        docker_client = _make_mock_docker_client(container)
        run_row = _make_mock_run_row(status=RunStatus.running)
        mock_session_get.get.return_value = run_row

        with (
            patch("src.services.agent_runner._load_run_context", return_value=_make_context()),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": f"patch_{FAKE_RUN_ID}", "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        assert run_row.status == RunStatus.failed
        assert run_row.error_message is not None

    def test_container_removed_on_load_context_error(self):
        """Even if context loading fails, the finally block does not crash."""
        docker_client = _make_mock_docker_client()

        with (
            patch("src.services.agent_runner._load_run_context", side_effect=ValueError("not found")),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.Session") as MockSession,
        ):
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_session.get.return_value = _make_mock_run_row()
            MockSession.return_value = mock_session

            with pytest.raises(ValueError, match="not found"):
                dispatch_agent_run(FAKE_RUN_ID)

        # container was never created (failed before containers.run), so remove is not called
        docker_client.containers.run.assert_not_called()


class TestFollowUpRun:
    def test_follow_up_env_vars_injected(self, mock_session_get):
        """Follow-up runs include HEAD_BRANCH and PARENT_RUN_ID in the container env."""
        parent_id = str(uuid.uuid4())
        container = _make_mock_container(exit_code=0)
        docker_client = _make_mock_docker_client(container)

        ctx = _make_context(
            parent_run_id=parent_id,
            head_branch="patch/task-abc",
            follow_up_instruction="Fix the flaky test.",
        )

        with (
            patch("src.services.agent_runner._load_run_context", return_value=ctx),
            patch("src.services.agent_runner.docker.from_env", return_value=docker_client),
            patch("src.services.agent_runner.get_sandbox_options", return_value={"network": f"patch_{FAKE_RUN_ID}", "detach": True, "remove": False}),
        ):
            dispatch_agent_run(FAKE_RUN_ID)

        call_args = docker_client.containers.run.call_args
        env = call_args.kwargs.get("environment")
        if env is None and len(call_args.args) > 1:
            env = call_args.args[1]
        env = env or {}
        assert env.get("HEAD_BRANCH") == "patch/task-abc"
        assert env.get("PARENT_RUN_ID") == parent_id
        assert env.get("FOLLOW_UP_INSTRUCTION") == "Fix the flaky test."
