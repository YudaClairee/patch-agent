import uuid
from sqlmodel import Session, select
from src.models.task import Task
from src.models.agent_run import AgentRun
from src.schemas.task import TaskCreate


def create_task(session: Session, user_id: uuid.UUID, data: TaskCreate) -> Task:
    """
    Creates a new Task or returns the existing task from a parent run.
    """
    if data.parent_run_id:
        parent_run = session.get(AgentRun, data.parent_run_id)
        if parent_run:
            return parent_run.task

    # Generate title from the first 80 characters of instruction
    title = data.instruction[:80] if len(data.instruction) > 0 else "New Task"
    
    task = Task(
        user_id=user_id,
        repository_id=data.repository_id,
        title=title,
        instruction=data.instruction,
        target_branch=data.target_branch,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: uuid.UUID) -> Task | None:
    """
    Retrieves a task by ID.
    """
    return session.get(Task, task_id)


def list_tasks_by_user(session: Session, user_id: uuid.UUID, limit: int = 50) -> list[Task]:
    """
    Lists tasks for a specific user, ordered by creation date descending.
    """
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    results = session.exec(statement)
    return list(results.all())
