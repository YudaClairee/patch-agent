import { useQuery } from "@tanstack/react-query";
import { ApiClientError, apiEndpoints, patchApi, type RepositoryRead } from "./api";

export function repositoryLabel(repository: RepositoryRead) {
  return `${repository.github_owner}/${repository.github_repo}`;
}

export function useRepositories() {
  return useQuery({
    queryKey: ["patch", apiEndpoints.repositories],
    queryFn: patchApi.listRepositories,
    retry: false,
  });
}

export function useGithubRepositories(enabled: boolean) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.githubRepositories],
    queryFn: patchApi.listGithubRepositories,
    enabled,
    retry: (failureCount, err) => {
      if (err instanceof ApiClientError && (err.status === 401 || err.status === 404)) return false;
      return failureCount < 2;
    },
  });
}

export function useAgentRuns(limit = 50, repositoryId?: string) {
  return useQuery({
    queryKey: ["patch", apiEndpoints.agentRuns, limit, repositoryId ?? null],
    queryFn: () => patchApi.listAgentRuns(limit, repositoryId),
    retry: false,
    refetchInterval: 5000,
  });
}

const TERMINAL_RUN_STATUSES = new Set(["succeeded", "failed", "cancelled"]);

export function useAgentRun(id: string | undefined) {
  return useQuery({
    queryKey: ["patch", id ? apiEndpoints.agentRun(id) : "agent-run:missing"],
    queryFn: () => patchApi.getAgentRun(id ?? ""),
    enabled: Boolean(id),
    retry: false,
    // Poll while the run hasn't reached a terminal state. Cheap source of
    // truth that doesn't depend on the WS catching every status_change frame.
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status || TERMINAL_RUN_STATUSES.has(status)) return false;
      return 2000;
    },
  });
}

export function useAgentRunEvents(id: string | undefined, limit = 100) {
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
