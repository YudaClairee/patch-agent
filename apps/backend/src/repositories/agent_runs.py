import uuid
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from src.models.agent_run import AgentRun
from src.models.agent_run_event import AgentRunEvent
from src.models.pull_request import PullRequest
from src.models.enums import RunStatus
from src.schemas.task import TaskCreate


def create_agent_run(session: Session, task_id: uuid.UUID, data: TaskCreate) -> AgentRun:
    """
    Creates a new AgentRun in 'queued' status.
    Inherits branch_name and model_id from parent run if parent_run_id is provided.
    """
    branch_name = None
    model_id = "claude-3-5-sonnet-20241022"  # Default model
    follow_up_instruction = data.follow_up_instruction

    if data.parent_run_id:
        parent_run = session.get(AgentRun, data.parent_run_id)
        if parent_run:
            branch_name = parent_run.branch_name
            model_id = parent_run.model_id
            if not follow_up_instruction:
                follow_up_instruction = data.instruction

    run = AgentRun(
        task_id=task_id,
        status=RunStatus.queued,
        parent_run_id=data.parent_run_id,
        follow_up_instruction=follow_up_instruction,
        branch_name=branch_name,
        model_id=model_id,
        prompt_version="v1",
        max_turns=15,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def get_agent_run(session: Session, run_id: uuid.UUID) -> AgentRun | None:
    """
    Retrieves an agent run by ID, including nested tool calls and pull request.
    """
    statement = (
        select(AgentRun)
        .where(AgentRun.id == run_id)
        .options(
            selectinload(AgentRun.tool_calls),
            selectinload(AgentRun.pull_request),
        )
    )
    return session.exec(statement).first()


def list_events(session: Session, run_id: uuid.UUID) -> list[AgentRunEvent]:
    """
    Lists all events for a run, ordered by sequence.
    """
    statement = (
        select(AgentRunEvent)
        .where(AgentRunEvent.agent_run_id == run_id)
        .order_by(AgentRunEvent.sequence.asc())
    )
    return list(session.exec(statement).all())


def get_pull_request_for_run(session: Session, run_id: uuid.UUID) -> PullRequest | None:
    """
    Finds the PullRequest associated with a run.
    If the run is a follow-up, it walks the parent chain to find the PR.
    """
    current_run_id = run_id
    while current_run_id:
        statement = select(PullRequest).where(PullRequest.agent_run_id == current_run_id)
        pr = session.exec(statement).first()
        if pr:
            return pr

        run = session.get(AgentRun, current_run_id)
        if not run or not run.parent_run_id:
            break
        current_run_id = run.parent_run_id

    return None
