# Stream 3 — Agent Runtime & Orchestration: Implementation Plan

## Overview

Stream 3 owns the end-to-end agent execution lifecycle:
- A user submits a task → Celery dispatches a fresh Docker container → the agent clones the repo, loops (read → plan → write → test), calls `submit_pull_request` → the container exits → the host worker finalizes the DB row.

Diff review is **post-PR**. Follow-up changes are new `AgentRun` rows linked via `parent_run_id`.

---

## Current State

| Area | State |
|---|---|
| `src/ai/agent.py` | Exists — `run_agent_stream` yields SSE strings only, no DB persistence, no container awareness |
| `src/ai/tools/` | All tools exist and are correct for `/workspace` inside a container |
| `src/models/` | Fully defined — `AgentRun`, `AgentRunEvent`, `ToolCall`, `PullRequest` with `parent_run_id` |
| `src/services/` | **Empty** — no Celery, no Docker, no events |
| `src/ai/tools/pr_tools.py` | **Missing** — `submit_pull_request` tool does not exist |
| `docker-compose.yml` | Has postgres + valkey + backend + frontend. No Celery worker, no agent image |
| Alembic migrations | `versions/` is empty — migrations need to be generated separately |
| `decrypt_token` | Not implemented — infrastructure is in place (`fernet_key` + `GithubCredential.encrypted_token`) |

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Docker socket vs DinD | **Docker socket mount** | Simpler, fast to set up, good enough for MVP |
| `decrypt_token` | Implement in stream 3 | It's 3 lines of Fernet; don't block on Stream 1 |
| ChromaDB in-container | `ENV CHROMA_PERSIST_DIR=/tmp/chromadb` | PersistentClient works via tmpfs; Stream 2 migrates to HttpClient |
| Precondition guard for PR | Query Postgres `tool_calls` table | Cleaner than module-level state, already being persisted by runner |
| `workspace_path` in `run_agent_stream` | **Keep optional, default `/workspace`** | Allows tests to override without patching the module |
| Network isolation | Per-run bridge network, no iptables egress | Full egress restriction is Linux/iptables specific — too complex for MVP |
| `agent.py` `_build_agent` param | Drop `workspace_path`, hardcode `/workspace` | Per spec — path is constant inside container |

---

## Files to Create / Modify

```
apps/backend/
├── Dockerfile.agent                     # NEW
├── src/
│   ├── ai/
│   │   ├── agent.py                     # MODIFY
│   │   ├── runner.py                    # NEW
│   │   └── tools/
│   │       └── pr_tools.py              # NEW
│   ├── core/
│   │   └── config.py                    # MODIFY (add Docker/sandbox settings)
│   └── services/
│       ├── __init__.py                  # MODIFY (add exports)
│       ├── agent_runner.py              # NEW
│       ├── sandboxing.py                # NEW
│       └── events.py                    # NEW
├── tests/
│   └── agent/
│       └── test_runner_smoke.py         # NEW
docker-compose.yml                       # MODIFY
```

---

## Implementation Steps

### Step 1 — Infrastructure Layer

**`src/services/events.py`**
- Single function: `publish_event(agent_run_id: str, payload: dict) -> None`
- Uses `redis.Redis.from_url(settings.redis_url)`
- Publishes `json.dumps(payload)` to channel `agent_run:<id>`
- Channel name is locked here — Stream 4 subscribes on this exact name for its WebSocket relay

**`src/core/config.py`** — add new settings fields:
```
docker_agent_image: str = "patch/agent:latest"
agent_memory_limit: str = "2g"
agent_cpus: float = 1.0
agent_pids_limit: int = 512
agent_max_wall_time_sec: int = 900
```

---

### Step 2 — Docker Layer

**`src/services/sandboxing.py`**
- Function: `get_sandbox_options(agent_run_id: str) -> dict`
- Returns kwargs for `client.containers.run(...)`:
  - `mem_limit` from settings
  - `cpu_period=100000`, `cpu_quota=int(settings.agent_cpus * 100000)`
  - `pids_limit` from settings
  - `read_only=True`
  - `tmpfs={"/tmp": "rw,size=512m", "/workspace": "rw,exec,size=5g"}`
  - `network_mode` tied to a per-run bridge network created before the container starts
  - `detach=True`, `remove=False` (removed manually in `finally`)

**`apps/backend/Dockerfile.agent`**
- Base: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- Installs `git` (needed for cloning)
- Copies `pyproject.toml` + `uv.lock`, runs `uv sync --frozen --no-dev`
- Copies `src/`
- Sets `ENV CHROMA_PERSIST_DIR=/tmp/chromadb` (writable tmpfs path)
- Entry: `python -m src.ai.runner`

---

### Step 3 — New Tool: `src/ai/tools/pr_tools.py`

**`decrypt_token(credential: GithubCredential) -> str`**
- Uses `Fernet(settings.fernet_key.encode()).decrypt(credential.encrypted_token).decode()`

**`submit_pull_request(title: str, body: str) -> dict`**
- Reads `AGENT_RUN_ID`, `PARENT_RUN_ID`, `REPO_CLONE_URL`, `GITHUB_TOKEN` from env
- **Precondition guard** (raises `RuntimeError` on failure — agent retries):
  1. Query Postgres `tool_calls` where `agent_run_id = AGENT_RUN_ID` and `status = success`
  2. Assert `workspace_run_test` appears in successful tool names
  3. Assert `workspace_run_lint` appears in successful tool names
  4. Call `get_git_diff("/workspace")` — assert stdout is non-empty
- **Initial run** (no `PARENT_RUN_ID`):
  1. Derive branch: `patch/task-{agent_run_id}`
  2. `create_branch("/workspace", branch_name)`
  3. `commit_changes("/workspace", f"[P.A.T.C.H.] {title}")`
  4. `push_branch("/workspace", branch_name)`
  5. PyGithub: `repo.create_pull(title=f"[P.A.T.C.H.] {title}", body=body, head=branch_name, base=base_branch)`
  6. Write `AgentRun.branch_name` + new `PullRequest` row to Postgres
- **Follow-up run** (`PARENT_RUN_ID` is set):
  1. Branch already checked out (runner set it up)
  2. `commit_changes("/workspace", f"[P.A.T.C.H. follow-up] {title}")`
  3. `push_branch("/workspace", head_branch)`
  4. Find existing `PullRequest` row via `parent_run_id` → add PR comment via PyGithub
  5. No new PR opened

---

### Step 4 — Modify `src/ai/agent.py`

**`SYSTEM_PROMPT` rewrite** — autonomous mode:
- Explicit loop: search → read → plan → write → test → lint → `submit_pull_request`
- Must NOT call `submit_pull_request` until tests and lint have passed
- Never modify files outside `/workspace`
- Never read `.env`, `.pem`, `.key` files
- For follow-up runs: prompt augmented with parent run summary + `follow_up_instruction`

**`_build_agent(repository_id: str, branch: str)` — drop `workspace_path` param**:
- Hardcode `WORKSPACE = "/workspace"` as module constant
- Add `submit_pull_request_tool` closure to tool list
- 16 tools total (15 existing + `submit_pull_request`)

**`run_agent_stream(instruction, workspace_path="/workspace", repository_id="", branch="", agent_run_id="", follow_up_context=None)`**:
- Wrap `agent.run_stream(...)` with `asyncio.wait_for(timeout=settings.agent_max_wall_time_sec)`
- Enforce `max_turns=15` (already in place, now sourced from settings)
- On `asyncio.TimeoutError`: yield error event, let runner set status to `failed`
- Yield structured events: `status_change`, `tool_call`, `tool_result`, `summary`, `error`

---

### Step 5 — Container Entrypoint: `src/ai/runner.py`

Reads from env:
```
AGENT_RUN_ID, INSTRUCTION, REPO_CLONE_URL, BASE_BRANCH,
HEAD_BRANCH (follow-up only), GITHUB_TOKEN, OPENROUTER_API_KEY,
DATABASE_URL, REDIS_URL, REPOSITORY_ID, LANGFUSE_*, FERNET_KEY,
PARENT_RUN_ID (follow-up only), FOLLOW_UP_INSTRUCTION (follow-up only)
```

Execution flow:
1. Update `AgentRun.status = running`, `started_at = now()` in Postgres
2. Publish `{type: status_change, status: running}` to Redis
3. Clone repo: `git clone https://{GITHUB_TOKEN}@{REPO_CLONE_URL_WITHOUT_SCHEME} /workspace`
4. Checkout branch:
   - Initial run: `git checkout BASE_BRANCH`
   - Follow-up: `git checkout HEAD_BRANCH`
5. Loop over `run_agent_stream(...)`:
   - Each event → append `AgentRunEvent` row (with incrementing `sequence`) to Postgres
   - Each `tool_call` event → insert `ToolCall` row with `status=pending`
   - Each `tool_result` event → update matching `ToolCall` with `status`, `tool_output`, `duration_ms`, `finished_at`
   - Publish every event to Redis
6. On completion:
   - Update `AgentRun`: `status=succeeded`, `finished_at=now()`, `total_tool_calls`, `total_tokens`, `cost_usd`
7. On any exception:
   - Update `AgentRun`: `status=failed`, `error_message=str(e)`, `finished_at=now()`
   - Publish `{type: error, ...}` to Redis
   - Exit with code 1

---

### Step 6 — Host-side Celery: `src/services/agent_runner.py`

**Celery app definition** at module level using `settings.redis_url` as broker.

**`dispatch_agent_run(agent_run_id: str)` Celery task**:
1. Load `AgentRun` → `Task` → `Repository` → `GithubCredential` from Postgres
2. `decrypt_token(credential)` to get plaintext GitHub PAT
3. Build env dict — all vars that `runner.py` reads
4. Create per-run Docker network: `client.networks.create(f"patch_{agent_run_id}", driver="bridge")`
5. Get sandbox options from `sandboxing.py`
6. `container = client.containers.run(settings.docker_agent_image, environment=env, network=..., detach=True, **sandbox_opts)`
7. Update `AgentRun.container_id = container.id`, `celery_task_id = self.request.id`
8. `result = container.wait(timeout=settings.agent_max_wall_time_sec + 60)`
9. On non-zero exit AND status still `running`: set `status=failed`, `error_message="Container exited {code}"`
10. `finally`:
    - `container.remove(force=True)`
    - `client.networks.remove(f"patch_{agent_run_id}")`

**`docker-compose.yml` change** — add `celery_worker` service:
```yaml
celery_worker:
  build: ./apps/backend
  command: uv run celery -A src.services.agent_runner worker --loglevel=info --concurrency=2
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    DATABASE_URL: postgresql://postgres:postgres@postgres:5432/postgres
    REDIS_URL: redis://valkey:6379/0
  env_file:
    - ./apps/backend/.env
  depends_on:
    postgres:
      condition: service_healthy
    valkey:
      condition: service_healthy
  restart: unless-stopped
```

---

### Step 7 — Smoke Test: `tests/agent/test_runner_smoke.py`

- Stubs `docker.DockerClient` (mock container with `wait()` returning `{"StatusCode": 0}`)
- Stubs `run_agent_stream` with a deterministic async generator that yields:
  - `{type: tool_call, tool_name: workspace_write_file, ...}`
  - `{type: tool_result, ...}`
  - `{type: summary, content: "Done."}`
- Calls `dispatch_agent_run(str(agent_run_id))` directly (bypasses Celery broker)
- Asserts:
  - `AgentRun.status == RunStatus.succeeded`
  - `AgentRun.container_id` is set
  - `AgentRunEvent` rows exist with correct sequence
  - `container.remove()` was called (via mock assertion)

---

## Event Types Published to Redis (contract for Stream 4 & 5)

| Event type | Payload fields |
|---|---|
| `status_change` | `status` |
| `tool_call` | `tool_name`, `tool_input`, `sequence` |
| `tool_result` | `tool_name`, `tool_output`, `status`, `duration_ms`, `sequence` |
| `summary` | `content` |
| `error` | `error`, `traceback` |

---

## Out of Scope for Stream 3

- Auto-retry on container failure (user clicks retry → new `AgentRun` row)
- Cost tracking beyond writing `cost_usd` from OpenRouter usage headers
- Multi-region / GPU runners
- Alembic migration generation (run `alembic revision --autogenerate` separately)
- Full egress network restriction via iptables (Linux-specific, post-MVP)
- Stream 2's Chroma HttpClient migration (stream 3 uses PersistentClient via `/tmp/chromadb`)

---

## Coordination Notes

| Stream | Dependency |
|---|---|
| Stream 1 | `decrypt_token` implemented here; schema fields `parent_run_id`/`follow_up_instruction` already on `AgentRun` |
| Stream 2 | Chroma sidecar must be up before `search_code` works in-container; until then, the agent uses per-run PersistentClient at `/tmp/chromadb` |
| Stream 4 | Subscribes to `agent_run:<id>` Redis channel; event schema locked above |
| Stream 5 | Depends on `AgentRun` row shape and the event types above |

---

## Verification Checklist

- [ ] `docker build -t patch/agent -f apps/backend/Dockerfile.agent apps/backend/` succeeds
- [ ] `dispatch_agent_run` creates a container, it runs, exits 0, `AgentRun.status = succeeded`
- [ ] Container is removed after run (check `docker ps -a`)
- [ ] Per-run Docker network is cleaned up
- [ ] Follow-up run: commits to same branch, no new PR opened, PR comment added
- [ ] `cd apps/backend && uv run pytest tests/agent/`
- [ ] Events appear on Redis channel `agent_run:<id>` during a run
