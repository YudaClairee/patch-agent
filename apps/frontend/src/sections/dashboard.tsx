import { Badge, Button, Card, SectionHeading } from "@patch/ui";
import { Activity, CalendarDays, FileCode2, FolderGit, type LucideProps, Plus } from "lucide-react";
import React, { type ReactElement } from "react";
import type { DashboardRead } from "../api-contract";
import { findRepository, repositoryLabel, type SetActiveProps, useRepositories, useTasks } from "../wireframe-data";

export function Dashboard({ setActive, dashboardRead }: SetActiveProps & { dashboardRead: DashboardRead }) {
  const { data: repositories } = useRepositories();
  const { data: tasks } = useTasks();
  const primaryRepository = repositories[0];
  const primaryTask = tasks[0];

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <Metric icon={<FolderGit />} label="Repositories" value={String(dashboardRead.repository_count)} />
        <Metric icon={<Activity />} label="Active Runs" value={String(dashboardRead.active_run_count)} />
        <Metric icon={<FileCode2 />} label="Succeeded" value={String(dashboardRead.succeeded_run_count)} />
        <Metric icon={<CalendarDays />} label="Runs Today" value={String(dashboardRead.today_run_count)} />
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
            {repositories.map((repository) => (
              <button
                key={repository.id}
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
                      {repositoryLabel(repository)}
                    </div>
                    <div className="text-sm text-[var(--patch-muted)]">
                      Branch: {repository.default_branch} / {repository.language ?? "Unknown"}
                    </div>
                  </div>
                </div>
                <Badge tone="inverse">connected</Badge>
              </button>
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <SectionHeading
            title="Recent Tasks"
            action={
              <Button variant="chip" onClick={() => setActive("run")}>
                View all
              </Button>
            }
          />
          <div className="mt-4 space-y-3">
            {tasks.map((task) => {
              const repository = findRepository(task.repository_id, repositories);

              return (
                <button
                  key={task.id}
                  type="button"
                  onClick={() => setActive("run")}
                  className="flex w-full items-center justify-between gap-4 rounded-[22px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-left transition hover:bg-[var(--patch-surface)]"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-semibold tracking-[-0.003em] text-[var(--patch-ink)]">
                      {task.title}
                    </div>
                    <div className="mt-1 text-sm text-[var(--patch-muted)]">
                      {repository ? repositoryLabel(repository) : task.repository_id}
                    </div>
                  </div>
                  <Badge>{task.target_branch}</Badge>
                </button>
              );
            })}
          </div>
        </Card>
      </div>

      <Card className="p-5">
        <SectionHeading title="Current Route" action={<Badge tone="inverse">verifying</Badge>} />
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <RouteStep
            label="Repository"
            value={primaryRepository ? repositoryLabel(primaryRepository) : "not selected"}
            active
          />
          <RouteStep label="Task" value={primaryTask?.target_branch ?? "target_branch"} active />
          <RouteStep label="Review" value="/agent_runs/{id}/diff" />
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
