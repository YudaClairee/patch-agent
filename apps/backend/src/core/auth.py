"""
src/core/auth.py
────────────────
STUB — Stream 1 has not landed yet.

This module is the integration point for Stream 1's authentication layer.
Replace the bodies of `current_user` and `current_user_ws` when Stream 1
delivers its JWT / session-cookie validation logic.

Until then the stubs raise HTTP 401 so that protected endpoints are not
accidentally accessible in a deployed environment.  If you want to exercise
routes locally without a real user session, temporarily flip `_STUB_ENABLED`
to True (never commit that change to main).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, WebSocket, status

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Toggle this to True ONLY during local development when you want the routes
# to respond without a real auth token.  MUST remain False in production.
# ---------------------------------------------------------------------------
_STUB_ENABLED: bool = True

_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# Lazily created on first request so that all SQLAlchemy mappers are fully
# configured before we instantiate a model (avoids mapper-init ordering issues).
_stub_user_cache = None


def _get_stub_user():
    """Return (and cache) the hard-coded stub User instance."""
    global _stub_user_cache  # noqa: PLW0603
    if _stub_user_cache is None:
        # Import here, not at module level, so mappers are all configured first.
        from src.models.user import User  # noqa: PLC0415

        _stub_user_cache = User(
            id=_STUB_USER_ID,
            email="stub@example.com",
            name="Stub User",
            hashed_password="",
            daily_run_quota=15,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    return _stub_user_cache


async def current_user():
    """
    FastAPI dependency — resolves the authenticated user from the request.

    STUB: returns a hard-coded User until Stream 1 is integrated.
    Replace with real token extraction + DB lookup when Stream 1 lands.
    """
    if _STUB_ENABLED:
        logger.warning(
            "[AUTH STUB] current_user returning hard-coded stub user — Stream 1 auth has not been integrated yet."
        )
        return _get_stub_user()

    # TODO (Stream 1): extract bearer token from Authorization header,
    # validate it, look up the User in the DB, and return it.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Stream 1 not yet integrated).",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def current_user_ws(websocket: WebSocket):
    """
    WebSocket dependency — resolves the authenticated user from the WS handshake.

    STUB: returns a hard-coded User until Stream 1 is integrated.
    Replace with real token extraction when Stream 1 lands.
    """
    if _STUB_ENABLED:
        logger.warning(
            "[AUTH STUB] current_user_ws returning hard-coded stub user — Stream 1 auth has not been integrated yet."
        )
        return _get_stub_user()

    # TODO (Stream 1): extract token from query param / cookie,
    # validate it, look up the User, and return it.
    await websocket.close(code=1008)  # Policy Violation
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required (Stream 1 not yet integrated).",
    )
