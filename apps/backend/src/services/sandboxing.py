from src.core.config import settings


def get_sandbox_options(agent_run_id: str) -> dict:
    """Return kwargs for docker client.containers.run() for a sandboxed agent container."""
    options = {
        "mem_limit": settings.agent_memory_limit,
        "cpu_period": 100_000,
        "cpu_quota": int(settings.agent_cpus * 100_000),
        "pids_limit": settings.agent_pids_limit,
        "read_only": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "tmpfs": {
            "/tmp": "rw,exec,nosuid,nodev,size=512m,mode=1777",
            "/workspace": "rw,exec,nosuid,nodev,size=5g,uid=10001,gid=10001,mode=1770",
        },
        "network": f"patch_{agent_run_id}",
        "detach": True,
        "remove": False,
    }
    if settings.agent_allow_host_gateway:
        options["extra_hosts"] = {"host.docker.internal": "host-gateway"}
    return options
