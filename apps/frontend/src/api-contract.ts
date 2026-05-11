const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL ?? apiBaseUrl;

export type UserRead = {
  id: string;
  email: string;
  name: string | null;
  daily_run_quota: number;
  created_at: string;
};

export type RepositoryRead = {
  id: string;
  github_owner: string;
  github_repo: string;
  default_branch: string;
  language: string | null;
  clone_url: string;
  created_at: string;
};

export type TaskCreate = {
  repository_id: string;
  instruction: string;
  target_branch: string;
  parent_run_id?: string | null;
  follow_up_instruction?: string | null;
};

export type TaskRead = {
  id: string;
  user_id: string;
  repository_id: string;
  title: string;
  instruction: string;
  target_branch: string;
  created_at: string;
  updated_at: string;
};

export type AgentRunStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export type AgentRunRead = {
  id: string;
  task_id: string;
  status: AgentRunStatus;
  parent_run_id: string | null;
  follow_up_instruction: string | null;
  branch_name: string | null;
  model_id: string;
  prompt_version: string;
  max_turns: number;
  total_tool_calls: number | null;
  total_tokens: number | null;
  cost_usd: string | null;
  error_message: string | null;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  tool_calls: ToolCallRead[];
  pull_request: PullRequestRead | null;
};

export type EventType = "status_change" | "plan" | "message" | "tool_call" | "tool_result" | "error" | "summary";

export type AgentRunEventRead = {
  id: string;
  agent_run_id: string;
  sequence: number;
  event_type: EventType;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ToolCallRead = {
  id: string;
  agent_run_id: string;
  sequence: number;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output: Record<string, unknown> | null;
  status: "pending" | "success" | "error";
  error_message: string | null;
  duration_ms: number | null;
  started_at: string | null;
  finished_at: string | null;
};

export type PullRequestRead = {
  id: string;
  agent_run_id: string;
  repository_id: string;
  github_pr_number: number;
  title: string;
  body: string;
  head_branch: string;
  base_branch: string;
  url: string;
  state: "open" | "closed" | "merged" | "draft";
  merged_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardRead = {
  repository_count: number;
  active_run_count: number;
  succeeded_run_count: number;
  today_run_count: number;
  daily_run_quota: number;
};

export type FeedbackCreate = {
  instruction: string;
};

export type DiffFileRead = {
  file_path: string;
  status: "added" | "removed" | "modified" | "renamed";
  additions: number;
  deletions: number;
  patch: string | null;
};

export type AgentRunWebSocketFrame = {
  type: EventType;
  payload: Record<string, unknown>;
  sequence: number;
};

export type TerminalWebSocketFrame = {
  type: "terminal";
  status: Extract<AgentRunStatus, "succeeded" | "failed" | "cancelled">;
  pr_url: string | null;
  pr_number: number | null;
};

export type ApiErrorResponse =
  | { detail: string }
  | {
      detail: Array<{
        loc: Array<string | number>;
        msg: string;
        type: string;
      }>;
    };

export const apiEndpoints = {
  signup: "/auth/signup",
  login: "/auth/login",
  logout: "/auth/logout",
  me: "/me",
  githubCredentials: "/me/github-credentials",
  githubCredential: (id: string) => `/me/github-credentials/${id}`,
  repositories: "/repositories",
  repository: (id: string) => `/repositories/${id}`,
  tasks: "/tasks",
  tasksWithLimit: (limit: number) => `/tasks?limit=${limit}`,
  task: (task_id: string) => `/tasks/${task_id}`,
  agentRun: (id: string) => `/agent_runs/${id}`,
  agentRunEvents: (id: string, limit?: number) => `/agent_runs/${id}/events${limit ? `?limit=${limit}` : ""}`,
  agentRunPullRequest: (id: string) => `/agent_runs/${id}/pull_request`,
  agentRunDiff: (id: string) => `/agent_runs/${id}/diff`,
  agentRunFeedback: (id: string) => `/agent_runs/${id}/feedback`,
  dashboard: "/me/dashboard",
  agentRunWebSocket: (id: string) => `/ws/agent_runs/${id}`,
} as const;

export class ApiClientError extends Error {
  status: number;
  detail: ApiErrorResponse | null;

  constructor(status: number, detail: ApiErrorResponse | null) {
    super(getApiErrorMessage(detail) ?? `Request failed with status ${status}`);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

function getApiErrorMessage(detail: ApiErrorResponse | null) {
  if (!detail) {
    return null;
  }

  if (typeof detail.detail === "string") {
    return detail.detail;
  }

  return detail.detail.map((item) => item.msg).join(", ");
}

async function fetchJson<TResponse>(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    const detail = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new ApiClientError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export function createAgentRunWebSocket(id: string) {
  const fallbackOrigin = typeof window === "undefined" ? "http://localhost" : window.location.origin;
  const url = new URL(apiEndpoints.agentRunWebSocket(id), wsBaseUrl || fallbackOrigin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";

  return new WebSocket(url);
}

export const patchApi = {
  signup: (body: { email: string; password: string; name?: string | null }) =>
    fetchJson<UserRead>(apiEndpoints.signup, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: (body: { email: string; password: string }) =>
    fetchJson<UserRead>(apiEndpoints.login, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  logout: () =>
    fetchJson<void>(apiEndpoints.logout, {
      method: "POST",
    }),
  getMe: () => fetchJson<UserRead>(apiEndpoints.me),
  createGitHubCredential: (body: { token: string }) =>
    fetchJson<UserRead>(apiEndpoints.githubCredentials, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteGitHubCredential: (id: string) =>
    fetchJson<void>(apiEndpoints.githubCredential(id), {
      method: "DELETE",
    }),
  listRepositories: () => fetchJson<RepositoryRead[]>(apiEndpoints.repositories),
  createRepository: (body: { owner: string; name: string }) =>
    fetchJson<RepositoryRead>(apiEndpoints.repositories, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteRepository: (id: string) =>
    fetchJson<void>(apiEndpoints.repository(id), {
      method: "DELETE",
    }),
  createTask: (body: TaskCreate) =>
    fetchJson<AgentRunRead>(apiEndpoints.tasks, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listTasks: (limit = 50) => fetchJson<TaskRead[]>(apiEndpoints.tasksWithLimit(limit)),
  getTask: (task_id: string) => fetchJson<TaskRead>(apiEndpoints.task(task_id)),
  getAgentRun: (id: string) => fetchJson<AgentRunRead>(apiEndpoints.agentRun(id)),
  getAgentRunEvents: (id: string, limit = 50) => fetchJson<AgentRunEventRead[]>(apiEndpoints.agentRunEvents(id, limit)),
  getAgentRunPullRequest: (id: string) => fetchJson<PullRequestRead>(apiEndpoints.agentRunPullRequest(id)),
  getAgentRunDiff: (id: string) => fetchJson<DiffFileRead[]>(apiEndpoints.agentRunDiff(id)),
  submitFeedback: (id: string, body: FeedbackCreate) =>
    fetchJson<AgentRunRead>(apiEndpoints.agentRunFeedback(id), {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getDashboard: () => fetchJson<DashboardRead>(apiEndpoints.dashboard),
};
