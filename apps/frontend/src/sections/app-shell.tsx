import { Badge, Button, cn, patchClasses } from "@patch/ui";
import { motion } from "framer-motion";
import { Activity, ChevronRight, FolderGit, Plus, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { type ScreenId, type SetActive, screenMeta, screens, type WorkspaceSummary } from "../wireframe-data";

type ActiveScreenProps = {
  active: ScreenId;
  setActive: SetActive;
};

export function AppShell({
  active,
  setActive,
  workspaceSummary,
  children,
}: ActiveScreenProps & { workspaceSummary: WorkspaceSummary; children: ReactNode }) {
  const meta = screenMeta[active];

  return (
    <div className={cn("h-screen overflow-hidden", patchClasses.appSurface)}>
      <div className="flex h-screen">
        <aside className="hidden w-[280px] shrink-0 border-r border-[var(--patch-border)] bg-[var(--patch-bg)] p-4 md:flex md:flex-col">
          <button
            type="button"
            onClick={() => setActive("home")}
            className="mb-5 flex w-full items-center justify-center rounded-[24px] border border-[var(--patch-border)] bg-[var(--patch-surface)] p-4 text-left"
          >
            <img src="/patch.svg" alt="P.A.T.C.H." className="h-12 w-auto max-w-full object-contain" />
          </button>

          <nav className="space-y-1.5">
            {screens.map((screen) => (
              <button
                key={screen.id}
                type="button"
                onClick={() => setActive(screen.id)}
                className={`flex min-h-10 w-full items-center justify-between rounded-full px-3.5 text-sm font-medium tracking-[-0.003em] transition ${
                  active === screen.id
                    ? "border border-[var(--patch-border)] bg-[var(--patch-surface)] text-[var(--patch-ink)]"
                    : "text-[var(--patch-text)] hover:bg-[var(--patch-surface-translucent)] hover:text-[var(--patch-ink)]"
                }`}
              >
                <span>{screen.label}</span>
                <ChevronRight
                  size={15}
                  className={active === screen.id ? "text-[var(--patch-ink)]" : "text-[var(--patch-muted)]"}
                />
              </button>
            ))}
          </nav>

          <div className="mt-5 rounded-[24px] border border-[var(--patch-border)] bg-[var(--patch-surface)] p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Activity size={16} />
                Agent pool
              </div>
              <Badge>{workspaceSummary.activeRunCount} active</Badge>
            </div>
            <div className="mt-4 space-y-3">
              <MiniMeter label="CPU" value="42%" width="w-[42%]" />
              <MiniMeter label="Queue" value="3 runs" width="w-[68%]" />
            </div>
          </div>

          <div className="mt-auto rounded-[24px] bg-[var(--patch-ink)] p-4 text-white">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <ShieldCheck size={16} />
              Review gate
            </div>
            <p className="mt-2 text-xs leading-5 text-[var(--patch-on-dark-muted)]">
              Pull request dibuat setelah diff disetujui.
            </p>
          </div>
        </aside>

        <main className="flex min-w-0 flex-1 flex-col bg-[var(--patch-bg)]">
          <div className="flex shrink-0 gap-2 overflow-x-auto border-b border-[var(--patch-border)] bg-[var(--patch-surface)] px-4 py-3 md:hidden">
            {screens.map((screen) => (
              <button
                key={screen.id}
                type="button"
                onClick={() => setActive(screen.id)}
                className={`min-h-9 shrink-0 rounded-full px-3.5 text-sm font-medium ${
                  active === screen.id
                    ? "bg-[var(--patch-ink)] text-white"
                    : "bg-[var(--patch-bg)] text-[var(--patch-text)]"
                }`}
              >
                {screen.label}
              </button>
            ))}
          </div>

          <div className="shrink-0 border-b border-[var(--patch-border)] bg-[var(--patch-surface)] px-5 py-4">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-2xl font-bold leading-tight tracking-[-0.36px] md:text-[32px]">{meta.title}</h1>
                </div>
                <p className="mt-1 max-w-3xl text-sm leading-5 tracking-[-0.003em] text-[var(--patch-muted)]">
                  {meta.subtitle}
                </p>
              </div>

              <div className="flex flex-wrap gap-2 xl:justify-end">
                <Button variant="chip" onClick={() => setActive("diff")}>
                  <ShieldCheck size={15} />
                  Review
                </Button>
                <Button variant="secondary" onClick={() => setActive("run")}>
                  <Activity size={15} />
                  Active Run
                </Button>
                <Button variant="chip" onClick={() => setActive("repo")}>
                  <FolderGit size={15} />
                  Repositories
                </Button>
                <Button onClick={() => setActive("task")}>
                  <Plus size={15} />
                  New Task
                </Button>
              </div>
            </div>
          </div>

          <motion.div
            key={active}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18 }}
            className="min-h-0 flex-1 overflow-auto p-4 md:p-5"
          >
            {children}
          </motion.div>

          <footer className="flex h-9 shrink-0 items-center justify-between border-t border-[var(--patch-border)] bg-[var(--patch-surface)] px-4 text-xs text-[var(--patch-muted)]">
            <span className="truncate">workspace / fastapi-auth-app / main</span>
            <span className="hidden md:inline">{workspaceSummary.verificationStatus}</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

type MiniMeterProps = {
  label: string;
  value: string;
  width: string;
};

function MiniMeter({ label, value, width }: MiniMeterProps) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs text-[var(--patch-muted)]">
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--patch-border)]">
        <div className={`h-full rounded-full bg-[var(--patch-ink)] ${width}`} />
      </div>
    </div>
  );
}
