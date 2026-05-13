import logging
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

from sqlmodel import Session

from src.ai.indexing_helpers import build_index
from src.ai.tools.rag_tools import (
    _chunker,
    _chroma_client,
    _get_embedding,
    _should_ignore,
)
from src.celery_app import celery_app
from src.core.database import get_session
from src.models.codebase_index import CodebaseIndex
from src.models.enums import IndexStatus
from src.models.repository import Repository
from src.services.credentials import get_active_credential
from src.core.security import decrypt_github_token

logger = logging.getLogger(__name__)


def _authed_clone_url(clone_url: str, token: str | None) -> str:
    """Inject a token into an HTTPS GitHub clone URL for non-public access."""
    if not token or not clone_url.startswith("https://"):
        return clone_url
    parsed = urlparse(clone_url)
    netloc = f"x-access-token:{quote(token, safe='')}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _clone_repo(clone_url: str, target_dir: Path, branch: str, token: str | None = None) -> Path:
    authed_url = _authed_clone_url(clone_url, token)
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--branch", branch, authed_url, str(target_dir)],
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        # Scrub token from any error output before raising.
        stderr = result.stderr
        if token:
            stderr = stderr.replace(token, "***")
        raise RuntimeError(f"Clone failed: {stderr}")

    return target_dir


def _run_index(
    index_id: uuid.UUID,
    repository_id: uuid.UUID,
    branch: str,
    session: Session,
) -> None:
    index_row = session.get(CodebaseIndex, index_id)
    if index_row is None:
        raise ValueError(f"CodebaseIndex {index_id} not found.")

    repo_row = session.get(Repository, repository_id)
    if repo_row is None:
        raise ValueError(f"Repository {repository_id} not found.")

    index_row.status = IndexStatus.indexing
    session.add(index_row)
    session.commit()

    token: str | None = None
    cred = get_active_credential(session, repo_row.user_id)
    if cred is not None:
        try:
            token = decrypt_github_token(cred.encrypted_token)
        except ValueError:
            logger.warning("Failed to decrypt GitHub token for user %s; cloning anonymously", repo_row.user_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            target_workspace = Path(tmpdir) / "repo"
            workspace_path = _clone_repo(
                repo_row.clone_url,
                target_workspace,
                branch,
                token=token,
            )

            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
            )
            if sha_result.returncode != 0:
                raise RuntimeError("Failed resolving indexed commit SHA")

            index_row.indexed_commit_sha = sha_result.stdout.strip()

        except RuntimeError as exc:
            index_row.status = IndexStatus.failed
            index_row.error_message = str(exc)

            session.add(index_row)
            session.commit()

            logger.error(
                "Clone failed for repo %s: %s",
                repository_id,
                exc,
            )
            return

        try:
            indexed_chunks = build_index(
                workspace_path=str(workspace_path),
                repository_id=str(repository_id),
                branch=branch,
                collection_name=index_row.chroma_collection_name,
                chroma_client=_chroma_client,
                chunker=_chunker,
                embedding_fn=_get_embedding,
                ignore_fn=_should_ignore,
            )

            index_row.status = IndexStatus.ready
            index_row.chunk_count = indexed_chunks
            index_row.indexed_at = datetime.now(UTC)

            session.add(index_row)
            session.commit()

            logger.info(
                "Indexed %d chunks for repo %s branch %s",
                indexed_chunks,
                repository_id,
                branch,
            )

        except Exception as exc:
            try:
                # Collection may not exist during first-time indexing
                # or rollback cleanup.
                _chroma_client.delete_collection(
                    index_row.chroma_collection_name,
                )

            except Exception as delete_exc:
                logger.warning(
                    "Failed deleting collection %s: %s",
                    index_row.chroma_collection_name,
                    delete_exc,
                )

            index_row.status = IndexStatus.failed
            index_row.error_message = str(exc)

            session.add(index_row)
            session.commit()

            logger.exception(
                "Indexing failed for repo %s",
                repository_id,
            )


@celery_app.task(name="src.services.indexing.index_repository")
def index_repository(
    index_id: str,
    repository_id: str,
    branch: str,
) -> None:
    idx_uuid = uuid.UUID(index_id)
    repo_uuid = uuid.UUID(repository_id)

    session = next(get_session())

    try:
        _run_index(
            idx_uuid,
            repo_uuid,
            branch,
            session,
        )

    finally:
        session.close()