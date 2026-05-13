import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.core.auth import current_user
from src.core.database import get_session
from src.models.codebase_index import CodebaseIndex
from src.models.enums import IndexStatus
from src.models.repository import Repository
from src.services.indexing import index_repository
from src.services.repositories import connect_repo, disconnect_repo
from src.ai.tools.rag_tools import _get_collection_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])


class RepositoryCreate(BaseModel):
    """Body locked: {owner, name} — dari Stream 4 API contract."""
    owner: str
    name: str


class RepositoryRead(BaseModel):
    """Response schema — dikonsumsi Stream 5."""
    id: str
    github_owner: str
    github_repo: str
    full_name: str
    default_branch: str
    language: str | None
    index_status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


def _to_read(repo: Repository, session: Session) -> RepositoryRead:
    """Convert Repository model to RepositoryRead schema dengan join CodebaseIndex."""
    latest_index = session.exec(
        select(CodebaseIndex)
        .where(CodebaseIndex.repository_id == repo.id)
        .order_by(CodebaseIndex.indexed_at.desc().nullslast()) # type: ignore
    ).first()

    return RepositoryRead(
        id=str(repo.id),
        github_owner=repo.github_owner,
        github_repo=repo.github_repo,
        full_name=f"{repo.github_owner}/{repo.github_repo}",
        default_branch=repo.default_branch,
        language=repo.language,
        index_status=latest_index.status.value if latest_index else "not_indexed",
        chunk_count=latest_index.chunk_count if latest_index else 0,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


@router.get("/", response_model=list[RepositoryRead])
def list_repositories(
    session: Session = Depends(get_session),
    user=Depends(current_user),
) -> list[RepositoryRead]:
    """GET /repositories — current user's connected repositories."""
    user_uuid = UUID(user.id) if isinstance(user.id, str) else user.id
    repos = session.exec(
        select(Repository).where(Repository.user_id == user_uuid)
    ).all()
    return [_to_read(r, session) for r in repos]


@router.post("/", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def create_repository(
    body: RepositoryCreate,
    session: Session = Depends(get_session),
    user=Depends(current_user),
) -> RepositoryRead:
    """
    POST /repositories — connect a GitHub repo and kick off indexing.
    Body: {owner, name} — locked by Stream 4 contract.
    Kicks off index_repository Celery task immediately after connect.
    """
    # stub: decrypt_token
    # TODO: pat = decrypt_token(session.get(GithubCredential, user.active_credential_id))
    pat = ""  # stream 1 will provide this
    user_uuid = UUID(user.id) if isinstance(user.id, str) else user.id

    try:
        repo = connect_repo(
            user_id=user_uuid,
            owner=body.owner,
            name=body.name,
            pat=pat,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    collection_name = _get_collection_name(str(repo.id), repo.default_branch)
    
    index_row = CodebaseIndex(
        repository_id=repo.id,
        branch=repo.default_branch,
        status=IndexStatus.pending,
        chroma_collection_name=collection_name,
    )
    session.add(index_row)
    session.commit()
    session.refresh(index_row)

    index_repository.delay(str(index_row.id), str(repo.id), repo.default_branch)
    logger.info(
        "Kicked off indexing task for repo %s branch %s",
        repo.id,
        repo.default_branch,
    )

    return _to_read(repo, session)


@router.delete("/{repository_id}", status_code=204)
def delete_repository(
    repository_id: UUID,
    session: Session = Depends(get_session),
    user=Depends(current_user),
) -> Response:
    """DELETE /repositories/{id} — disconnect repo and delete all indexes."""
    user_uuid = UUID(user.id) if isinstance(user.id, str) else user.id
    try:
        disconnect_repo(
            user_id=user_uuid,
            repository_id=repository_id,
            session=session,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return Response(status_code=204)