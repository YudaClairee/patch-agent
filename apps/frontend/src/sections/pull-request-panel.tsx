import { Badge, Button, Card, SectionHeading, StatusLine } from "@patch/ui";
import { ExternalLink, GitPullRequest } from "lucide-react";
import { type AgentRunStatus, apiEndpoints, type PullRequestRead, type PullRequestSummaryRead } from "../lib/api";

type PullRequestPanelProps = {
  runId: string;
  pullRequest: PullRequestRead | PullRequestSummaryRead | null;
  branchName?: string | null;
  status?: AgentRunStatus;
  prUrl?: string | null;
  errorMessage?: string | null;
  compact?: boolean;
};

export function PullRequestPanel({
  runId,
  pullRequest,
  branchName,
  status,
  prUrl,
  errorMessage,
  compact = false,
}: PullRequestPanelProps) {
  const url = pullRequest?.url ?? prUrl ?? null;
  const title = pullRequest?.title ?? "Pull request pending";
  const state = pullRequest?.state ?? status ?? "loading";
  const headBranch = getHeadBranch(pullRequest) ?? branchName ?? "branch pending";
  const baseBranch = getBaseBranch(pullRequest);
  const prNumber = pullRequest?.github_pr_number;

  return (
    <Card className={compact ? "p-5" : "p-6"}>
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          {!compact && (
            <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-[18px] bg-[var(--patch-ink)] text-white">
              <GitPullRequest size={26} />
            </div>
          )}
          <SectionHeading
            title={compact ? "Pull Request" : title}
            action={compact ? <GitPullRequest size={18} /> : null}
          />
          {!compact && (
            <p className="mt-3 max-w-xl text-base leading-6 tracking-[-0.006em] text-[var(--patch-text)]">
              Branch <strong>{headBranch}</strong> is resolved from {apiEndpoints.agentRunPullRequest(runId)}.
            </p>
          )}
        </div>
        <Badge tone="inverse">{state}</Badge>
      </div>

      {compact && (
        <p className="mt-3 text-sm leading-6 text-[var(--patch-muted)]">
          {url
            ? "The agent published a pull request for this run."
            : "PR link appears after a successful terminal run."}
        </p>
      )}

      <div className={compact ? "mt-4" : "mt-6"}>
        {url ? (
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="flex min-h-11 items-center justify-between gap-3 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 text-sm font-semibold text-[var(--patch-ink)] transition hover:bg-[var(--patch-surface)]"
          >
            <span className="min-w-0 truncate">{title === "Pull request pending" ? url : title}</span>
            <ExternalLink size={16} className="shrink-0" />
          </a>
        ) : (
          <p className="rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-muted)]">
            Pull request is not available yet.
          </p>
        )}
      </div>

      {errorMessage && (
        <div className="mt-4 rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-ink)]">
          {errorMessage}
        </div>
      )}

      {!compact && (
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          <StatusLine label="github_pr_number" value={String(prNumber ?? "-")} />
          <StatusLine label="base_branch" value={baseBranch ?? "-"} />
          <StatusLine label="head_branch" value={headBranch} />
        </div>
      )}

      {!compact && url && (
        <Button className="mt-5 w-full" onClick={() => window.open(url, "_blank", "noopener,noreferrer")}>
          <ExternalLink size={15} />
          View on GitHub
        </Button>
      )}
    </Card>
  );
}

function getHeadBranch(pullRequest: PullRequestRead | PullRequestSummaryRead | null) {
  return pullRequest && "head_branch" in pullRequest ? pullRequest.head_branch : null;
}

function getBaseBranch(pullRequest: PullRequestRead | PullRequestSummaryRead | null) {
  return pullRequest && "base_branch" in pullRequest ? pullRequest.base_branch : null;
}
