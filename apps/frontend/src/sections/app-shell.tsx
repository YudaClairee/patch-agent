import { Badge, Button, cn, patchClasses } from "@patch/ui";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, ChevronRight, FolderGit, Loader2, LogOut, Plus, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";
import { ApiClientError, type DashboardRead, patchApi } from "../api-contract";
import { formatDashboardUsage, type ScreenId, type SetActive, screenMeta, screens } from "../wireframe-data";

type ActiveScreenProps = {
  active: ScreenId;
  setActive: SetActive;
};

export function AppShell({
  active,
  setActive,
  dashboardRead,
  children,
}: ActiveScreenProps & { dashboardRead: DashboardRead; children: ReactNode }) {
  const meta = screenMeta[active];
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [logoutState, setLogoutState] = useState<"idle" | "loading" | "error">("idle");
  const [logoutError, setLogoutError] = useState<string | undefined>();
  const isLoggingOut = logoutState === "loading";

  const finishLogout = () => {
    queryClient.clear();
    void navigate({ to: "/login" });
  };

  const handleLogout = async () => {
    if (isLoggingOut) {
      return;
    }

    setLogoutState("loading");
    setLogoutError(undefined);

    try {
      await patchApi.logout();
      finishLogout();
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 401) {
        finishLogout();
        return;
      }

      setLogoutState("error");
      setLogoutError(error instanceof Error ? error.message : "Log out gagal. Coba lagi.");
    }
  };

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
              <Badge>{dashboardRead.active_run_count} active</Badge>
            </div>
            <div className="mt-4 space-y-3">
              <MiniMeter label="Active" value={`${dashboardRead.active_run_count} runs`} width="w-[42%]" />
              <MiniMeter label="Today" value={`${dashboardRead.today_run_count} runs`} width="w-[68%]" />
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
            <LogoutButton isLoading={isLoggingOut} onClick={handleLogout} className="mt-4 w-full" />
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
            <LogoutButton isLoading={isLoggingOut} onClick={handleLogout} className="shrink-0" />
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
                  Diff Review
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
            <AnimatePresence mode="wait">
              {logoutError && (
                <motion.p
                  key="logout-error"
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="mt-3 rounded-[18px] border border-[var(--patch-border-strong)] bg-[var(--patch-bg)] px-4 py-3 text-sm text-[var(--patch-ink)]"
                >
                  {logoutError}
                </motion.p>
              )}
            </AnimatePresence>
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
            <span className="hidden md:inline">{formatDashboardUsage(dashboardRead)}</span>
          </footer>
        </main>
      </div>
    </div>
  );
}

type LogoutButtonProps = {
  isLoading: boolean;
  onClick: () => void;
  className?: string;
};

function LogoutButton({ isLoading, onClick, className }: LogoutButtonProps) {
  return (
    <Button
      variant="danger"
      onClick={onClick}
      disabled={isLoading}
      aria-label="Log out dari workspace"
      className={cn("active:scale-[0.98]", className)}
    >
      {isLoading ? <Loader2 size={15} className="animate-spin" /> : <LogOut size={15} />}
      {isLoading ? "Logging out" : "Log out"}
    </Button>
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
