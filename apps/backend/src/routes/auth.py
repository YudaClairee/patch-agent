"""Authentication and GitHub OAuth routes."""
from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.core.auth import current_user
from src.core.config import settings
from src.core.database import get_session
from src.core.security import (
    create_session_token,
    encrypt_github_token,
    hash_password,
    verify_password,
)
from src.models.github_credential import GithubCredential
from src.models.user import User
from src.schemas.user import UserRead

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
me_router = APIRouter(prefix="/me", tags=["Me"])

_OAUTH_STATE_COOKIE = "patch_oauth_state"
_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_GITHUB_SCOPES = "repo read:user"


class SignupBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)
    name: str | None = Field(default=None, max_length=255)


class LoginBody(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


def _is_production() -> bool:
    return settings.environment.lower() == "production"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        secure=_is_production(),
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        samesite="lax",
        secure=_is_production(),
        httponly=True,
    )


@auth_router.post("/signup", response_model=UserRead)
def signup(
    body: SignupBody,
    response: Response,
    session: Session = Depends(get_session),
) -> UserRead:
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_session_token(user.id)
    _set_session_cookie(response, token)
    return UserRead.model_validate(user)


@auth_router.post("/login", response_model=UserRead)
def login(
    body: LoginBody,
    response: Response,
    session: Session = Depends(get_session),
) -> UserRead:
    user = session.exec(select(User).where(User.email == body.email)).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_session_token(user.id)
    _set_session_cookie(response, token)
    return UserRead.model_validate(user)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    _clear_session_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@me_router.get("", response_model=UserRead)
def get_me(user: User = Depends(current_user)) -> UserRead:
    return UserRead.model_validate(user)


# ---------------------------------------------------------------------------
# GitHub OAuth
# ---------------------------------------------------------------------------


@auth_router.get("/github/start")
def github_start(
    request: Request,
    user: User = Depends(current_user),
) -> RedirectResponse:
    if not settings.github_oauth_client_id or not settings.github_oauth_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth is not configured on this server",
        )

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.github_oauth_client_id,
        "redirect_uri": settings.github_oauth_redirect_uri,
        "scope": _GITHUB_SCOPES,
        "state": state,
        "allow_signup": "false",
    }
    redirect = RedirectResponse(f"{_GITHUB_AUTHORIZE_URL}?{urlencode(params)}", status_code=302)
    redirect.set_cookie(
        key=_OAUTH_STATE_COOKIE,
        value=state,
        max_age=600,
        httponly=True,
        samesite="lax",
        secure=_is_production(),
        path="/auth/github",
    )
    return redirect


@auth_router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> RedirectResponse:
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"GitHub error: {error}")
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code/state")

    expected_state = request.cookies.get(_OAUTH_STATE_COOKIE)
    if not expected_state or not secrets.compare_digest(expected_state, state):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            _GITHUB_TOKEN_URL,
            data={
                "client_id": settings.github_oauth_client_id,
                "client_secret": settings.github_oauth_client_secret,
                "code": code,
                "redirect_uri": settings.github_oauth_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            logger.warning("GitHub token exchange failed: %s %s", token_resp.status_code, token_resp.text)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub token exchange failed")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        scopes = token_data.get("scope", "")
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"GitHub returned no access token: {token_data.get('error_description', 'unknown')}",
            )

        user_resp = await client.get(
            _GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub /user call failed")
        github_username = user_resp.json().get("login") or "unknown"

    now = datetime.now(timezone.utc)
    existing = session.exec(
        select(GithubCredential).where(
            GithubCredential.user_id == user.id,
            GithubCredential.revoked_at.is_(None),  # type: ignore[attr-defined]
        )
    ).all()
    for cred in existing:
        cred.revoked_at = now
        session.add(cred)

    new_cred = GithubCredential(
        user_id=user.id,
        github_username=github_username,
        encrypted_token=encrypt_github_token(access_token),
        token_scopes=scopes,
    )
    session.add(new_cred)
    session.commit()

    response = RedirectResponse(f"{settings.frontend_url}/dashboard?github_connected=1", status_code=302)
    response.delete_cookie(_OAUTH_STATE_COOKIE, path="/auth/github")
    return response


# ---------------------------------------------------------------------------
# GitHub credential listing (read-only) under /me
# ---------------------------------------------------------------------------


class GithubCredentialRead(BaseModel):
    id: str
    github_username: str
    token_scopes: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


@me_router.get("/github-credentials", response_model=list[GithubCredentialRead])
def list_github_credentials(
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> list[GithubCredentialRead]:
    rows = session.exec(
        select(GithubCredential).where(GithubCredential.user_id == user.id)
    ).all()
    return [
        GithubCredentialRead(
            id=str(c.id),
            github_username=c.github_username,
            token_scopes=c.token_scopes,
            created_at=c.created_at,
            last_used_at=c.last_used_at,
            revoked_at=c.revoked_at,
        )
        for c in rows
    ]


@me_router.delete("/github-credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_github_credential(
    credential_id: str,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> Response:
    import uuid as _uuid

    try:
        cred_uuid = _uuid.UUID(credential_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid credential id")

    cred = session.get(GithubCredential, cred_uuid)
    if cred is None or cred.user_id != user.id:
        raise HTTPException(status_code=404, detail="Credential not found")
    cred.revoked_at = datetime.now(timezone.utc)
    session.add(cred)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
