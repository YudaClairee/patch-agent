"""Embedding service for code chunks and queries.

Uses LiteLLM to generate embeddings via the configured embedding model.
Falls back gracefully on errors so indexing failures are non-fatal.
"""
from __future__ import annotations

import logging

import litellm

from src.core.config import settings

logger = logging.getLogger(__name__)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts using the configured embedding model.

    Returns a list of embedding vectors. If embedding fails for a batch,
    the entire batch raises — callers should handle partial failures.
    """
    if not texts:
        return []

    all_embeddings: list[list[float]] = []
    batch_size = settings.embedding_batch_size

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # Build kwargs for LiteLLM based on model prefix
        embedding_kwargs: dict = {
            "model": settings.embedding_model_id,
            "input": batch,
        }

        # For OpenRouter models, pass api_base and api_key explicitly
        if settings.embedding_model_id.startswith("openrouter/"):
            embedding_kwargs["api_base"] = "https://openrouter.ai/api/v1"
            embedding_kwargs["api_key"] = settings.llm_api_key

        try:
            response = await litellm.aembedding(**embedding_kwargs)
            batch_embeddings = [item["embedding"] for item in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception:
            logger.exception(
                "Embedding batch %d-%d failed (model=%s)",
                i,
                i + len(batch),
                settings.embedding_model_id,
            )
            raise

    return all_embeddings


async def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    embeddings = await embed_texts([query])
    return embeddings[0]
