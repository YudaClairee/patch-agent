import logging
from uuid import UUID

from github import Github, GithubException
from sqlmodel import Session, select

from src.models.codebase_index import CodebaseIndex
from src.models.repository import Repository
from src.ai.tools.rag_tools import _chroma_client

logger = logging.getLogger(__name__)


def _delete_chroma_collection_by_name(collection_name: str) -> None:
    """Delete Chroma collection by name — wrapped untuk kemudahan mocking di test."""
    try:
        _chroma_client.delete_collection(collection_name)
        logger.debug("Deleted Chroma collection: %s", collection_name)
    except Exception:
        logger.warning("Collection %s not found in Chroma, skipping.", collection_name)


def connect_repo(
    user_id: UUID,
    owner: str,
    name: str,
    pat: str,
    session: Session,
) -> Repository:
    """
    Validate repo via PyGitHub, upsert Repository row.
    pat: plain-text PAT, sudah di-decrypt oleh caller (Stream 1's decrypt_token).
    
    Field mapping sesuai model tim:
    - owner → github_owner
    - name → github_repo
    - full_name tidak disimpan (computed)
    - credential_id tidak ada di Repository (ada di User level via Stream 1)
    """
    full_name = f"{owner}/{name}"

    existing = session.exec(
        select(Repository).where(
            Repository.user_id == user_id,
            Repository.github_owner == owner,
            Repository.github_repo == name,
        )
    ).first()

    if existing is not None:
        logger.debug("Repository %s already connected for user %s", full_name, user_id)
        return existing

    try:
        g = Github(pat)
        gh_repo = g.get_repo(full_name)
    except GithubException:
        raise ValueError(
            f"Repository {full_name} not found or not accessible with provided credentials."
        )

    repo = Repository(
        user_id=user_id,
        github_owner=owner,
        github_repo=name,
        github_repo_id=gh_repo.id,
        clone_url=gh_repo.clone_url,
        default_branch=gh_repo.default_branch,
        language=gh_repo.language,
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)

    logger.info("Connected repository %s for user %s", full_name, user_id)
    return repo


def disconnect_repo(
    user_id: UUID,
    repository_id: UUID,
    session: Session,
) -> None:
    """
    Delete Repository and cascade all CodebaseIndex rows + Chroma collections.
    Raises PermissionError if user_id is not the owner.
    """
    repo = session.get(Repository, repository_id)
    if repo is None:
        raise ValueError(f"Repository {repository_id} not found.")

    if repo.user_id != user_id:
        raise PermissionError(
            f"User {user_id} is not authorized to disconnect repository {repository_id}."
        )

    indexes = session.exec(
        select(CodebaseIndex).where(CodebaseIndex.repository_id == repository_id)
    ).all()

    for idx in indexes:
        _delete_chroma_collection_by_name(idx.chroma_collection_name)
        session.delete(idx)

    session.delete(repo)
    session.commit()
    logger.info("Disconnected repository %s for user %s", repository_id, user_id)