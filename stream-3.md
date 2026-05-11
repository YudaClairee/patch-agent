## Direction

P.A.T.C.H. is a pure autonomous coding agent. A user submits a task → the backend spawns a **fresh Docker container** → the agent loops (read → plan → write → test → iterate) → calls \`submit_pull_request\` → the container is destroyed.

Diff review is **post-PR**. After the PR exists, the user can request follow-up changes from our UI. Each follow-up is a **new** \`AgentRun\` linked via \`parent_run_id\` (already added to the model). When \`parent_run_id\` is set, the runner does **not** open a new PR — it checks out the parent run's \`branch_name\`, runs the loop, pushes another commit to that same branch, and exits. The PR stays open and grows.

This is the load-bearing stream. It owns: the agent image, the loop's "done" semantics, sandboxing, hard caps, and the host-side worker that watches containers and finalizes DB rows.

---

## Your task

### Goal
Dispatching an \`AgentRun\` (initial or follow-up) spawns a fresh container that runs the agent loop, publishes events to Redis, opens or pushes to a PR via \`submit_pull_request\`, and exits cleanly. The host-side Celery worker captures exit + finalizes the row regardless of outcome.

### Files to create

- \`apps/backend/Dockerfile.agent\` — separate image with \`uv\` + \`src/ai/\` + \`src/core/\` + \`src/models/\` + minimal deps. Entry: \`python -m src.ai.runner\`.

- \`apps/backend/src/ai/runner.py\` — entrypoint **inside** the container. Reads env: \`AGENT_RUN_ID\`, \`INSTRUCTION\`, \`REPO_CLONE_URL\`, \`BASE_BRANCH\`, \`HEAD_BRANCH\` (set when this is a follow-up run), \`GITHUB_TOKEN\`, \`OPENROUTER_API_KEY\`, \`BACKEND_URL\`, \`PARENT_RUN_ID\`, \`FOLLOW_UP_INSTRUCTION\`. Clones into \`/workspace\`, checks out the right branch, calls \`run_agent_stream\`, publishes events to Redis channel \`agent_run:<id>\`, persists structured milestones (status changes, tool_calls, summary, error) to Postgres directly.

- \`apps/backend/src/ai/tools/pr_tools.py\` — new \`submit_pull_request(title, body)\` tool.
  - **Initial run**: creates a new branch, commits + pushes, opens a PR via PyGithub. Writes \`AgentRun.branch_name\` and the matching \`PullRequest\` row.
  - **Follow-up run** (\`PARENT_RUN_ID\` set): commits + pushes to the existing \`branch_name\` from the parent run; does NOT open a new PR; appends a comment on the existing PR with the agent's summary.
  - **Precondition guard**: must have observed a successful \`run_test\` AND \`run_lint\` in the *current* turn; \`get_git_diff\` must be non-empty. Otherwise raises \`RuntimeError\` and the agent retries.

- \`apps/backend/src/services/agent_runner.py\` — host-side Celery task \`dispatch_agent_run(agent_run_id)\`. Uses the \`docker\` Python SDK to: build/pull the image, create a container with env injected (resolves \`GITHUB_TOKEN\` via Stream 1's \`decrypt_token\`), apply hard caps, watch via Redis pub/sub, capture exit, write \`started_at\`/\`finished_at\`/\`container_id\`/\`status\`/\`total_tool_calls\`/\`total_tokens\`/\`cost_usd\`/\`error_message\`. Always calls \`container.remove()\` in a \`finally\`.

- \`apps/backend/src/services/sandboxing.py\` — Docker run options factory:
  - \`--network\` on a per-run user-defined network with egress restricted to \`api.github.com\`, \`openrouter.ai\`, and the Chroma sidecar.
  - \`--read-only\` rootfs with \`/workspace\` and \`/tmp\` mounted writable.
  - \`--memory\`, \`--cpus\`, \`--pids-limit\` from settings.

- \`apps/backend/src/services/events.py\` — thin Redis publisher used by both runner and host. Channel name: \`agent_run:<id>\`.

- \`apps/backend/tests/agent/test_runner_smoke.py\` — end-to-end smoke against a fixture repo with a deterministic LLM stub.

### Files to modify

- \`apps/backend/src/ai/agent.py\`
  - \`SYSTEM_PROMPT\` (line 40) — rewrite for autonomous mode: loop, iterate, never modify \`/workspace\` outside the repo, must call \`submit_pull_request\` when done. For follow-ups, the prompt is augmented with the parent run's summary + the user's \`follow_up_instruction\`.
  - \`_build_agent\` (line 60) — drop the \`workspace_path\` parameter. Path is the constant \`/workspace\` inside the container. Inject \`submit_pull_request\` into the tool list.
  - \`run_agent_stream\` (line 155) — enforce hard caps: \`max_turns=15\`, \`max_tokens\` (configurable), \`max_wall_time_sec=900\`. On any cap hit, status → \`failed\`.

- \`docker-compose.yml\` — add the Celery worker service. Two options to choose between (document the choice in the PR): mount the host's Docker socket into the worker (simpler, weaker isolation) **or** docker-in-docker (stronger isolation, more setup).

### Reuses

- \`apps/backend/src/ai/tools/{file,git,rag,command}_tools.py\` are correct as-is *inside* the container — they were always meant for \`/workspace\`. No changes.
- Models \`AgentRun\` (with new \`parent_run_id\`, \`follow_up_instruction\`, \`cost_usd\`, \`prompt_version\` fields), \`PullRequest\`, \`AgentRunEvent\`, \`ToolCall\`.
- Stream 1's \`decrypt_token\`.
- Stream 2's Chroma \`HttpClient\` (the agent uses it from inside the container).

### Out of scope

- Auto-retry policy on container failure (user clicks "retry" → new \`AgentRun\` row → new PR or new commit on existing branch).
- Cost tracking beyond writing \`cost_usd\` from OpenRouter usage headers.
- Multi-region / GPU runners.

### Verification

1. \`docker build -t patch/agent -f apps/backend/Dockerfile.agent apps/backend/\`.
2. End-to-end smoke: dispatch an \`AgentRun\` against a fixture repo with a stubbed LLM that emits a deterministic plan + a single \`write_file\` + \`submit_pull_request\`. Expect: container starts, runs, opens a real PR on a test repo, exits 0; row finalized with \`status=succeeded\`; \`docker ps -a\` shows the container removed.
3. Follow-up run: dispatch a child \`AgentRun\` with \`parent_run_id\` set → another commit lands on the same branch; no new PR opened; PR comment added.
4. \`cd apps/backend && uv run pytest tests/agent/\`.

### Coordination

- **Stream 1** must ship \`decrypt_token\` first. Schema fields \`parent_run_id\` and \`follow_up_instruction\` are already on \`AgentRun\` (commit \`e402567\`).
- **Stream 2**'s Chroma sidecar must be up before agent runs can search code.
- **Stream 4** subscribes to \`agent_run:<id>\` over Redis pub/sub for its WebSocket relay; channel name is locked here.
- **Stream 5** depends on \`AgentRun\` row shape and the event types you publish (\`status_change\`, \`tool_call\`, \`tool_result\`, \`summary\`, \`error\`).