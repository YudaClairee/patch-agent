import chromadb
from chromadb import Collection
from pathlib import Path
from openai import OpenAI
from chonkie import SemanticChunker
from src.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"
IGNORED_PATHS: list[str] = [
    ".git", "node_modules", ".venv", "dist", "build",
    ".env", ".env.local", ".pem", ".key", ".png", ".jpg", ".zip",
]
_CHROMA_PATH = str(Path(".data/chromadb").resolve())
_chroma_client = chromadb.PersistentClient(path=_CHROMA_PATH)

_chunker = SemanticChunker(embedding_model="minishlab/potion-base-32M", chunk_size=256, threshold=0.5)

def _get_embedding(text: str) -> list[float]:
    client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

def _should_ignore(file_path: str) -> bool:
    for pattern in IGNORED_PATHS:
        if pattern in file_path:
            return True
    return False

def index_codebase(workspace_path: str, repository_id: str, branch: str) -> dict[str, str]:
    """Index all source code files in the workspace into ChromaDB."""
    collection_name = f"repo_{repository_id}_{branch}".replace("/", "_")[:63]

    try:
        _chroma_client.delete_collection(collection_name)
    except Exception:
        pass

    collection: Collection = _chroma_client.create_collection(collection_name)
    base = Path(workspace_path)
    
    indexed = 0
    documents, embeddings, metadatas, ids = [], [], [], []

    for file_path in base.rglob("*"):
        if not file_path.is_file():
            continue
        rel_path = str(file_path.relative_to(base))
        if _should_ignore(rel_path):
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
                
            chunks = _chunker.chunk(content)
            
            for i, chunk in enumerate(chunks):
                if not chunk.text.strip():
                    continue
                
                chunk_id = f"{repository_id}_{rel_path}_{i}"
                documents.append(chunk.text)
                embeddings.append(_get_embedding(chunk.text))
                metadatas.append({
                    "repository_id": repository_id,
                    "branch": branch,
                    "file_path": rel_path,
                    "chunk_index": i,
                })
                ids.append(chunk_id)
                indexed += 1
                
        except Exception:
            continue

    if documents:
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    return {"status": "success", "indexed_chunks": str(indexed)}

def search_code(query: str, repository_id: str, branch: str, n_results: int = 5) -> dict[str, list[dict]]:
    """Search for relevant code snippets in the indexed repository."""
    collection_name = f"repo_{repository_id}_{branch}".replace("/", "_")[:63]

    try:
        collection = _chroma_client.get_collection(collection_name)
    except Exception:
        raise FileNotFoundError("Collection not found. Codebase indexing is required.")

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
            results["metadatas"][0],
            results["distances"][0],
        ):
            if not _should_ignore(meta.get("file_path", "")):
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