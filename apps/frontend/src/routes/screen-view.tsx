import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AgentRun } from "../sections/agent-run";
import { AppShell } from "../sections/app-shell";
import { ConnectPat } from "../sections/auth/connect-pat";
import { Dashboard } from "../sections/dashboard";
import { DiffReview } from "../sections/diff-review";
import { HomePage } from "../sections/home-page";
import { NewTask } from "../sections/new-task";
import { PRResult } from "../sections/pr-result";
import { RepositorySetup } from "../sections/repository-setup";
import { emptyDashboardRead, type ScreenId, type SetActive, screenRoutes, useDashboardRead } from "../wireframe-data";

type ScreenViewProps = {
  initialScreen?: ScreenId;
  runId?: string;
};

export default function ScreenView({ initialScreen = "home", runId }: ScreenViewProps) {
  const [active, setActive] = useState<ScreenId>(initialScreen);
  const navigate = useNavigate();
  const { data: dashboardRead = emptyDashboardRead } = useDashboardRead();

  useEffect(() => {
    setActive(initialScreen);
  }, [initialScreen]);

  const navigateToScreen: SetActive = (screen) => {
    setActive(screen);
    if (runId && screen === "run") {
      void navigate({ to: "/run/$id", params: { id: runId } });
      return;
    }
    if (runId && screen === "diff") {
      void navigate({ to: "/run/$id/diff", params: { id: runId } });
      return;
    }
    if (runId && screen === "pr") {
      void navigate({ to: "/run/$id/pr", params: { id: runId } });
      return;
    }

    void navigate({ to: screenRoutes[screen] });
  };

  if (active === "home") {
    return <HomePage setActive={navigateToScreen} dashboardRead={dashboardRead} />;
  }

  return (
    <AppShell active={active} setActive={navigateToScreen} dashboardRead={dashboardRead}>
      {active === "dashboard" && <Dashboard setActive={navigateToScreen} dashboardRead={dashboardRead} />}
      {active === "repo" && <RepositorySetup setActive={navigateToScreen} />}
      {active === "task" && <NewTask setActive={navigateToScreen} />}
      {active === "run" && <AgentRun runId={runId} setActive={navigateToScreen} />}
      {active === "diff" && <DiffReview runId={runId} setActive={navigateToScreen} />}
      {active === "pr" && <PRResult runId={runId} />}
      {active === "settings" && <ConnectPat />}
    </AppShell>
  );
}
