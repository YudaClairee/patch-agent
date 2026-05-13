"""GitHub credential helpers — single integration point for decrypted tokens."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlmodel import Session, select

from src.core.security import decrypt_github_token
from src.models.github_credential import GithubCredential

logger = logging.getLogger(__name__)


def get_active_credential(session: Session, user_id: uuid.UUID) -> GithubCredential | None:
    return session.exec(
        select(GithubCredential)
        .where(
            GithubCredential.user_id == user_id,
            GithubCredential.revoked_at.is_(None),  # type: ignore[attr-defined]
        )
        .order_by(GithubCredential.created_at.desc())  # type: ignore[attr-defined]
    ).first()


def get_active_token(session: Session, user_id: uuid.UUID) -> str:
    """Return the decrypted GitHub token for the user. Raises 400 if none connected."""
    cred = get_active_credential(session, user_id)
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GitHub account connected. Connect via /auth/github/start first.",
        )
    token = decrypt_github_token(cred.encrypted_token)
    cred.last_used_at = datetime.now(timezone.utc)
    session.add(cred)
    session.commit()
    return token


def decrypt_token(credential: GithubCredential) -> str:
    """Backwards-compatible helper used by the agent runner."""
    if credential is None or not credential.encrypted_token:
        raise ValueError("Credential is missing")
    return decrypt_github_token(credential.encrypted_token)
