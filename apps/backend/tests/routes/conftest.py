"""
conftest.py — Phase 7 test fixtures for route-level integration tests.

Uses an in-memory SQLite database so tests run without a real Postgres instance.
All PostgreSQL-specific column types (PG_UUID, JSONB, SAEnum) are mapped to
their SQLite equivalents via SQLAlchemy event hooks at engine creation time.
"""

import datetime
import sqlite3
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy import JSON
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import Uuid as SA_Uuid
from sqlmodel import Session, SQLModel, create_engine

from src.core.auth import current_user
from src.core.database import get_session
from src.main import app
from src.models.agent_run import AgentRun
from src.models.agent_run_event import AgentRunEvent
from src.models.enums import EventType, PRState, RunStatus, ToolCallStatus
from src.models.pull_request import PullRequest
from src.models.repository import Repository
from src.models.task import Task
from src.models.tool_call import ToolCall
from src.models.usage_record import UsageRecord
from src.models.user import User

# Teach sqlite3 how to handle uuid.UUID objects natively.
sqlite3.register_adapter(uuid.UUID, str)

# Ensure all models are registered with SQLModel metadata before create_all.
import src.models  # noqa: F401, E402


# ---------------------------------------------------------------------------
# SQLite compatibility — remap PG-specific types to SQLite-friendly ones
# ---------------------------------------------------------------------------


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID on PG, VARCHAR(36) on other databases.
    Transparently converts between Python uuid.UUID and string storage.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value).hex
            return value.hex
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value
        return value


# Before creating the tables, swap PG-only types to generic ones for SQLite.

@event.listens_for(SQLModel.metadata, "before_create")
def _remap_pg_types_for_sqlite(target, connection, **kw):
    """Walk all columns and replace PG-only types with generic ones for SQLite."""
    if connection.dialect.name != "sqlite":
        return

    for table in target.sorted_tables:
        for column in table.columns:
            col_type = column.type
            if isinstance(col_type, JSONB):
                column.type = JSON()
            elif isinstance(col_type, PG_UUID):
                column.type = GUID()
            elif isinstance(col_type, SA_Uuid):
                column.type = GUID()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OTHER_USER_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture(name="engine")
def fixture_engine():
    """Create a one-off in-memory SQLite engine for the test session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign-key support in SQLite (off by default).
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)

    yield engine
    engine.dispose()


@pytest.fixture(name="session")
def fixture_session(engine):
    """Create a new database session for each test."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def fixture_test_user(session: Session):
    """Seed the primary test user."""
    user = User(
        id=TEST_USER_ID,
        email="test@example.com",
        name="Test User",
        hashed_password="hashed",
        daily_run_quota=15,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="other_user")
def fixture_other_user(session: Session):
    """Seed a second user for ownership isolation tests."""
    user = User(
        id=OTHER_USER_ID,
        email="other@example.com",
        name="Other User",
        hashed_password="hashed",
        daily_run_quota=10,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="repository")
def fixture_repository(session: Session, test_user: User):
    """Seed a repository owned by the test user."""
    repo = Repository(
        id=uuid.uuid4(),
        user_id=test_user.id,
        github_owner="test-owner",
        github_repo="test-repo",
        default_branch="main",
        language="python",
        clone_url="https://github.com/test-owner/test-repo.git",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


@pytest.fixture(name="other_repository")
def fixture_other_repository(session: Session, other_user: User):
    """Seed a repository owned by the other user."""
    repo = Repository(
        id=uuid.uuid4(),
        user_id=other_user.id,
        github_owner="other-owner",
        github_repo="other-repo",
        default_branch="main",
        language="python",
        clone_url="https://github.com/other-owner/other-repo.git",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


@pytest.fixture(name="task")
def fixture_task(session: Session, test_user: User, repository: Repository):
    """Seed a task owned by the test user."""
    t = Task(
        id=uuid.uuid4(),
        user_id=test_user.id,
        repository_id=repository.id,
        title="Fix the bug",
        instruction="Please fix the bug in main.py",
        target_branch="main",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


@pytest.fixture(name="other_task")
def fixture_other_task(session: Session, other_user: User, other_repository: Repository):
    """Seed a task owned by the other user."""
    t = Task(
        id=uuid.uuid4(),
        user_id=other_user.id,
        repository_id=other_repository.id,
        title="Other task",
        instruction="Other user's task",
        target_branch="main",
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


@pytest.fixture(name="agent_run")
def fixture_agent_run(session: Session, task: Task):
    """Seed an agent run linked to the test user's task."""
    run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.queued,
        model_id="anthropic/claude-sonnet-4.6",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


@pytest.fixture(name="succeeded_agent_run")
def fixture_succeeded_agent_run(session: Session, task: Task):
    """Seed a succeeded agent run for follow-up / feedback tests."""
    run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        branch_name="fix/the-bug",
        model_id="anthropic/claude-sonnet-4.6",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


@pytest.fixture(name="agent_run_with_extras")
def fixture_agent_run_with_extras(
    session: Session, task: Task, repository: Repository
):
    """Seed an agent run with tool_calls, events, and a pull_request."""
    run = AgentRun(
        id=uuid.uuid4(),
        task_id=task.id,
        status=RunStatus.succeeded,
        branch_name="fix/the-bug",
        model_id="anthropic/claude-sonnet-4.6",
        prompt_version="v1",
        max_turns=15,
        queued_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(run)
    session.flush()

    # Tool call
    tc = ToolCall(
        id=uuid.uuid4(),
        agent_run_id=run.id,
        sequence=1,
        tool_name="read_file",
        tool_input={"path": "main.py"},
        tool_output={"content": "print('hello')"},
        status=ToolCallStatus.success,
        duration_ms=120,
        started_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(tc)

    # Events
    for i in range(3):
        evt = AgentRunEvent(
            id=uuid.uuid4(),
            agent_run_id=run.id,
            sequence=i + 1,
            event_type=EventType.message,
            payload={"text": f"Event {i + 1}"},
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(evt)

    # Pull request
    pr = PullRequest(
        id=uuid.uuid4(),
        agent_run_id=run.id,
        repository_id=repository.id,
        github_pr_number=42,
        title="Fix the bug",
        body="This PR fixes the bug",
        head_branch="fix/the-bug",
        base_branch="main",
        url="https://github.com/test-owner/test-repo/pull/42",
        state=PRState.open,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        updated_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(pr)

    session.commit()
    session.refresh(run)
    return run


@pytest.fixture(name="usage_record")
def fixture_usage_record(session: Session, test_user: User):
    """Seed a usage record for today."""
    record = UsageRecord(
        id=uuid.uuid4(),
        user_id=test_user.id,
        date=datetime.datetime.now(datetime.timezone.utc).date(),
        run_count=5,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@pytest.fixture(name="client")
def fixture_client(session: Session, test_user: User):
    """
    Create a TestClient that:
    - overrides get_session to use the test SQLite session
    - overrides current_user to return the test user
    - patches enqueue_agent_run to be a no-op (no Celery needed)
    """

    def _override_get_session():
        yield session

    async def _override_current_user():
        return test_user

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[current_user] = _override_current_user

    with patch("src.routes.tasks.enqueue_agent_run"):
        with patch("src.routes.feedback.enqueue_agent_run"):
            with TestClient(app) as tc:
                yield tc

    app.dependency_overrides.clear()
