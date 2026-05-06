import { useQuery } from "@tanstack/react-query";

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

export const repoRows = [
  { name: "fastapi-auth-app", branch: "main", status: "Ready", lang: "Python" },
  { name: "patch-web", branch: "develop", status: "Indexed", lang: "React" },
  { name: "mini-ecommerce-api", branch: "main", status: "Ready", lang: "FastAPI" },
];

export const recentRuns = [
  { task: "Add unit tests for login endpoint", repo: "fastapi-auth-app", status: "review_required" },
  { task: "Fix navbar responsive bug", repo: "patch-web", status: "verifying" },
  { task: "Refactor product service", repo: "mini-ecommerce-api", status: "pr_created" },
];

export type SetActiveProps = {
  setActive: SetActive;
};

export type WorkspaceSummary = {
  repositoryCount: number;
  activeRunCount: number;
  reviewRequiredCount: number;
  pullRequestCount: number;
  verificationStatus: string;
  usageLabel: string;
};

const workspaceSummary: WorkspaceSummary = {
  repositoryCount: repoRows.length,
  activeRunCount: recentRuns.filter((run) => run.status !== "pr_created").length,
  reviewRequiredCount: recentRuns.filter((run) => run.status === "review_required").length,
  pullRequestCount: 7,
  verificationStatus: "pytest passed - ruff passed - review required",
  usageLabel: "Daily agent run usage (6/15)",
};

export function useWorkspaceSummary() {
  return useQuery({
    queryKey: ["patch", "workspace-summary"],
    queryFn: async () => workspaceSummary,
    initialData: workspaceSummary,
    staleTime: Number.POSITIVE_INFINITY,
  });
}

export const statusSteps = [
  "queued",
  "preparing_workspace",
  "cloning_repo",
  "indexing",
  "planning",
  "executing",
  "verifying",
  "review_required",
] as const;

export const screenMeta: Record<ScreenId, { title: string; subtitle: string }> = {
  home: {
    title: "P.A.T.C.H. Home",
    subtitle: "Chat with the coding agent, inspect repository context, and keep review control before PR handoff.",
  },
  dashboard: {
    title: "Operations",
    subtitle: "Live workspace for repositories, runs, diff gates, and pull request output.",
  },
  repo: {
    title: "Repository Setup",
    subtitle: "Source, branch, credential reference, and verification commands.",
  },
  task: {
    title: "New Coding Task",
    subtitle: "Target context and instruction editor for the next agent run.",
  },
  run: {
    title: "Agent Run",
    subtitle: "Queue state, execution plan, command logs, and changed files.",
  },
  diff: {
    title: "Diff Review",
    subtitle: "Inspect generated changes before creating the pull request.",
  },
  pr: {
    title: "PR Result",
    subtitle: "Final branch, verification badges, and GitHub pull request link.",
  },
};
