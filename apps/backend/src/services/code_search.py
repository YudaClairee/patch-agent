"""Semantic code search service.

Provides search_code() that embeds a query, searches pgvector for similar
code chunks, and returns ranked results with file paths and line ranges.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlmodel import Session, select

from src.core.database import engine
from src.models.code_chunk import CodeChunk
from src.services.embedding import embed_query

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    file_path: str
    start_line: int
    end_line: int
    language: str | None
    symbol_name: str | None
    symbol_type: str | None
    score: float
    content_preview: str

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "symbol_name": self.symbol_name,
            "symbol_type": self.symbol_type,
            "score": round(self.score, 4),
            "content_preview": self.content_preview,
        }


async def search_code(
    query: str,
    repository_id: str | uuid.UUID,
    limit: int = 8,
) -> list[SearchResult]:
    """Semantic code search over indexed chunks.

    1. Embed the query string.
    2. Search code_chunks by cosine similarity, filtered by repository_id.
    3. Return top-k results with file path, line range, and content preview.
    """
    if isinstance(repository_id, str):
        repository_id = uuid.UUID(repository_id)

    limit = max(1, min(limit, 20))

    try:
        query_embedding = await embed_query(query)
    except Exception:
        logger.exception("Query embedding failed")
        return []

    with Session(engine) as session:
        distance = CodeChunk.embedding.cosine_distance(query_embedding).label(
            "distance"
        )
        stmt = (
            select(
                CodeChunk,
                distance,
            )
            .where(CodeChunk.repository_id == repository_id)
            .order_by(distance)
            .limit(limit)
        )

        results: list[SearchResult] = []
        for row in session.exec(stmt).all():
            chunk = row[0]
            distance = float(row[1])
            score = 1.0 - distance

            preview = chunk.content[:500]
            if len(chunk.content) > 500:
                preview += "..."

            results.append(
                SearchResult(
                    file_path=chunk.file_path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    language=chunk.language,
                    symbol_name=chunk.symbol_name,
                    symbol_type=chunk.symbol_type,
                    score=score,
                    content_preview=preview,
                )
            )

        return results
