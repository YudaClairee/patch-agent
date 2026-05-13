import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.core.auth import current_user
from src.core.database import get_session
from src.models.agent_run import AgentRun
from src.models.enums import RunStatus
from src.models.user import User
from src.repositories import agent_runs as agent_runs_repo
from src.schemas.agent_run import AgentRunRead
from src.schemas.feedback import FeedbackCreate
from src.services.agent_dispatch import enqueue_agent_run

logger = logging.getLogger(__name__)

feedback_router = APIRouter(prefix="/agent_runs", tags=["Feedback"])


@feedback_router.post(
    "/{id}/feedback",
    response_model=AgentRunRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    id: uuid.UUID,
    body: FeedbackCreate,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    parent_run = agent_runs_repo.get_agent_run_for_user(session, id, user.id)
    if not parent_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent agent run not found or does not belong to you.",
        )
    if parent_run.status != RunStatus.succeeded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Parent agent run must be succeeded before submitting feedback.",
        )

    try:
        new_run = AgentRun(
            task_id=parent_run.task_id,
            parent_run_id=parent_run.id,
            follow_up_instruction=body.instruction,
            branch_name=parent_run.branch_name,
            status=RunStatus.queued,
            model_id=parent_run.model_id,
            prompt_version=parent_run.prompt_version,
            max_turns=parent_run.max_turns,
            queued_at=datetime.now(timezone.utc),
        )
        session.add(new_run)
        session.commit()
        session.refresh(new_run)
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.exception("Error creating feedback child run: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feedback run",
        ) from exc

    enqueue_agent_run(new_run.id)

    return AgentRunRead.model_validate(new_run)

