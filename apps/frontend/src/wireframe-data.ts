import { useQuery } from "@tanstack/react-query";
import {
  type AgentRunEventRead,
  type AgentRunRead,
  apiEndpoints,
  type DashboardRead,
  type DiffFileRead,
  type PullRequestRead,
  patchApi,
  type RepositoryRead,
  type TaskRead,
} from "./api-contract";

export const screens = [
  { id: "home", label: "Home" },
  { id: "dashboard", label: "Dashboard" },
  { id: "repo", label: "Repository" },
  { id: "task", label: "New Task" },
  { id: "run", label: "Agent Run" },
  { id: "diff", label: "Diff Review" },
  { id: "pr", label: "PR Result" },
] as const;

export type ScreenId = (typeof screens)[number]["id"];
export type SetActive = (screen: ScreenId) => void;

export const screenRoutes = {
  home: "/",
  dashboard: "/dashboard",
  repo: "/repo",
  task: "/task",
  run: "/run",
  diff: "/diff",
  pr: "/pr",
} as const satisfies Record<ScreenId, string>;

export const repositoryRows: RepositoryRead[] = [
  {
    id: "11111111-1111-4111-8111-111111111111",
    github_owner: "user",
    github_repo: "fastapi-auth-app",
    default_branch: "main",
    language: "Python",
    clone_url: "https://github.com/user/fastapi-auth-app.git",
    created_at: "2026-05-01T08:00:00.000Z",
  },
  {
    id: "22222222-2222-4222-8222-222222222222",
    github_owner: "user",
    github_repo: "patch-web",
    default_branch: "develop",
    language: "React",
    clone_url: "https://github.com/user/patch-web.git",
    created_at: "2026-05-02T08:00:00.000Z",
  },
  {
    id: "33333333-3333-4333-8333-333333333333",
    github_owner: "user",
    github_repo: "mini-ecommerce-api",
    default_branch: "main",
    language: "FastAPI",
    clone_url: "https://github.com/user/mini-ecommerce-api.git",
    created_at: "2026-05-03T08:00:00.000Z",
  },
];

export const taskRows: TaskRead[] = [
  {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    user_id: "99999999-9999-4999-8999-999999999999",
    repository_id: repositoryRows[0].id,
    title: "Add unit tests for login endpoint",
    instruction:
      "Tambahkan unit test untuk endpoint login. Pastikan test dapat dijalankan dengan pytest dan jangan ubah logic utama jika tidak perlu.",
    target_branch: "main",
    created_at: "2026-05-12T02:00:00.000Z",
    updated_at: "2026-05-12T02:00:00.000Z",
  },
  {
    id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    user_id: "99999999-9999-4999-8999-999999999999",
    repository_id: repositoryRows[1].id,
    title: "Fix navbar responsive bug",
    instruction: "Fix navbar responsive bug on tablet viewport.",
    target_branch: "develop",
    created_at: "2026-05-11T10:00:00.000Z",
    updated_at: "2026-05-11T10:00:00.000Z",
  },
  {
    id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    user_id: "99999999-9999-4999-8999-999999999999",
    repository_id: repositoryRows[2].id,
    title: "Refactor product service",
    instruction: "Refactor product service without changing public API behavior.",
    target_branch: "main",
    created_at: "2026-05-10T10:00:00.000Z",
    updated_at: "2026-05-10T10:00:00.000Z",
  },
];

export const pullRequestRow: PullRequestRead = {
  id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  agent_run_id: "12345678-1234-4234-8234-123456789abc",
  repository_id: repositoryRows[0].id,
  github_pr_number: 42,
  title: "Add unit tests for login endpoint",
  body: "Adds login endpoint tests and verifies existing auth behavior.",
  head_branch: "patch/task-102",
  base_branch: "main",
  url: "https://github.com/user/fastapi-auth-app/pull/42",
  state: "open",
  merged_at: null,
  created_at: "2026-05-12T02:12:00.000Z",
  updated_at: "2026-05-12T02:12:00.000Z",
};

export const agentRunRows: AgentRunRead[] = [
  {
    id: pullRequestRow.agent_run_id,
    task_id: taskRows[0].id,
    status: "running",
    parent_run_id: null,
    follow_up_instruction: null,
    branch_name: pullRequestRow.head_branch,
    model_id: "gpt-5-codex",
    prompt_version: "stream-4-v1",
    max_turns: 20,
    total_tool_calls: 4,
    total_tokens: 18240,
    cost_usd: "0.74",
    error_message: null,
    queued_at: "2026-05-12T02:02:00.000Z",
    started_at: "2026-05-12T02:03:00.000Z",
    finished_at: null,
    tool_calls: [
      {
        id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
        agent_run_id: pullRequestRow.agent_run_id,
        sequence: 3,
        tool_name: "run_command",
        tool_input: { command: "uv run pytest" },
        tool_output: { output: "12 passed in 2.41s" },
        status: "success",
        error_message: null,
        duration_ms: 2410,
        started_at: "2026-05-12T02:06:00.000Z",
        finished_at: "2026-05-12T02:06:03.000Z",
      },
    ],
    pull_request: pullRequestRow,
  },
  {
    id: "22345678-1234-4234-8234-123456789abc",
    task_id: taskRows[1].id,
    status: "running",
    parent_run_id: null,
    follow_up_instruction: null,
    branch_name: "patch/navbar-responsive",
    model_id: "gpt-5-codex",
    prompt_version: "stream-4-v1",
    max_turns: 20,
    total_tool_calls: null,
    total_tokens: null,
    cost_usd: null,
    error_message: null,
    queued_at: "2026-05-11T10:02:00.000Z",
    started_at: "2026-05-11T10:03:00.000Z",
    finished_at: null,
    tool_calls: [],
    pull_request: null,
  },
  {
    id: "32345678-1234-4234-8234-123456789abc",
    task_id: taskRows[2].id,
    status: "succeeded",
    parent_run_id: null,
    follow_up_instruction: null,
    branch_name: "patch/product-service",
    model_id: "gpt-5-codex",
    prompt_version: "stream-4-v1",
    max_turns: 20,
    total_tool_calls: 7,
    total_tokens: 24012,
    cost_usd: "1.06",
    error_message: null,
    queued_at: "2026-05-10T10:02:00.000Z",
    started_at: "2026-05-10T10:03:00.000Z",
    finished_at: "2026-05-10T10:18:00.000Z",
    tool_calls: [],
    pull_request: null,
  },
];

export const agentRunEventRows: AgentRunEventRead[] = [
  {
    id: "10000000-0000-4000-8000-000000000001",
    agent_run_id: agentRunRows[0].id,
    sequence: 1,
    event_type: "status_change",
    payload: { old_status: "queued", new_status: "running" },
    created_at: "2026-05-12T02:03:00.000Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000002",
    agent_run_id: agentRunRows[0].id,
    sequence: 2,
    event_type: "plan",
    payload: {
      text: "Inspect repository structure, read auth routes and tests, add login tests, run verification, then prepare diff.",
    },
    created_at: "2026-05-12T02:04:00.000Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000003",
    agent_run_id: agentRunRows[0].id,
    sequence: 3,
    event_type: "tool_call",
    payload: { tool_name: "run_command", tool_input: { command: "uv run pytest" } },
    created_at: "2026-05-12T02:06:00.000Z",
  },
  {
    id: "10000000-0000-4000-8000-000000000004",
    agent_run_id: agentRunRows[0].id,
    sequence: 4,
    event_type: "tool_result",
    payload: { tool_name: "run_command", tool_output: "12 passed in 2.41s", success: true },
    created_at: "2026-05-12T02:06:03.000Z",
  },
];

export const diffFileRows: DiffFileRead[] = [
  {
    file_path: "tests/test_auth.py",
    status: "added",
    additions: 82,
    deletions: 0,
    patch: "@@ -0,0 +1,82 @@\n+def test_login_success():\n+    ...",
  },
  {
    file_path: "app/auth/routes.py",
    status: "modified",
    additions: 4,
    deletions: 1,
    patch: "@@ -22,7 +22,10 @@\n-    return user\n+    return user",
  },
];

const dashboardRead: DashboardRead = {
  repository_count: repositoryRows.length,
  active_run_count: agentRunRows.filter((run) => run.status === "queued" || run.status === "running").length,
  succeeded_run_count: agentRunRows.filter((run) => run.status === "succeeded").length,
  today_run_count: 6,
  daily_run_quota: 15,
};

export type SetActiveProps = {
  setActive: SetActive;
};

export function repositoryLabel(repository: RepositoryRead) {
  return `${repository.github_owner}/${repository.github_repo}`;
}

export function formatDashboardUsage(dashboard: DashboardRead) {
  return `Daily agent run usage (${dashboard.today_run_count}/${dashboard.daily_run_quota})`;
}

export function findRepository(repository_id: string, repositories = repositoryRows) {
  return repositories.find((repository) => repository.id === repository_id);
}

export function useDashboardRead() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.dashboard],
    queryFn: patchApi.getDashboard,
    initialData: dashboardRead,
    retry: false,
  });
}

export function useRepositories() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.repositories],
    queryFn: patchApi.listRepositories,
    initialData: repositoryRows,
    retry: false,
  });
}

export function useTasks(limit = 50) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.tasks, limit],
    queryFn: () => patchApi.listTasks(limit),
    initialData: taskRows,
    retry: false,
  });
}

export function useAgentRun(id = agentRunRows[0].id) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.agentRun(id)],
    queryFn: () => patchApi.getAgentRun(id),
    initialData: agentRunRows.find((run) => run.id === id) ?? agentRunRows[0],
    retry: false,
  });
}

export function useAgentRunEvents(id = agentRunRows[0].id, limit = 50) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.agentRunEvents(id, limit)],
    queryFn: () => patchApi.getAgentRunEvents(id, limit),
    initialData: agentRunEventRows.filter((event) => event.agent_run_id === id),
    retry: false,
  });
}

export function useAgentRunDiff(id = agentRunRows[0].id) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.agentRunDiff(id)],
    queryFn: () => patchApi.getAgentRunDiff(id),
    initialData: diffFileRows,
    retry: false,
  });
}

export const statusSteps = ["queued", "running", "succeeded", "failed", "cancelled"] as const;

export const screenMeta: Record<ScreenId, { title: string; subtitle: string }> = {
  home: {
    title: "P.A.T.C.H. Home",
    subtitle: "Submit a coding task and let the autonomous agent open the pull request.",
  },
  dashboard: {
    title: "Operations",
    subtitle: "Live workspace for repositories, tasks, and agent run output.",
  },
  repo: {
    title: "Repository Setup",
    subtitle: "Connect GitHub repositories with the Stream 2 repository contract.",
  },
  task: {
    title: "New Coding Task",
    subtitle: "Send TaskCreate to POST /tasks with repository, branch, and instruction.",
  },
  run: {
    title: "Agent Run",
    subtitle: "Live events from /agent_runs/{id}/events and /ws/agent_runs/{id}.",
  },
  diff: {
    title: "Diff Review",
    subtitle: "Inspect /agent_runs/{id}/diff and submit follow-up feedback.",
  },
  pr: {
    title: "PR Result",
    subtitle: "Pull request data from /agent_runs/{id}/pull_request.",
  },
};
