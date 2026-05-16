"""Repository indexing service.

Chunks a repository, embeds the chunks, and upserts them into the
code_chunks table. Uses content_hash to avoid re-embedding unchanged chunks.
Deletes stale chunks (files no longer in repo) after indexing.
"""

from __future__ import annotations

import logging
import uuid

from sqlmodel import Session, select

from src.core.database import engine
from src.models.code_chunk import CodeChunk
from src.services.code_chunker import chunk_repository
from src.services.embedding import embed_texts

logger = logging.getLogger(__name__)


async def index_repository(
    repository_id: uuid.UUID | str,
    workspace_path: str,
    commit_sha: str | None = None,
) -> dict:
    """Index a repository into the vector DB.

    1. Chunk all source files in workspace_path.
    2. Check which chunks already exist (by content_hash) to skip re-embedding.
    3. Embed new/changed chunks.
    4. Upsert into code_chunks table.
    5. Delete stale chunks (files no longer in current scan).

    Returns a summary dict with counts. Non-fatal: if embedding fails,
    returns error info without raising.
    """
    if isinstance(repository_id, str):
        repository_id = uuid.UUID(repository_id)

    try:
        chunks = chunk_repository(workspace_path)
    except Exception as exc:
        logger.exception("Chunking failed for %s", workspace_path)
        return {"ok": False, "error": f"Chunking failed: {exc}"}

    if not chunks:
        logger.info("No chunks found in %s", workspace_path)
        # Clean up all chunks for this repo if no files found
        _delete_chunks_for_repo(repository_id)
        return {
            "ok": True,
            "chunks_total": 0,
            "chunks_new": 0,
            "chunks_skipped": 0,
            "chunks_deleted": 0,
        }

    current_keys = {
        _chunk_key(chunk.file_path, chunk.start_line, chunk.content_hash)
        for chunk in chunks
    }

    with Session(engine) as session:
        existing_chunks = list(
            session.exec(
                select(CodeChunk).where(CodeChunk.repository_id == repository_id)
            ).all()
        )
        existing_by_key = {
            _chunk_key(row.file_path, row.start_line, row.content_hash): row
            for row in existing_chunks
        }

        new_chunks = []
        for chunk in chunks:
            key = _chunk_key(chunk.file_path, chunk.start_line, chunk.content_hash)
            if key in existing_by_key:
                continue
            new_chunks.append(chunk)

        if not new_chunks:
            logger.info(
                "All %d chunks already indexed for repo %s",
                len(chunks),
                repository_id,
            )
            updated = _refresh_existing_metadata(
                existing_by_key,
                current_keys,
                commit_sha,
                session,
            )
            deleted = _delete_obsolete_chunks(existing_chunks, current_keys, session)
            session.commit()
            return {
                "ok": True,
                "chunks_total": len(chunks),
                "chunks_new": 0,
                "chunks_skipped": len(chunks),
                "chunks_updated": updated,
                "chunks_deleted": deleted,
            }

        texts_to_embed = [c.content for c in new_chunks]
        try:
            embeddings = await embed_texts(texts_to_embed)
        except Exception as exc:
            logger.exception("Embedding failed for repo %s", repository_id)
            return {
                "ok": False,
                "error": f"Embedding failed: {exc}",
                "chunks_total": len(chunks),
            }

        upserted = 0
        for chunk, embedding in zip(new_chunks, embeddings):
            key = _chunk_key(chunk.file_path, chunk.start_line, chunk.content_hash)
            existing_chunk = existing_by_key.get(key)

            if existing_chunk:
                existing_chunk.content = chunk.content
                existing_chunk.embedding = embedding
                existing_chunk.commit_sha = commit_sha
                existing_chunk.language = chunk.language
                existing_chunk.end_line = chunk.end_line
                session.add(existing_chunk)
                upserted += 1
            else:
                db_chunk = CodeChunk(
                    id=uuid.uuid4(),
                    repository_id=repository_id,
                    commit_sha=commit_sha,
                    file_path=chunk.file_path,
                    language=chunk.language,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                    embedding=embedding,
                )
                session.add(db_chunk)
                upserted += 1

        updated = _refresh_existing_metadata(
            existing_by_key,
            current_keys,
            commit_sha,
            session,
        )
        deleted = _delete_obsolete_chunks(existing_chunks, current_keys, session)

        session.commit()

        logger.info(
            "Indexed repo %s: %d total, %d new/updated, %d skipped, %d deleted",
            repository_id,
            len(chunks),
            upserted,
            len(chunks) - upserted,
            deleted,
        )

        return {
            "ok": True,
            "chunks_total": len(chunks),
            "chunks_new": upserted,
            "chunks_skipped": len(chunks) - upserted,
            "chunks_updated": updated,
            "chunks_deleted": deleted,
        }


def _chunk_key(file_path: str, start_line: int, content_hash: str) -> str:
    return f"{file_path}:{start_line}:{content_hash}"


def _refresh_existing_metadata(
    existing_by_key: dict[str, CodeChunk],
    current_keys: set[str],
    commit_sha: str | None,
    session: Session,
) -> int:
    """Refresh metadata on unchanged chunks without re-embedding them."""
    updated = 0
    for key in current_keys:
        chunk = existing_by_key.get(key)
        if chunk is None or chunk.commit_sha == commit_sha:
            continue
        chunk.commit_sha = commit_sha
        session.add(chunk)
        updated += 1
    return updated


def _delete_obsolete_chunks(
    existing_chunks: list[CodeChunk],
    current_keys: set[str],
    session: Session,
) -> int:
    """Delete chunks no longer present at the current checkout."""
    obsolete_chunks = [
        chunk
        for chunk in existing_chunks
        if _chunk_key(chunk.file_path, chunk.start_line, chunk.content_hash)
        not in current_keys
    ]
    count = len(obsolete_chunks)
    for chunk in obsolete_chunks:
        session.delete(chunk)
    if count > 0:
        logger.info("Deleted %d obsolete chunks", count)
    return count


def _delete_chunks_for_repo(repository_id: uuid.UUID) -> None:
    """Delete all chunks for a repository."""
    with Session(engine) as session:
        stmt = select(CodeChunk).where(CodeChunk.repository_id == repository_id)
        chunks = session.exec(stmt).all()
        count = len(chunks)
        for chunk in chunks:
            session.delete(chunk)
        session.commit()
        if count > 0:
            logger.info("Deleted all %d chunks for repo %s", count, repository_id)
