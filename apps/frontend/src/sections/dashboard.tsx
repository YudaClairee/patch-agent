import { Badge, Button, Card, SectionHeading } from "@patch/ui";
import { Activity, FileCode2, FolderGit, GitPullRequest, type LucideProps, Plus } from "lucide-react";
import React, { type ReactElement } from "react";
import { recentRuns, repoRows, type SetActiveProps, type WorkspaceSummary } from "../wireframe-data";

export function Dashboard({ setActive, workspaceSummary }: SetActiveProps & { workspaceSummary: WorkspaceSummary }) {
  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <Metric icon={<FolderGit />} label="Repositories" value={String(workspaceSummary.repositoryCount)} />
        <Metric icon={<Activity />} label="Active Runs" value={String(workspaceSummary.activeRunCount)} />
        <Metric icon={<FileCode2 />} label="Succeeded" value={String(workspaceSummary.succeededCount)} />
        <Metric icon={<GitPullRequest />} label="PR Created" value={String(workspaceSummary.pullRequestCount)} />
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="p-5">
          <SectionHeading
            title="Repository List"
            action={
              <Button variant="chip" onClick={() => setActive("repo")}>
                <Plus size={15} />
                Add Repo
              </Button>
            }
          />
          <div className="mt-4 divide-y divide-[var(--patch-border)]">
            {repoRows.map((repo) => (
              <button
                key={repo.name}
                type="button"
                onClick={() => setActive("repo")}
                className="flex w-full items-center justify-between gap-4 py-4 text-left"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[16px] border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)]">
                    <FolderGit size={18} />
                  </div>
                  <div className="min-w-0">
                    <div className="truncate text-base font-semibold tracking-[-0.006em] text-[var(--patch-ink)]">
                      {repo.name}
                    </div>
                    <div className="text-sm text-[var(--patch-muted)]">
                      Branch: {repo.branch} / {repo.lang}
                    </div>
                  </div>
                </div>
                <Badge tone={repo.status === "Indexed" ? "inverse" : "default"}>{repo.status}</Badge>
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <SectionHeading
            title="Recent Runs"
            action={
              <Button variant="chip" onClick={() => setActive("run")}>
                View all
              </Button>
            }
          />
          <div className="mt-4 space-y-3">
            {recentRuns.map((run) => (
              <button
                key={run.task}
                type="button"
                onClick={() => setActive(run.status === "succeeded" ? "pr" : "run")}
                className="flex w-full items-center justify-between gap-4 rounded-[22px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-left transition hover:bg-[var(--patch-surface)]"
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">
                    {run.task}
                  </div>
                  <div className="mt-1 text-sm text-[var(--patch-muted)]">{run.repo}</div>
                </div>
                <Badge tone={run.status === "review_required" ? "inverse" : "default"}>{run.status}</Badge>
              </button>
            ))}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <SectionHeading title="Current Route" action={<Badge tone="inverse">verifying</Badge>} />
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <RouteStep label="Repo indexed" value="fastapi-auth-app" active />
          <RouteStep label="Agent verifying" value="pytest + ruff" active />
          <RouteStep label="Review gate" value="diff approval required" />
        </div>
      </Card>
    </div>
  );
}

type MetricProps = {
  icon: ReactElement<LucideProps>;
  label: string;
  value: string;
};

function Metric({ icon, label, value }: MetricProps) {
  return (
    <Card className="p-5">
      <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-[16px] border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)]">
        {React.cloneElement(icon, { size: 18 })}
      </div>
      <div className="text-[32px] font-bold leading-tight tracking-[-0.6px] text-[var(--patch-ink)]">{value}</div>
      <div className="mt-1 text-sm font-medium text-[var(--patch-muted)]">{label}</div>
    </Card>
  );
}

type RouteStepProps = {
  label: string;
  value: string;
  active?: boolean;
};

function RouteStep({ label, value, active = false }: RouteStepProps) {
  return (
    <div className="rounded-[22px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4">
      <div className="flex items-center gap-2">
        <span
          className={`h-2.5 w-2.5 rounded-full ${active ? "bg-[var(--patch-ink)]" : "bg-[var(--patch-border-strong)]"}`}
        />
        <span className="text-sm font-semibold tracking-[-0.003em]">{label}</span>
      </div>
      <div className="mt-2 text-sm text-[var(--patch-muted)]">{value}</div>
    </div>
  );
}
