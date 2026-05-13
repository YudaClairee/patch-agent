"""Authentication dependencies: cookie-based JWT session resolved to a User."""
from __future__ import annotations

import logging

import jwt
from fastapi import Depends, HTTPException, Request, WebSocket, status
from sqlmodel import Session

from src.core.config import settings
from src.core.database import get_session
from src.core.security import decode_session_token
from src.models.user import User

logger = logging.getLogger(__name__)


def _resolve_user(session: Session, token: str | None) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    try:
        user_id = decode_session_token(token)
    except (jwt.PyJWTError, ValueError) as exc:
        logger.debug("Rejected session token: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    return _resolve_user(session, token)


async def current_user_ws(
    websocket: WebSocket,
    session: Session = Depends(get_session),
) -> User:
    token = websocket.cookies.get(settings.session_cookie_name)
    try:
        return _resolve_user(session, token)
    except HTTPException:
        await websocket.close(code=4401)
        raise
