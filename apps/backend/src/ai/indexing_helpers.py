import logging
from pathlib import Path
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

def build_index(
    workspace_path: str,
    repository_id: str,
    branch: str,
    collection_name: str,
    chroma_client: Any,
    chunker: Any,
    embedding_fn: Callable[[str], list[float]],
    ignore_fn: Callable[[str], bool]
) -> int:
    """Shared helper to extract, chunk, embed, and store documents."""
    base = Path(workspace_path)
    
    try:
        chroma_client.delete_collection(collection_name)
    except Exception as exc:
        logger.warning("Failed deleting collection %s: %s", collection_name, exc)

    collection = chroma_client.get_or_create_collection(collection_name)

    batch_documents: list[str] = []
    batch_embeddings: list[list[float]] = []
    batch_metadata: list[dict[str, Any]] = []
    batch_ids: list[str] = []
    indexed_chunks = 0

    for file_path in base.rglob("*"):
        if not file_path.is_file():
            continue
            
        rel_path = str(file_path.relative_to(base))
        if ignore_fn(rel_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue

            chunks = chunker.chunk(text=content)

            for i, chunk in enumerate(chunks):
                if not chunk.text.strip():
                    continue

                chunk_id = f"{repository_id}_{rel_path}_{i}"
                batch_documents.append(chunk.text)
                
                # NOTE:
                # Embeddings are generated sequentially per chunk.
                # Acceptable for MVP-sized repositories but should be batched
                # or parallelized for larger indexing workloads.
                batch_embeddings.append(embedding_fn(chunk.text))
                
                batch_metadata.append({
                    "repository_id": str(repository_id),
                    "branch": branch,
                    "file_path": rel_path,
                    "chunk_index": i,
                })
                batch_ids.append(chunk_id)
                indexed_chunks += 1

        except Exception as exc:
            logger.warning(
                "Skipping file %s due to indexing error: %s",
                rel_path,
                exc,
                exc_info=True,
            )
            continue

    if batch_documents:
        collection.add(
            documents=batch_documents,
            embeddings=batch_embeddings,
            metadatas=batch_metadata,
            ids=batch_ids,
        )

    return indexed_chunks