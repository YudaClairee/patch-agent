import { Badge, Button, Card, cn, patchClasses, SectionHeading, StatusLine, Textarea } from "@patch/ui";
import { useNavigate } from "@tanstack/react-router";
import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileCode2,
  FolderGit,
  GitBranch,
  GitPullRequest,
  MessageSquare,
  Play,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import type { ReactNode } from "react";
import type { DashboardRead } from "../lib/api";
import {
  formatDashboardUsage,
  repositoryLabel,
  type SetActiveProps,
  useAgentRuns,
  useRepositories,
  useTasks,
} from "../wireframe-data";

export function HomePage({ setActive, dashboardRead }: SetActiveProps & { dashboardRead: DashboardRead }) {
  const navigate = useNavigate();
  const { data: repositories = [] } = useRepositories();
  const { data: tasks = [] } = useTasks();
  const { data: runs = [] } = useAgentRuns();
  const primaryRepository = repositories[0];
  const primaryTask = tasks[0];
  const primaryRun = runs[0];
  const primaryRepositoryLabel = primaryRepository ? repositoryLabel(primaryRepository) : "Repository";
  const taskById = new Map(tasks.map((task) => [task.id, task]));

  return (
    <div className={cn("flex h-screen overflow-hidden", patchClasses.appSurface)}>
      <aside className="hidden w-[304px] shrink-0 flex-col border-r border-[var(--patch-border)] bg-[var(--patch-bg)] p-5 lg:flex">
        <div className="mb-7 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setActive("home")}
            className="flex min-w-0 flex-1 items-center justify-center text-left"
          >
            <img src="/patch.svg" alt="P.A.T.C.H." className="h-10 w-auto max-w-[190px] object-contain" />
          </button>
          {/* <button className="flex h-9 w-9 items-center justify-center rounded-[10px] border border-[var(--patch-border)] bg-[var(--patch-surface)] text-[var(--patch-muted)]">
            <ChevronRight size={16} />
          </button> */}
        </div>

        <button
          type="button"
          className="flex h-11 items-center gap-2 rounded-[10px] border border-[var(--patch-border)] bg-[var(--patch-surface)] px-3 text-left text-sm text-[var(--patch-muted)]"
        >
          <span className="min-w-0 flex-1 truncate">Search repo, session, trace</span>
          <Search size={17} />
        </button>

        <HomeSidebarSection title="Repositories">
          {repositories.map((repository) => (
            <button
              key={repository.id}
              type="button"
              onClick={() => setActive("repo")}
              className="flex w-full items-center gap-3 rounded-[10px] px-2 py-2 text-left text-sm text-[var(--patch-ink)] hover:bg-[var(--patch-surface)]"
            >
              <FolderGit size={16} className="text-[var(--patch-muted)]" />
              <span className="min-w-0 flex-1 truncate">{repository.github_repo}</span>
              <span className="text-xs text-[var(--patch-muted)]">{repository.default_branch}</span>
            </button>
          ))}
        </HomeSidebarSection>

        <HomeSidebarSection title="Recent runs">
          {runs.slice(0, 4).map((run) => {
            const task = taskById.get(run.task_id);
            const title = task?.title ?? run.pull_request?.title ?? run.id;

            return (
              <button
                key={run.id}
                type="button"
                onClick={() => void navigate({ to: "/run/$id", params: { id: run.id } })}
                className="flex w-full items-start gap-3 rounded-[10px] px-2 py-2 text-left hover:bg-[var(--patch-surface)]"
              >
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--patch-muted)]" />
                <span className="min-w-0">
                  <span className="block truncate text-sm text-[var(--patch-ink)]">{title}</span>
                  <span className="block truncate text-xs text-[var(--patch-muted)]">{run.status}</span>
                </span>
              </button>
            );
          })}
          {runs.length === 0 && (
            <p className="px-2 py-2 text-sm leading-5 text-[var(--patch-muted)]">No agent runs yet.</p>
          )}
        </HomeSidebarSection>

        <div className="mt-auto">
          <div className="rounded-[24px] bg-[var(--patch-surface)] p-4">
            <div className="flex items-center justify-between text-sm font-semibold text-[var(--patch-ink)]">
              <span>Review control</span>
              <ShieldCheck size={16} />
            </div>
            <p className="mt-2 text-xs leading-5 text-[var(--patch-muted)]">
              PR diff appears after the agent publishes a pull request. Secret/token values are never displayed again.
            </p>
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-[var(--patch-border)]">
            <div className="h-full w-[42%] rounded-full bg-[var(--patch-ink)]" />
          </div>
          <div className="mt-3 text-sm text-[var(--patch-muted)]">{formatDashboardUsage(dashboardRead)}</div>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--patch-border)] bg-[var(--patch-surface)] px-5">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className="flex min-h-10 items-center gap-2 rounded-full bg-[var(--patch-bg)] px-4 font-mono text-sm font-semibold text-[var(--patch-ink)]"
            >
              {primaryRepository?.github_repo ?? "repository"}
              <ChevronRight size={16} className="rotate-90 text-[var(--patch-muted)]" />
            </button>
            <button
              type="button"
              className="hidden min-h-10 items-center gap-2 rounded-full bg-[var(--patch-bg)] px-4 text-sm font-medium text-[var(--patch-ink)] md:flex"
            >
              <GitBranch size={16} />
              {primaryRepository?.default_branch ?? "main"}
            </button>
          </div>
          <div className="flex items-center gap-2">
            {/* <button
              type="button"
              className="hidden h-10 items-center gap-2 rounded-full bg-[var(--patch-chip)] px-4 text-sm font-medium text-[var(--patch-ink)] backdrop-blur-[20px] md:flex"
            >
              <Moon size={16} />
              Focus
            </button> */}
            <button
              type="button"
              onClick={() => setActive("repo")}
              className="hidden h-10 items-center gap-2 rounded-full bg-[var(--patch-chip)] px-4 text-sm font-medium text-[var(--patch-ink)] backdrop-blur-[20px] md:flex"
            >
              <Settings size={16} />
              Configure repo
            </button>
            <button
              type="button"
              onClick={() => setActive("task")}
              className="flex h-10 items-center gap-2 rounded-full bg-[var(--patch-accent)] px-4 text-sm font-medium text-white"
            >
              <Plus size={16} />
              New task
            </button>
          </div>
        </header>

        <main className="grid min-h-0 flex-1 grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px]">
          <section className="relative flex min-h-0 flex-col overflow-hidden">
            <div className="min-h-0 flex-1 overflow-auto px-5 pb-44 pt-6">
              <div className="mx-auto flex w-full max-w-[880px] flex-col gap-5">
                <ChatBubble speaker="user">
                  {primaryTask?.instruction ?? "Describe a coding task for this repository."}
                </ChatBubble>
                <ChatBubble speaker="agent">
                  Saya akan menunggu task baru, membuka run live dari WebSocket, lalu menampilkan PR dan diff saat
                  backend mengirim status terminal.
                </ChatBubble>

                <Card className="p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--patch-ink)]">
                        <Activity size={16} />
                        Workspace activity
                      </div>
                      <p className="mt-2 text-sm leading-5 text-[var(--patch-muted)]">
                        {dashboardRead.active_run_count} active runs / {dashboardRead.succeeded_run_count} succeeded
                        runs / {dashboardRead.today_run_count} today
                      </p>
                    </div>
                    <Badge tone="inverse">{dashboardRead.active_run_count > 0 ? "active" : "ready"}</Badge>
                  </div>
                  <div className="mt-5 grid gap-3 md:grid-cols-4">
                    <HomeRunStep title="Repositories" value={String(dashboardRead.repository_count)} active />
                    <HomeRunStep title="Active runs" value={String(dashboardRead.active_run_count)} active />
                    <HomeRunStep title="Succeeded" value={String(dashboardRead.succeeded_run_count)} active />
                    <HomeRunStep title="Review" value="run-scoped" />
                  </div>
                </Card>

                <Card className="p-5">
                  <SectionHeading title="Task Outcomes" action={<Badge>success criteria</Badge>} />
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <OutcomeCheck
                      label="Repository selected"
                      value={primaryRepositoryLabel}
                      done={Boolean(primaryRepository)}
                    />
                    <OutcomeCheck
                      label="Branch selected"
                      value={primaryTask?.target_branch ?? primaryRepository?.default_branch ?? "choose branch"}
                      done={Boolean(primaryTask || primaryRepository)}
                    />
                    <OutcomeCheck label="Human review remains" value="diff route after PR" />
                  </div>
                </Card>

                <div className="grid gap-5 lg:grid-cols-2">
                  <Card className="p-5">
                    <SectionHeading title="Execution Plan" />
                    <ol className="mt-4 space-y-3 text-sm leading-5 text-[var(--patch-text)]">
                      <li>1. Connect a GitHub PAT for authenticated repository and diff access.</li>
                      <li>2. Connect a repository from Stream 2.</li>
                      <li>3. Submit TaskCreate to queue an agent run.</li>
                      <li>4. Watch live WebSocket events on /run/:id.</li>
                      <li>5. Review GitHub diff and request follow-up work if needed.</li>
                    </ol>
                  </Card>
                  <Card className="p-5">
                    <SectionHeading title="Live Contracts" />
                    <div className="mt-4 space-y-3">
                      <ToolCall label="GET /repositories" value={`${repositories.length} connected`} />
                      <ToolCall label="GET /tasks" value={`${tasks.length} recent tasks`} />
                      <ToolCall label="GET /agent_runs" value={`${runs.length} recent runs`} />
                      <ToolCall label="GET /me/dashboard" value={formatDashboardUsage(dashboardRead)} />
                      <ToolCall label="WS /agent_runs/:id" value="opens after task submit" />
                    </div>
                  </Card>
                </div>
              </div>
            </div>

            <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-48 bg-gradient-to-t from-[var(--patch-bg)] via-[var(--patch-bg)] to-transparent" />

            <div className="absolute bottom-6 left-5 right-5 z-20 mx-auto flex max-w-[880px] flex-col gap-3 rounded-[28px] border border-[var(--patch-border)] bg-[var(--patch-surface)] p-4 shadow-[var(--patch-shadow-floating)]">
              <Textarea
                aria-label="Coding task instruction"
                className="min-h-24 resize-none bg-[var(--patch-surface)] px-1 py-2 text-base leading-6 text-[var(--patch-ink)] outline-none placeholder:text-[var(--patch-muted)]"
                placeholder="Ask P.A.T.C.H. to work on this repository"
              />
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  aria-label="Attach context"
                  className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--patch-border)] bg-[var(--patch-bg)] text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)]"
                >
                  <Plus size={18} />
                </button>
                <button
                  type="button"
                  className="flex h-10 items-center gap-2 rounded-full border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 font-mono text-sm font-semibold text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)]"
                >
                  <GitBranch size={15} />
                  {primaryTask?.target_branch ?? primaryRepository?.default_branch ?? "main"}
                </button>
                <button
                  type="button"
                  className="hidden h-10 items-center gap-2 rounded-full border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 text-sm text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)] md:flex"
                >
                  <Terminal size={15} />
                  live events
                </button>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActive("task")}
                    className="flex h-10 items-center gap-2 rounded-full bg-[var(--patch-accent)] px-4 text-sm font-medium text-white"
                  >
                    <Play size={16} />
                    Create run
                  </button>
                  <button
                    type="button"
                    aria-label="Open review"
                    onClick={() => {
                      if (primaryRun) {
                        void navigate({ to: "/run/$id/diff", params: { id: primaryRun.id } });
                        return;
                      }

                      setActive("diff");
                    }}
                    className="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--patch-ink)] text-white"
                  >
                    <ArrowRight size={18} />
                  </button>
                </div>
              </div>
            </div>
          </section>

          <aside className="hidden min-h-0 overflow-auto border-l border-[var(--patch-border)] bg-[var(--patch-bg)] p-5 xl:block">
            <div className="space-y-5">
              <Card className="p-5">
                <SectionHeading title="Repository Context" action={<Badge>indexed</Badge>} />
                <div className="mt-4 space-y-3">
                  <StatusLine label="Repo" value={primaryRepositoryLabel} />
                  <StatusLine
                    label="Branch"
                    value={primaryTask?.target_branch ?? primaryRepository?.default_branch ?? "main"}
                  />
                  <StatusLine label="Run endpoint" value="/run/:id after task submission" />
                  <StatusLine label="Repository ID" value={primaryRepository?.id ?? "not selected"} />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Developer Journey" />
                <div className="mt-4 space-y-3">
                  <JourneyItem label="Describe task" value="instruction captured" active />
                  <JourneyItem label="Agent works" value="plan, tools, command logs" active />
                  <JourneyItem label="Review diff" value="current decision point" />
                  <JourneyItem label="Open PR" value="after agent succeeds" />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Verification" />
                <div className="mt-4 space-y-3">
                  <StatusLine label="Run checks" value="rendered from live tool timeline" />
                  <StatusLine label="Terminal state" value="succeeded, failed, or cancelled" />
                  <StatusLine label="Feedback" value="queues a child run on the same PR branch" />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Diff Review" action={<Badge tone="inverse">ready</Badge>} />
                <p className="mt-3 text-sm leading-5 text-[var(--patch-muted)]">
                  Next best action after a successful run: inspect changed files, request follow-up changes, or open the
                  pull request on GitHub.
                </p>
                <p className="mt-4 rounded-[18px] border border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 text-sm leading-6 text-[var(--patch-muted)]">
                  Diff files are loaded from /agent_runs/:id/diff on a run-scoped review route.
                </p>
                <div className="mt-5 grid gap-3">
                  <Button
                    onClick={() => {
                      if (primaryRun) {
                        void navigate({ to: "/run/$id/diff", params: { id: primaryRun.id } });
                        return;
                      }

                      setActive("diff");
                    }}
                  >
                    <FileCode2 size={15} />
                    Open Diff
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => {
                      if (primaryRun) {
                        void navigate({ to: "/run/$id/pr", params: { id: primaryRun.id } });
                        return;
                      }

                      setActive("pr");
                    }}
                  >
                    <GitPullRequest size={15} />
                    Open PR
                  </Button>
                </div>
              </Card>

              <Card surface="dark" className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  <ShieldCheck size={16} />
                  Guardrails
                </div>
                <p className="mt-3 text-sm leading-6 text-[var(--patch-on-dark-muted)]">
                  Blocked commands, secret protection, isolated workspace, and follow-up review are enforced for the MVP
                  flow.
                </p>
              </Card>
            </div>
          </aside>
        </main>
      </section>
    </div>
  );
}

type ChatBubbleProps = {
  speaker: "user" | "agent";
  children: ReactNode;
};

function ChatBubble({ speaker, children }: ChatBubbleProps) {
  const isUser = speaker === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[760px] rounded-[28px] border border-[var(--patch-border)] p-5 ${isUser ? "bg-[var(--patch-ink)] text-white" : "bg-[var(--patch-surface)] text-[var(--patch-ink)]"}`}
      >
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.08em] opacity-70">
          {isUser ? <MessageSquare size={14} /> : <Bot size={14} />}
          {isUser ? "Developer" : "P.A.T.C.H."}
        </div>
        <p className="text-base leading-7 tracking-[-0.006em]">{children}</p>
      </div>
    </div>
  );
}

type HomeRunStepProps = {
  title: string;
  value: string;
  active?: boolean;
};

function HomeRunStep({ title, value, active = false }: HomeRunStepProps) {
  return (
    <div className="rounded-[22px] bg-[var(--patch-bg)] p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--patch-ink)]">
        <span className={`h-2.5 w-2.5 rounded-full ${active ? "bg-[var(--patch-ink)]" : "bg-[var(--patch-muted)]"}`} />
        {title}
      </div>
      <div className="mt-2 text-sm text-[var(--patch-muted)]">{value}</div>
    </div>
  );
}

type OutcomeCheckProps = {
  label: string;
  value: string;
  done?: boolean;
};

function OutcomeCheck({ label, value, done = false }: OutcomeCheckProps) {
  return (
    <div className="rounded-[22px] bg-[var(--patch-bg)] p-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--patch-ink)]">
        {done ? <CheckCircle2 size={16} /> : <Clock3 size={16} />}
        {label}
      </div>
      <div className="mt-2 text-sm text-[var(--patch-muted)]">{value}</div>
    </div>
  );
}

type ToolCallProps = {
  label: string;
  value: string;
};

function ToolCall({ label, value }: ToolCallProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-[18px] bg-[var(--patch-bg)] px-3 py-2">
      <span className="font-mono text-xs font-semibold text-[var(--patch-ink)]">{label}</span>
      <span className="min-w-0 truncate text-sm text-[var(--patch-muted)]">{value}</span>
    </div>
  );
}

type JourneyItemProps = {
  label: string;
  value: string;
  active?: boolean;
};

function JourneyItem({ label, value, active = false }: JourneyItemProps) {
  return (
    <div className="flex gap-3 rounded-[18px] bg-[var(--patch-bg)] p-3">
      <span
        className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${active ? "bg-[var(--patch-ink)]" : "bg-[var(--patch-muted)]"}`}
      />
      <span className="min-w-0">
        <span className="block text-sm font-semibold text-[var(--patch-ink)]">{label}</span>
        <span className="block truncate text-sm text-[var(--patch-muted)]">{value}</span>
      </span>
    </div>
  );
}

type HomeSidebarSectionProps = {
  title: string;
  children: ReactNode;
};

function HomeSidebarSection({ title, children }: HomeSidebarSectionProps) {
  return (
    <div className="mt-8">
      <div className="mb-3 flex items-center justify-between text-sm font-medium text-[var(--patch-muted)]">
        <span>{title}</span>
        <ChevronRight size={16} className="rotate-[-90deg]" />
      </div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}
