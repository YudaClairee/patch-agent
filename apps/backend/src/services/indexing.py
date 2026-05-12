import logging
import subprocess
import tempfile
import uuid
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session, select

from src.celery_app import celery_app
from src.core.config import settings
from src.core.database import get_session
from src.models.codebase_index import CodebaseIndex
from src.models.repository import Repository
from src.models.enums import IndexStatus

from src.ai.tools.rag_tools import (
    IGNORED_PATHS,
    _chunker,
    _chroma_client,
    _get_embedding,
    _should_ignore,
)

logger = logging.getLogger(__name__)


def _clone_repo(clone_url: str, target_dir: str, branch: str) -> str:
    result = subprocess.run(
        ["git", "clone", "--depth=1", "--branch", branch, clone_url, target_dir],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Clone failed: {result.stderr}")
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

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            workspace_path = _clone_repo(repo_row.clone_url, tmpdir, branch)
        except RuntimeError as e:
            index_row.status = IndexStatus.failed
            index_row.error_message = str(e)
            session.add(index_row)
            session.commit()
            logger.error("Clone failed for repo %s: %s", repository_id, e)
            return

        try:
            collection_name = index_row.chroma_collection_name

            try:
                _chroma_client.delete_collection(collection_name)
            except Exception:
                pass

            collection = _chroma_client.create_collection(collection_name)
            base = Path(workspace_path)

            indexed = 0
            documents: list[str] = []
            embeddings: list[list[float]] = []
            metadatas: list[dict] = []
            ids: list[str] = []

            for file_path in base.rglob("*"):
                if not file_path.is_file():
                    continue
                rel_path = str(file_path.relative_to(base))
                if _should_ignore(rel_path):
                    continue

                logger.debug("Indexing: %s", rel_path)

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    if not content.strip():
                        continue

                    chunks = _chunker.chunk(text=content)

                    for i, chunk in enumerate(chunks):
                        if not chunk.text.strip():
                            continue

                        chunk_id = f"{repository_id}_{rel_path}_{i}"
                        documents.append(chunk.text)
                        embeddings.append(_get_embedding(chunk.text))
                        metadatas.append({
                            "repository_id": str(repository_id),
                            "branch": branch,
                            "file_path": rel_path,
                            "chunk_index": i,
                        })
                        ids.append(chunk_id)
                        indexed += 1

                except Exception:
                    logger.warning("Skipping file %s", rel_path, exc_info=True)
                    continue

            if documents:
                collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )

            index_row.status = IndexStatus.ready
            index_row.chunk_count = indexed
            index_row.indexed_at = datetime.now(UTC)
            session.add(index_row)
            session.commit()
            logger.info("Indexed %d chunks for repo %s branch %s", indexed, repository_id, branch)

        except Exception as e:
            try:
                _chroma_client.delete_collection(index_row.chroma_collection_name)
            except Exception:
                pass

            index_row.status = IndexStatus.failed
            index_row.error_message = str(e)
            session.add(index_row)
            session.commit()
            logger.error("Indexing failed for repo %s: %s", repository_id, e, exc_info=True)


@celery_app.task(name="src.services.indexing.index_repository", bind=True)
def index_repository(self, index_id: str, repository_id: str, branch: str) -> None:
    idx_uuid = uuid.UUID(index_id)
    repo_uuid = uuid.UUID(repository_id)
    
    def _sync_wrapper():
        with next(get_session()) as session:
            _run_index(idx_uuid, repo_uuid, branch, session)
            
    asyncio.run(_sync_wrapper())