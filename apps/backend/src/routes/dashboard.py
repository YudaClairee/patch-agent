import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.core.auth import current_user
from src.core.database import get_session
from src.models.user import User
from src.repositories import dashboard as dashboard_repo
from src.schemas.dashboard import DashboardRead

logger = logging.getLogger(__name__)

dashboard_router = APIRouter(prefix="/me", tags=["Dashboard"])


@dashboard_router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    stats = dashboard_repo.get_dashboard(session, user.id)
    return DashboardRead(**stats)
