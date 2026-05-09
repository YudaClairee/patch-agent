import { useQuery } from "@tanstack/react-query";

export const screens = [
  { id: "home", label: "Home" },
  { id: "dashboard", label: "Dashboard" },
  { id: "repo", label: "Repository" },
  { id: "task", label: "New Task" },
  { id: "run", label: "Agent Run" },
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
  pr: "/pr",
} as const satisfies Record<ScreenId, string>;

export const repoRows = [
  { name: "fastapi-auth-app", branch: "main", status: "Ready", lang: "Python" },
  { name: "patch-web", branch: "develop", status: "Indexed", lang: "React" },
  { name: "mini-ecommerce-api", branch: "main", status: "Ready", lang: "FastAPI" },
];

export const recentRuns = [
  { task: "Add unit tests for login endpoint", repo: "fastapi-auth-app", status: "running" },
  { task: "Fix navbar responsive bug", repo: "patch-web", status: "running" },
  { task: "Refactor product service", repo: "mini-ecommerce-api", status: "succeeded" },
];

export type SetActiveProps = {
  setActive: SetActive;
};

export type WorkspaceSummary = {
  repositoryCount: number;
  activeRunCount: number;
  succeededCount: number;
  pullRequestCount: number;
  verificationStatus: string;
  usageLabel: string;
};

const workspaceSummary: WorkspaceSummary = {
  repositoryCount: repoRows.length,
  activeRunCount: recentRuns.filter((run) => run.status === "running").length,
  succeededCount: recentRuns.filter((run) => run.status === "succeeded").length,
  pullRequestCount: 7,
  verificationStatus: "agent autonomous - tests gated - PR auto-opened",
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

export const statusSteps = ["queued", "running", "succeeded", "failed"] as const;

export const screenMeta: Record<ScreenId, { title: string; subtitle: string }> = {
  home: {
    title: "P.A.T.C.H. Home",
    subtitle: "Submit a coding task and let the autonomous agent open the pull request.",
  },
  dashboard: {
    title: "Operations",
    subtitle: "Live workspace for repositories, runs, and pull request output.",
  },
  repo: {
    title: "Repository Setup",
    subtitle: "Source, branch, credential reference, and verification commands.",
  },
  task: {
    title: "New Coding Task",
    subtitle: "Target context and instruction for the next agent run.",
  },
  run: {
    title: "Agent Run",
    subtitle: "Live tool-call timeline and final pull request handoff.",
  },
  pr: {
    title: "PR Result",
    subtitle: "Final branch and GitHub pull request link.",
  },
};
