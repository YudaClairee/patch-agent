# API Contract — Stream 4

> **Status: LOCKED for response/request field names and core schema shapes.**
> This file is the Stream 4 source of truth for endpoint behavior, auth/ownership rules, WebSocket frames, and the typed API surface consumed by Stream 5.
>
> If a field name or type changes after this point, coordinate with Stream 5 before merging.

---

## Ownership Boundaries

Stream 4 owns:

- Task submission endpoints.
- Agent run read endpoints.
- Agent run event history endpoint.
- Pull request lookup endpoint for a run.
- GitHub PR diff endpoint for a run.
- Feedback/follow-up endpoint.
- WebSocket relay for live agent run events.
- Dashboard summary endpoint.
- The Pydantic response/request schemas used by these endpoints.
- Route-level auth and ownership enforcement for all Stream 4 endpoints.

Stream 4 reuses but does **not** own:

- Auth/session implementation from **Stream 1**:
  - `POST /auth/signup`
  - `POST /auth/login`
  - `POST /auth/logout`
  - `GET /me`
  - `POST /me/github-credentials`
  - `DELETE /me/github-credentials/{id}`
  - `current_user`
  - `current_user_ws`
- Repository connection/indexing implementation from **Stream 2**:
  - `GET /repositories`
  - `POST /repositories`
  - `DELETE /repositories/{id}`
  - Repository validation against GitHub
  - Codebase indexing in Chroma
- Agent execution, Redis publisher, event production, PR creation, and sandboxing from **Stream 3**.
- Frontend rendering and client-side typed hooks from **Stream 5**.

Important note for Stream 5:

- Use Stream 2's `GET /repositories` to populate repository pickers.
- Use Stream 4's `POST /tasks` to submit coding tasks against a selected repository.

---

## Endpoint List — Owned by Stream 4

| Method | Path                            | Query Params | Request Body     | Response                         |
| ------ | ------------------------------- | ------------ | ---------------- | -------------------------------- |
| `POST` | `/tasks`                        | —            | `TaskCreate`     | `AgentRunRead` (201)             |
| `GET`  | `/tasks`                        | `limit?`     | —                | `TaskRead[]`                     |
| `GET`  | `/tasks/{task_id}`              | —            | —                | `TaskRead`                       |
| `GET`  | `/agent_runs`                   | `limit?`     | —                | `AgentRunListItemRead[]`         |
| `GET`  | `/agent_runs/{id}`              | —            | —                | `AgentRunRead`                   |
| `GET`  | `/agent_runs/{id}/events`       | `limit?`     | —                | `AgentRunEventRead[]`            |
| `GET`  | `/agent_runs/{id}/pull_request` | —            | —                | `PullRequestRead`                |
| `GET`  | `/agent_runs/{id}/diff`         | —            | —                | `DiffFileRead[]`                 |
| `POST` | `/agent_runs/{id}/feedback`     | —            | `FeedbackCreate` | `AgentRunRead` (201)             |
| `GET`  | `/me/dashboard`                 | —            | —                | `DashboardRead`                  |
| `WS`   | `/ws/agent_runs/{id}`           | —            | —                | `AgentRunWebSocketFrame` stream  |

---

## Related Endpoint List — Not Owned by Stream 4

These endpoints are listed here only so Stream 4 and Stream 5 developers understand cross-stream dependencies. Do **not** implement these in Stream 4 unless the owning stream explicitly delegates them.

### Stream 1 — Auth and GitHub PAT

| Method   | Path                              | Owner    | Notes                              |
| -------- | --------------------------------- | -------- | ---------------------------------- |
| `POST`   | `/auth/signup`                    | Stream 1 | Creates user + auth cookie         |
| `POST`   | `/auth/login`                     | Stream 1 | Sets httpOnly auth cookie          |
| `POST`   | `/auth/logout`                    | Stream 1 | Clears auth cookie                 |
| `GET`    | `/me`                             | Stream 1 | Current user profile               |
| `GET`    | `/me/github-credentials`          | Stream 1 | Lists current user's GitHub PAT metadata |
| `POST`   | `/me/github-credentials`          | Stream 1 | Stores encrypted GitHub PAT        |
| `DELETE` | `/me/github-credentials/{id}`     | Stream 1 | Revokes credential                 |

### Stream 2 — Repository Connection and Indexing

| Method   | Path                     | Owner    | Notes                                        |
| -------- | ------------------------ | -------- | -------------------------------------------- |
| `GET`    | `/repositories`          | Stream 2 | Current user's connected repositories        |
| `POST`   | `/repositories`          | Stream 2 | Body `{ owner, name }`, connects repository  |
| `DELETE` | `/repositories/{id}`     | Stream 2 | Disconnects current user's repository        |

`RepositoryRead` is included below because Stream 5 needs a stable type for repository pickers, but Stream 2 owns the route implementation.

---

## Global Auth and Ownership Rules

All Stream 4 HTTP endpoints require Stream 1's cookie-based auth via `Depends(current_user)`.

All Stream 4 WebSocket connections require Stream 1's cookie-based WebSocket auth via `current_user_ws` during the handshake.

### Ownership rules

Stream 4 must enforce these rules at the route/service boundary:

- A user can only list their own tasks.
- A user can only read a task where `Task.user_id == current_user.id`.
- A user can only create a task for a repository where `Repository.user_id == current_user.id`.
- A user can only read an agent run if its task belongs to the current user.
- A user can only read events for an agent run if its task belongs to the current user.
- A user can only read pull request data for an agent run if its task belongs to the current user.
- A user can only fetch a diff for an agent run if its task belongs to the current user.
- A user can only submit feedback for an agent run if its task belongs to the current user.
- A user can only open a WebSocket to an agent run if its task belongs to the current user.
- A user can only use `parent_run_id` if that parent run belongs to the current user.

### Missing vs foreign resources

For security, Stream 4 should return `404 Not Found` for both:

- Resource does not exist.
- Resource exists but belongs to another user.

This prevents leaking information about other users' resources.

---

## Query Parameters and Pagination

Pagination is intentionally minimal for v1.

### `limit`

Applies to:

- `GET /tasks`
- `GET /agent_runs`
- `GET /agent_runs/{id}/events`

Rules:

- Optional.
- Default: `50`.
- Minimum: `1`.
- Maximum: `100`.
- If `limit > 100`, the server should clamp it to `100`.
- If `limit < 1` or not an integer, the server should return `422`.

There is no cursor or offset in v1.

---

## Validation Rules

These rules are part of Stream 4's API behavior. They may be implemented with Pydantic validators, route-level checks, or service-level checks.

### UUID fields

Fields and path params marked as UUID must be valid UUID strings.

Invalid UUIDs should return `422`.

### Text fields

`TaskCreate.instruction`:

- Required.
- Trimmed before validation.
- Must not be empty or whitespace-only.
- Recommended maximum length: `20000` characters.

`TaskCreate.target_branch`:

- Required.
- Trimmed before validation.
- Must not be empty or whitespace-only.
- Maximum length: `255` characters.

`TaskCreate.follow_up_instruction`:

- Optional.
- If provided, trim before validation.
- If provided, must not be whitespace-only.
- Recommended maximum length: `20000` characters.

`FeedbackCreate.instruction`:

- Required.
- Trimmed before validation.
- Must not be empty or whitespace-only.
- Recommended maximum length: `20000` characters.

### Git branch safety

`target_branch` is user input and must never be concatenated into shell commands.

If a subprocess is needed, use safe argument arrays instead of shell string concatenation.

---

## Schemas

### `UserRead`

Owned by Stream 1. Included for shared typing only.

```ts
{
  id: string;                    // UUID
  email: string;
  name: string | null;
  daily_run_quota: number;
  created_at: string;            // ISO datetime
}
```

### `RepositoryRead`

Owned by Stream 2. Included for Stream 5 repository picker typing.

```ts
{
  id: string;                    // UUID
  github_owner: string;
  github_repo: string;
  default_branch: string;
  language: string | null;
  clone_url: string;
  created_at: string;            // ISO datetime
}
```

### `TaskCreate` — Request Body

Used by `POST /tasks`.

```ts
{
  repository_id: string;          // UUID
  instruction: string;
  target_branch: string;
  parent_run_id?: string | null;  // UUID, only for follow-up-compatible task creation
  follow_up_instruction?: string | null;
}
```

### `TaskRead`

```ts
{
  id: string;                     // UUID
  user_id: string;                // UUID
  repository_id: string;          // UUID
  title: string;
  instruction: string;
  target_branch: string;
  created_at: string;             // ISO datetime
  updated_at: string;             // ISO datetime
}
```

### `AgentRunRead`

```ts
{
  id: string;                     // UUID
  task_id: string;                // UUID
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  parent_run_id: string | null;   // UUID or null
  follow_up_instruction: string | null;
  branch_name: string | null;
  model_id: string;
  prompt_version: string;
  max_turns: number;
  total_tool_calls: number | null;
  total_tokens: number | null;
  cost_usd: string | null;        // Decimal serialized as string
  error_message: string | null;
  queued_at: string;              // ISO datetime
  started_at: string | null;      // ISO datetime or null
  finished_at: string | null;     // ISO datetime or null
  tool_calls: ToolCallRead[];     // populated by GET /agent_runs/{id}; empty array otherwise
  pull_request: PullRequestRead | null;
}
```

Serialization rule:

- `cost_usd` must be serialized as a JSON string when present, not as a JSON number.

### `PullRequestSummaryRead`

Used by `AgentRunListItemRead` so dashboards can link to PR-aware routes without fetching every run detail.

```ts
{
  github_pr_number: number;
  title: string;
  url: string;
  state: "open" | "closed" | "merged" | "draft";
}
```

### `AgentRunListItemRead`

Returned by `GET /agent_runs`.

```ts
{
  id: string;                     // UUID
  task_id: string;                // UUID
  status: "queued" | "running" | "succeeded" | "failed" | "cancelled";
  branch_name: string | null;
  queued_at: string;              // ISO datetime
  started_at: string | null;      // ISO datetime or null
  finished_at: string | null;     // ISO datetime or null
  pull_request: PullRequestSummaryRead | null;
}
```

### `GitHubCredentialRead`

Owned by Stream 1. Included so Stream 5 can render credential status and revoke actions.

```ts
{
  id: string;                     // UUID
  github_username: string;
  token_scopes: string;
  created_at: string;             // ISO datetime
  last_used_at: string | null;    // ISO datetime or null
  revoked_at: string | null;      // ISO datetime or null
}
```

### `AgentRunEventRead`

Returned by `GET /agent_runs/{id}/events`.

```ts
{
  id: string;                     // UUID
  agent_run_id: string;           // UUID
  sequence: number;
  event_type: EventType;
  payload: Record<string, any>;
  created_at: string;             // ISO datetime
}
```

### `EventType`

Defined by the backend enum `src.models.enums.EventType`. Stream 3 publishes these event types, Stream 4 stores/relays them, and Stream 5 renders them.

Stream 4 must not invent event names outside this enum. If Stream 3 adds or removes event types, update both `src.models.enums.EventType` and this table, then coordinate with Stream 5.

| Value           | Description                         | Payload keys                          |
| --------------- | ----------------------------------- | ------------------------------------- |
| `status_change` | Agent run status transition         | `{ old_status, new_status }`          |
| `plan`          | Agent generated or updated its plan | `{ text }`                            |
| `message`       | Agent/user-facing message chunk     | `{ text }`                            |
| `tool_call`     | Agent calls a tool                  | `{ tool_name, tool_input }`           |
| `tool_result`   | Tool returns output                 | `{ tool_name, tool_output, success }` |
| `error`         | Error occurred                      | `{ message }`                         |
| `summary`       | Agent produces a summary            | `{ text }`                            |

`plan` and `message` may be optional in early Stream 3 implementations, but they are valid public event types because they exist in the backend enum and `AgentRunEventRead.event_type` uses that enum.

### `ToolCallRead`

```ts
{
  id: string;                     // UUID
  agent_run_id: string;           // UUID
  sequence: number;
  tool_name: string;
  tool_input: Record<string, any>;
  tool_output: Record<string, any> | null;
  status: "pending" | "success" | "error";
  error_message: string | null;
  duration_ms: number | null;
  started_at: string | null;      // ISO datetime or null
  finished_at: string | null;     // ISO datetime or null
}
```

### `PullRequestRead`

```ts
{
  id: string;                     // UUID
  agent_run_id: string;           // UUID
  repository_id: string;          // UUID
  github_pr_number: number;
  title: string;
  body: string;
  head_branch: string;
  base_branch: string;
  url: string;
  state: "open" | "closed" | "merged" | "draft";
  merged_at: string | null;       // ISO datetime or null
  created_at: string;             // ISO datetime
  updated_at: string;             // ISO datetime
}
```

This matches the backend enum `src.models.enums.PRState`. Stream 5 should render `draft` as a valid PR state if it appears.

### `DashboardRead`

```ts
{
  repository_count: number;
  active_run_count: number;       // AgentRun status queued or running
  succeeded_run_count: number;
  today_run_count: number;        // From usage_records for the agreed quota timezone
  daily_run_quota: number;        // From users.daily_run_quota
}
```

### `FeedbackCreate` — Request Body

Used by `POST /agent_runs/{id}/feedback`.

```ts
{
  instruction: string;
}
```

Response:

- Returns `AgentRunRead` with status `201`.
- Response is a new child run.
- Child run has a new `id`.
- Child run has `parent_run_id` set to the `{id}` path parameter.
- Stream 5 should navigate to `/run/{new_run_id}` after submit.

### `DiffFileRead`

Returned by `GET /agent_runs/{id}/diff`.

```ts
{
  file_path: string;
  status: "added" | "removed" | "modified" | "renamed";
  additions: number;
  deletions: number;
  patch: string | null;           // Unified diff text from GitHub, may be null for large/binary files
}
```

---

## Endpoint Behavior — Stream 4

### `POST /tasks`

Creates a task submission and queues an agent run.

Normal task creation:

- Validate current user via Stream 1 `current_user`.
- Validate `repository_id` belongs to current user.
- Create a `Task` row.
- Create an `AgentRun` row with `status = "queued"`.
- Enqueue Stream 3's `dispatch_agent_run(agent_run_id)` Celery task.
- Return `AgentRunRead` with `201`.

Follow-up-compatible behavior using `parent_run_id`:

- This path exists because `TaskCreate` supports `parent_run_id`.
- The preferred UI follow-up endpoint is still `POST /agent_runs/{id}/feedback`.
- If `parent_run_id` is provided, validate the parent run belongs to current user.
- Do not create a new `Task` row.
- Reuse the parent run's task.
- The new run must inherit the parent run's `branch_name`.
- `repository_id` must match the parent task's repository or the request must be rejected.
- `follow_up_instruction` should be used as the child run's follow-up instruction. If omitted, the server may use `instruction` as the follow-up instruction.

Failure cases:

- `401` if unauthenticated.
- `404` if repository or parent run does not exist or belongs to another user.
- `422` if request body is invalid.

### `GET /tasks`

Returns current user's tasks.

Rules:

- Uses `current_user`.
- Returns only tasks where `Task.user_id == current_user.id`.
- Ordered by newest first.
- Supports `limit` query param.

### `GET /tasks/{task_id}`

Returns one task owned by the current user.

Rules:

- Uses `current_user`.
- Return `404` if task is missing or belongs to another user.

### `GET /agent_runs`

Returns recent agent runs owned by the current user for dashboard and home navigation.

Rules:

- Uses `current_user`.
- Returns only runs whose task belongs to current user.
- Ordered by newest queued run first.
- Supports `limit` query param with the same validation rules as `GET /tasks`.
- Includes PR summary when a pull request exists for the run or parent chain.

### `GET /agent_runs/{id}`

Returns one agent run owned by the current user.

Rules:

- Uses `current_user`.
- Return `404` if run is missing or belongs to another user.
- Include `tool_calls` and `pull_request` in the response.

### `GET /agent_runs/{id}/events`

Returns milestone event history from Postgres.

Rules:

- Uses `current_user`.
- Return `404` if run is missing or belongs to another user.
- Ordered by `sequence ASC`.
- Supports `limit` query param.

### `GET /agent_runs/{id}/pull_request`

Returns the pull request linked to an agent run.

Rules:

- Uses `current_user`.
- Return `404` if run is missing or belongs to another user.
- Return `404` if no pull request exists for the run or its parent chain.
- For follow-up runs, the implementation may walk the parent chain to find the original PR.

### `GET /agent_runs/{id}/diff`

Fetches PR file changes from GitHub on demand.

Rules:

- Uses `current_user`.
- Return `404` if run is missing or belongs to another user.
- Return `404` if no linked PR exists for the run or parent chain.
- Use the current user's decrypted GitHub PAT from Stream 1.
- Fetch from GitHub API using PyGithub.
- No DB caching in v1.
- Return the same file set as the GitHub PR "Files changed" tab when possible.

External failure cases:

- `401` if the user is authenticated to P.A.T.C.H. but has no usable GitHub credential.
- `403` if GitHub denies access with the user's credential.
- `404` if GitHub cannot find the repository or PR.
- `502` if GitHub API fails unexpectedly.

### `POST /agent_runs/{id}/feedback`

Creates a child agent run that pushes more commits to the same PR branch.

Rules:

- Uses `current_user`.
- Validate parent run belongs to current user.
- Validate parent run status is `succeeded`.
- Create a child `AgentRun` with:
  - `parent_run_id = {id}`
  - `follow_up_instruction = body.instruction`
  - `status = "queued"`
  - same task as parent
  - branch inherited from parent run
- Enqueue Stream 3's `dispatch_agent_run(child_run_id)` Celery task.
- Return child `AgentRunRead` with `201`.

Failure cases:

- `401` if unauthenticated.
- `404` if parent run does not exist or belongs to another user.
- `409` if parent run is not `succeeded`.
- `422` if request body is invalid.

### `GET /me/dashboard`

Returns current user's dashboard counts.

Rules:

- Uses `current_user`.
- `repository_count`: count of repositories owned by current user.
- `active_run_count`: count of current user's agent runs with `queued` or `running` status.
- `succeeded_run_count`: count of current user's agent runs with `succeeded` status.
- `today_run_count`: current user's usage count for the agreed daily quota date.
- `daily_run_quota`: from current user row.

Timezone note:

- The backend should use the same timezone rule for writing `usage_records.date` and reading `today_run_count`.
- Recommended default is UTC.

---

## WebSocket — `/ws/agent_runs/{id}`

Owned by Stream 4. Event production is owned by Stream 3.

### Auth and ownership

- Authenticate at WebSocket handshake using Stream 1's `current_user_ws`.
- Validate the requested agent run belongs to the authenticated user.
- If auth or ownership fails, reject/close the connection.

### Subscription

- Subscribe to Redis channel `agent_run:<id>`.
- Redis channel naming is owned by Stream 3 and locked for Stream 4 consumption.
- Forward each event to the client as JSON.
- On client disconnect, unsubscribe and close cleanly.
- On terminal run status, send a terminal frame and close.

### `AgentRunWebSocketFrame`

All non-terminal frames sent to the browser must use this shape:

```ts
{
  type: EventType;
  payload: Record<string, any>;
  sequence: number;
}
```

### `TerminalWebSocketFrame`

Terminal frame follows the exact Stream 4 route requirement from `stream4.md`:

```ts
{
  type: "terminal";
  status: "succeeded" | "failed" | "cancelled";
  pr_url: string | null;
  pr_number: number | null;
}
```

`TerminalWebSocketFrame` intentionally does not use the normal `{ type, payload, sequence }` event envelope because `stream4.md` explicitly defines the final frame as `{ type: "terminal", status, pr_url, pr_number }`.

After receiving `type === "terminal"`, Stream 5 should stop waiting for more frames. If the terminal frame contains `pr_url`, Stream 5 can show the PR link.

After feedback submission, Stream 5 must open a new WebSocket connection using the child run id returned by `POST /agent_runs/{id}/feedback`.

---

## Standard Error Responses

Stream 4 should use FastAPI-compatible error shapes.

### Simple error

```ts
{
  detail: string;
}
```

Examples:

- `{ "detail": "Not authenticated" }`
- `{ "detail": "Task not found" }`
- `{ "detail": "Agent run not found" }`
- `{ "detail": "Parent run must be succeeded before feedback" }`

### Validation error

FastAPI's default validation error shape is acceptable:

```ts
{
  detail: Array<{
    loc: Array<string | number>;
    msg: string;
    type: string;
  }>;
}
```

### Status code guide

| Status | Meaning                                                                 |
| ------ | ----------------------------------------------------------------------- |
| `200`  | Successful read                                                         |
| `201`  | Resource created or child run queued                                    |
| `401`  | Missing/invalid auth cookie, or no usable GitHub credential for diff    |
| `403`  | GitHub credential exists but GitHub denies access                       |
| `404`  | Resource missing or belongs to another user                             |
| `409`  | Business state conflict, e.g. feedback on a non-succeeded parent run    |
| `422`  | Invalid request body, path param, or query param                        |
| `502`  | GitHub API or upstream dependency failed unexpectedly                   |
| `500`  | Unexpected backend error                                                |

---

## Notes for Stream 5

- All IDs are UUID strings.
- All datetime fields are ISO datetime strings.
- `cost_usd` is a string when present. Convert with `parseFloat` only for display.
- All Stream 4 HTTP endpoints require auth cookie. Use `credentials: "include"` in `fetch`/axios.
- WebSocket auth uses the same browser cookie at handshake.
- `GET /tasks`, `GET /agent_runs`, and `GET /agent_runs/{id}/events` support `?limit=N`, default 50, max 100.
- Use Stream 2's `GET /repositories` for repository pickers.
- Use Stream 1's auth endpoints for signup/login/logout/current user/PAT connection.
- Use this file as the Stream 4 source of truth for mock data and TypeScript types.

---

## Coordination Notes

- **Stream 1** owns auth, `current_user`, `current_user_ws`, encrypted GitHub PAT storage, and PAT decryption.
- **Stream 2** owns repository connection, repository listing, repository deletion, indexing, and Chroma setup.
- **Stream 3** owns container dispatch, Redis event publishing, event payload production, agent execution, PR creation, and follow-up commits.
- **Stream 4** owns the endpoints and WebSocket relay in this document and must enforce auth/ownership on them.
- **Stream 5** consumes the schemas and endpoints in this document.

If any stream changes a shared contract, update this document and coordinate before frontend implementation depends on it.
