import { useQuery } from "@tanstack/react-query";
import { apiEndpoints, type DashboardRead, patchApi, type RepositoryRead } from "./lib/api";

export const screens = [
  { id: "home", label: "Home" },
  { id: "dashboard", label: "Dashboard" },
  { id: "repo", label: "Repository" },
  { id: "task", label: "New Task" },
  { id: "run", label: "Agent Run" },
  { id: "diff", label: "Diff Review" },
  { id: "pr", label: "PR Result" },
  { id: "settings", label: "GitHub PAT" },
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
  settings: "/settings/github",
} as const satisfies Record<ScreenId, string>;

export const emptyDashboardRead: DashboardRead = {
  repository_count: 0,
  active_run_count: 0,
  succeeded_run_count: 0,
  today_run_count: 0,
  daily_run_quota: 0,
};

export type SetActiveProps = {
  setActive: SetActive;
};

export function repositoryLabel(repository: RepositoryRead) {
  return `${repository.github_owner}/${repository.github_repo}`;
}

export function formatDashboardUsage(dashboard: DashboardRead) {
  if (dashboard.daily_run_quota <= 0) {
    return "Daily agent run usage unavailable";
  }

  return `Daily agent run usage (${dashboard.today_run_count}/${dashboard.daily_run_quota})`;
}

export function findRepository(repository_id: string, repositories: RepositoryRead[]) {
  return repositories.find((repository) => repository.id === repository_id);
}

export function useDashboardRead() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.dashboard],
    queryFn: patchApi.getDashboard,
    retry: false,
  });
}

export function useRepositories() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.repositories],
    queryFn: patchApi.listRepositories,
    retry: false,
  });
}

export function useTasks(limit = 50) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.tasks, limit],
    queryFn: () => patchApi.listTasks(limit),
    retry: false,
  });
}

export function useAgentRuns(limit = 50) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.agentRuns, limit],
    queryFn: () => patchApi.listAgentRuns(limit),
    retry: false,
  });
}

export function useGitHubCredentials() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.githubCredentials],
    queryFn: patchApi.listGitHubCredentials,
    retry: false,
  });
}

export function useAgentRun(id: string | undefined) {
  return useQuery({
    queryKey: ["patch", id ? apiEndpoints.agentRun(id) : "agent-run:missing"],
    queryFn: () => patchApi.getAgentRun(id ?? ""),
    enabled: Boolean(id),
    retry: false,
  });
}

export function useAgentRunEvents(id: string | undefined, limit = 50) {
  return useQuery({
    queryKey: ["patch", id ? apiEndpoints.agentRunEvents(id, limit) : "agent-run-events:missing", limit],
    queryFn: () => patchApi.getAgentRunEvents(id ?? "", limit),
    enabled: Boolean(id),
    retry: false,
  });
}

export function useAgentRunPullRequest(id: string | undefined) {
  return useQuery({
    queryKey: ["patch", id ? apiEndpoints.agentRunPullRequest(id) : "agent-run-pull-request:missing"],
    queryFn: () => patchApi.getAgentRunPullRequest(id ?? ""),
    enabled: Boolean(id),
    retry: false,
  });
}

export function useAgentRunDiff(id: string | undefined) {
  return useQuery({
    queryKey: ["patch", id ? apiEndpoints.agentRunDiff(id) : "agent-run-diff:missing"],
    queryFn: () => patchApi.getAgentRunDiff(id ?? ""),
    enabled: Boolean(id),
    retry: false,
  });
}

export const statusSteps = ["queued", "running", "succeeded", "failed", "cancelled"] as const;

export const screenMeta: Record<ScreenId, { title: string; subtitle: string }> = {
  home: {
    title: "P.A.T.C.H. Home",
    subtitle: "Submit a coding task and watch the autonomous agent open a pull request.",
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
    subtitle: "Live agent work from /ws/agent_runs/{id}, backed by event history.",
  },
  diff: {
    title: "Diff Review",
    subtitle: "Inspect /agent_runs/{id}/diff and submit follow-up feedback.",
  },
  pr: {
    title: "PR Result",
    subtitle: "Pull request data from /agent_runs/{id}/pull_request.",
  },
  settings: {
    title: "GitHub PAT",
    subtitle: "Connect the encrypted GitHub credential used for repository access and diff fetches.",
  },
};
