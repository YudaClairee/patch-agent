import { Badge, Button, Card, cn, FileRow, patchClasses, SectionHeading, StatusLine, Textarea } from "@patch/ui";
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
  Moon,
  Play,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Terminal,
} from "lucide-react";
import type { ReactNode } from "react";
import { recentRuns, repoRows, type SetActiveProps, type WorkspaceSummary } from "../wireframe-data";

export function HomePage({ setActive, workspaceSummary }: SetActiveProps & { workspaceSummary: WorkspaceSummary }) {
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
          {repoRows.map((repo) => (
            <button
              key={repo.name}
              type="button"
              onClick={() => setActive("repo")}
              className="flex w-full items-center gap-3 rounded-[10px] px-2 py-2 text-left text-sm text-[var(--patch-ink)] hover:bg-[var(--patch-surface)]"
            >
              <FolderGit size={16} className="text-[var(--patch-muted)]" />
              <span className="min-w-0 flex-1 truncate">{repo.name}</span>
              <span className="text-xs text-[var(--patch-muted)]">{repo.branch}</span>
            </button>
          ))}
        </HomeSidebarSection>

        <HomeSidebarSection title="Recent agent runs">
          {recentRuns.map((run) => (
            <button
              key={run.task}
              type="button"
              onClick={() => setActive(run.status === "succeeded" ? "pr" : "run")}
              className="flex w-full items-start gap-3 rounded-[10px] px-2 py-2 text-left hover:bg-[var(--patch-surface)]"
            >
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-[var(--patch-muted)]" />
              <span className="min-w-0">
                <span className="block truncate text-sm text-[var(--patch-ink)]">{run.task}</span>
                <span className="block truncate text-xs text-[var(--patch-muted)]">{run.status}</span>
              </span>
            </button>
          ))}
        </HomeSidebarSection>

        <div className="mt-auto">
          <div className="rounded-[24px] bg-[var(--patch-surface)] p-4">
            <div className="flex items-center justify-between text-sm font-semibold text-[var(--patch-ink)]">
              <span>Review control</span>
              <ShieldCheck size={16} />
            </div>
            <p className="mt-2 text-xs leading-5 text-[var(--patch-muted)]">
              PR dibuat setelah diff disetujui. Secret/token tidak ditampilkan ulang.
            </p>
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-[var(--patch-border)]">
            <div className="h-full w-[42%] rounded-full bg-[var(--patch-ink)]" />
          </div>
          <div className="mt-3 text-sm text-[var(--patch-muted)]">{workspaceSummary.usageLabel}</div>
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--patch-border)] bg-[var(--patch-surface)] px-5">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              className="flex min-h-10 items-center gap-2 rounded-full bg-[var(--patch-bg)] px-4 font-mono text-sm font-semibold text-[var(--patch-ink)]"
            >
              fastapi-auth-app
              <ChevronRight size={16} className="rotate-90 text-[var(--patch-muted)]" />
            </button>
            <button
              type="button"
              className="hidden min-h-10 items-center gap-2 rounded-full bg-[var(--patch-bg)] px-4 text-sm font-medium text-[var(--patch-ink)] md:flex"
            >
              <GitBranch size={16} />
              main
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="hidden h-10 items-center gap-2 rounded-full bg-[var(--patch-chip)] px-4 text-sm font-medium text-[var(--patch-ink)] backdrop-blur-[20px] md:flex"
            >
              <Moon size={16} />
              Focus
            </button>
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
                  Tambahkan unit test untuk endpoint login. Pastikan test dapat dijalankan dengan pytest dan jangan ubah
                  logic utama jika tidak perlu.
                </ChatBubble>
                <ChatBubble speaker="agent">
                  Saya akan membaca struktur repo, mencari endpoint auth/login, membuat execution plan, menambahkan
                  test, menjalankan pytest dan ruff, lalu menahan hasilnya di review gate sebelum PR.
                </ChatBubble>

                <Card className="p-5">
                  <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--patch-ink)]">
                        <Activity size={16} />
                        Current agent run
                      </div>
                      <p className="mt-2 text-sm leading-5 text-[var(--patch-muted)]">
                        run_123 / patch/task-102 / Langfuse trace lf_9a12
                      </p>
                    </div>
                    <Badge tone="inverse">review_required</Badge>
                  </div>
                  <div className="mt-5 grid gap-3 md:grid-cols-4">
                    <HomeRunStep title="Workspace" value="ready" active />
                    <HomeRunStep title="Indexing" value="Vector DB" active />
                    <HomeRunStep title="Verifying" value="pytest + ruff" active />
                    <HomeRunStep title="Review" value="diff gate" />
                  </div>
                </Card>

                <Card className="p-5">
                  <SectionHeading title="Task Outcomes" action={<Badge>success criteria</Badge>} />
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <OutcomeCheck label="Relevant context found" value="auth router + test fixtures" done />
                    <OutcomeCheck label="Verification passes" value="pytest and ruff complete" done />
                    <OutcomeCheck label="Human review remains" value="diff approval required" />
                  </div>
                </Card>

                <div className="grid gap-5 lg:grid-cols-2">
                  <Card className="p-5">
                    <SectionHeading title="Execution Plan" />
                    <ol className="mt-4 space-y-3 text-sm leading-5 text-[var(--patch-text)]">
                      <li>1. Inspect repository structure and auth router.</li>
                      <li>2. Search login endpoint password validation context.</li>
                      <li>3. Add login success and invalid password tests.</li>
                      <li>4. Run pytest and ruff check.</li>
                      <li>5. Generate diff for human review.</li>
                    </ol>
                  </Card>
                  <Card className="p-5">
                    <SectionHeading title="Tool Calls" />
                    <div className="mt-4 space-y-3">
                      <ToolCall label="search_code" value="app/routers/auth.py / score 0.89" />
                      <ToolCall label="read_file" value="tests/conftest.py" />
                      <ToolCall label="run_command" value="uv run pytest" />
                      <ToolCall label="get_git_diff" value="2 files changed" />
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
                  main
                </button>
                <button
                  type="button"
                  className="hidden h-10 items-center gap-2 rounded-full border border-[var(--patch-border)] bg-[var(--patch-bg)] px-4 text-sm text-[var(--patch-ink)] transition hover:bg-[var(--patch-border)] md:flex"
                >
                  <Terminal size={15} />
                  pytest + ruff
                </button>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setActive("run")}
                    className="flex h-10 items-center gap-2 rounded-full bg-[var(--patch-accent)] px-4 text-sm font-medium text-white"
                  >
                    <Play size={16} />
                    Start run
                  </button>
                  <button
                    type="button"
                    aria-label="Open review"
                    onClick={() => setActive("pr")}
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
                  <StatusLine label="Repo" value="fastapi-auth-app" />
                  <StatusLine label="Branch" value="main" />
                  <StatusLine label="Workspace" value="/workspaces/run_123/repo" />
                  <StatusLine label="Credential" value="github_token_prod_01" />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Developer Journey" />
                <div className="mt-4 space-y-3">
                  <JourneyItem label="Describe task" value="instruction captured" active />
                  <JourneyItem label="Agent works" value="plan, tools, command logs" active />
                  <JourneyItem label="Review diff" value="current decision point" />
                  <JourneyItem label="Create PR" value="after approval" />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Verification" />
                <div className="mt-4 space-y-3">
                  <StatusLine label="pytest" value="12 passed" />
                  <StatusLine label="ruff" value="passed" />
                  <StatusLine label="retry budget" value="1 attempt" />
                </div>
              </Card>

              <Card className="p-5">
                <SectionHeading title="Diff Review" action={<Badge tone="inverse">ready</Badge>} />
                <p className="mt-3 text-sm leading-5 text-[var(--patch-muted)]">
                  Next best action: inspect changed files, then approve or reject. Rejection ends the MVP run and clears
                  the workspace.
                </p>
                <div className="mt-4 space-y-3 text-sm">
                  <FileRow path="tests/test_auth.py" additions="+82" deletions="-0" />
                  <FileRow path="app/auth/routes.py" additions="+4" deletions="-1" />
                </div>
                <div className="mt-5 grid gap-3">
                  <Button onClick={() => setActive("pr")}>
                    <FileCode2 size={15} />
                    Open Diff
                  </Button>
                  <Button variant="secondary" onClick={() => setActive("pr")}>
                    <GitPullRequest size={15} />
                    Approve PR
                  </Button>
                </div>
              </Card>

              <Card surface="dark" className="p-5">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  <ShieldCheck size={16} />
                  Guardrails
                </div>
                <p className="mt-3 text-sm leading-6 text-[var(--patch-on-dark-muted)]">
                  Blocked commands, secret protection, isolated workspace, and human approval are enforced for the MVP
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
