from src.core.config import settings


def get_sandbox_options(agent_run_id: str) -> dict:
    """Return kwargs for docker client.containers.run() for a sandboxed agent container."""
    return {
        "mem_limit": settings.agent_memory_limit,
        "cpu_period": 100_000,
        "cpu_quota": int(settings.agent_cpus * 100_000),
        "pids_limit": settings.agent_pids_limit,
        "read_only": True,
        "tmpfs": {
            "/tmp": "rw,exec,nosuid,nodev,size=512m",
            "/workspace": "rw,exec,nosuid,nodev,size=5g",
            # rag_tools uses PersistentClient at /app/.data/chromadb (resolved from WORKDIR)
            "/app/.data": "rw,size=2g",
        },
        "network": f"patch_{agent_run_id}",
        "detach": True,
        "remove": False,
    }
