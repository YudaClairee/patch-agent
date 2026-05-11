import { Badge, Card, SectionHeading, StatusLine } from "@patch/ui";
import { ExternalLink, GitPullRequest } from "lucide-react";
import { apiEndpoints } from "../api-contract";
import { useAgentRun } from "../wireframe-data";

export function PRResult() {
  const { data: agentRun } = useAgentRun();
  const pullRequest = agentRun.pull_request;

  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_320px]">
      <Card className="p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-[18px] bg-[var(--patch-ink)] text-white">
              <GitPullRequest size={26} />
            </div>
            <h2 className="text-[32px] font-bold leading-tight tracking-[-0.6px] text-[var(--patch-ink)]">
              PullRequestRead
            </h2>
            <p className="mt-3 max-w-xl text-base leading-6 tracking-[-0.006em] text-[var(--patch-text)]">
              Branch <strong>{pullRequest?.head_branch ?? agentRun.branch_name ?? "branch pending"}</strong> siap dibuka
              lewat endpoint {apiEndpoints.agentRunPullRequest(agentRun.id)}.
            </p>
          </div>
          <Badge tone="inverse">{pullRequest?.state ?? agentRun.status}</Badge>
        </div>

        <div className="mt-6 rounded-[22px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4">
          <div className="text-sm font-semibold text-[var(--patch-ink)]">url</div>
          <div className="mt-2 flex items-center justify-between gap-3 rounded-full border border-[var(--patch-border)] bg-[var(--patch-surface)] px-4 py-3 text-sm text-[var(--patch-ink)]">
            <span className="truncate">{pullRequest?.url ?? "Pull request belum tersedia"}</span>
            <ExternalLink size={16} />
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <SectionHeading title="Pull Request" />
        <div className="mt-5 space-y-3">
          <StatusLine label="github_pr_number" value={String(pullRequest?.github_pr_number ?? "-")} />
          <StatusLine label="base_branch" value={pullRequest?.base_branch ?? "-"} />
          <StatusLine label="head_branch" value={pullRequest?.head_branch ?? agentRun.branch_name ?? "-"} />
        </div>
      </Card>
    </div>
  );
}
