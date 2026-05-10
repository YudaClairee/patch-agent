import datetime
import uuid
from sqlmodel import Session, select, func
from src.models.user import User
from src.models.repository import Repository
from src.models.agent_run import AgentRun
from src.models.task import Task
from src.models.usage_record import UsageRecord
from src.models.enums import RunStatus


def get_dashboard(session: Session, user_id: uuid.UUID) -> dict:
    """
    Returns dashboard statistics for a user.
    """
    # 1. repository_count
    repo_count_statement = select(func.count(Repository.id)).where(
        Repository.user_id == user_id
    )
    repository_count = session.exec(repo_count_statement).one()

    # 2. active_run_count (queued, running)
    active_run_statement = (
        select(func.count(AgentRun.id))
        .join(Task)
        .where(Task.user_id == user_id)
        .where(AgentRun.status.in_([RunStatus.queued, RunStatus.running]))
    )
    active_run_count = session.exec(active_run_statement).one()

    # 3. succeeded_run_count
    succeeded_run_statement = (
        select(func.count(AgentRun.id))
        .join(Task)
        .where(Task.user_id == user_id)
        .where(AgentRun.status == RunStatus.succeeded)
    )
    succeeded_run_count = session.exec(succeeded_run_statement).one()

    # 4. today_run_count
    today = datetime.date.today()
    usage_statement = select(UsageRecord).where(
        UsageRecord.user_id == user_id, UsageRecord.date == today
    )
    usage = session.exec(usage_statement).first()
    today_run_count = usage.run_count if usage else 0

    # 5. daily_run_quota
    user = session.get(User, user_id)
    daily_run_quota = user.daily_run_quota if user else 0

    return {
        "repository_count": repository_count,
        "active_run_count": active_run_count,
        "succeeded_run_count": succeeded_run_count,
        "today_run_count": today_run_count,
        "daily_run_quota": daily_run_quota,
    }
