import logging
from pathlib import Path

import chromadb
from chonkie import SemanticChunker
from openai import OpenAI

from src.ai.indexing_helpers import build_index
from src.core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"

IGNORED_PATHS: list[str] = [
    ".git", "node_modules", ".venv", "dist", "build",
    ".env", ".env.local", ".pem", ".key", ".png", ".jpg", ".zip",
    "__pycache__", ".pyc", ".DS_Store", ".pytest_cache",
]

# PersistentClient does not work with ephemeral agent containers
# because indexes become container-local and are destroyed per run.
# HttpClient allows all workers/agents to share the same Chroma instance.
_chroma_client = chromadb.HttpClient(
    host=settings.chroma_host,
    port=settings.chroma_port,
)

_openai_client = OpenAI(
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
)

_chunker = SemanticChunker(
    embedding_model="minishlab/potion-base-32M",
    chunk_size=256,
    threshold=0.5,
)


def _get_embedding(text: str) -> list[float]:
    response = _openai_client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def _should_ignore(file_path: str) -> bool:
    # TODO: Compare by path parts instead of simple substring for better accuracy in future iteration
    for pattern in IGNORED_PATHS:
        if pattern in file_path:
            return True
    return False


def _get_collection_name(repository_id: str, branch: str) -> str:
    return f"repo_{repository_id}_{branch}".replace("/", "_")[:63]


def index_codebase(workspace_path: str, repository_id: str, branch: str) -> dict[str, str]:
    collection_name = _get_collection_name(repository_id, branch)

    indexed = build_index(
        workspace_path=workspace_path,
        repository_id=repository_id,
        branch=branch,
        collection_name=collection_name,
        chroma_client=_chroma_client,
        chunker=_chunker,
        embedding_fn=_get_embedding,
        ignore_fn=_should_ignore,
    )

    return {
        "status": "success",
        "indexed_chunks": str(indexed),
    }


def search_code(
    query: str,
    repository_id: str,
    branch: str,
    n_results: int = 5,
) -> dict[str, list[dict]]:
    """Search for relevant code snippets in the indexed repository."""
    collection_name = _get_collection_name(repository_id, branch)

    try:
        collection = _chroma_client.get_collection(collection_name)
    except ValueError as exc:
        logger.warning(
            "Collection lookup failed for %s: %s",
            collection_name,
            exc,
        )
        raise FileNotFoundError(
            "Collection not found. Codebase indexing is required."
        ) from exc

    query_embedding = _get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, 10),
        include=["documents", "metadatas", "distances"],
    )

    output: list[dict] = []
    if results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0], # type: ignore
            results["distances"][0], # type: ignore
        ):
            if not _should_ignore(meta.get("file_path", "")): # type: ignore
                output.append({
                    "file_path": meta.get("file_path", ""),
                    "chunk_index": meta.get("chunk_index", 0),
                    "score": round(1 - dist, 4),
                    "content": doc,
                })

    return {"results": output}


def get_code_context(workspace_path: str, file_path: str) -> dict[str, str]:
    """Get the full content of a specific code file for better context."""
    if _should_ignore(file_path):
        raise PermissionError(f"Access to {file_path} is blocked by security policy.")
    full_path = Path(workspace_path) / file_path
    if not full_path.exists():
        raise FileNotFoundError(f"File {file_path} not found in workspace.")
    return {
        "file_path": file_path,
        "content": full_path.read_text(encoding="utf-8", errors="ignore"),
    }