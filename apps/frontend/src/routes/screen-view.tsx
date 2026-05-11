import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AgentRun } from "../sections/agent-run";
import { AppShell } from "../sections/app-shell";
import { Dashboard } from "../sections/dashboard";
import { DiffReview } from "../sections/diff-review";
import { HomePage } from "../sections/home-page";
import { NewTask } from "../sections/new-task";
import { PRResult } from "../sections/pr-result";
import { RepositorySetup } from "../sections/repository-setup";
import { type ScreenId, type SetActive, screenRoutes, useDashboardRead } from "../wireframe-data";

type ScreenViewProps = {
  initialScreen?: ScreenId;
};

export default function ScreenView({ initialScreen = "home" }: ScreenViewProps) {
  const [active, setActive] = useState<ScreenId>(initialScreen);
  const navigate = useNavigate();
  const { data: dashboardRead } = useDashboardRead();

  useEffect(() => {
    setActive(initialScreen);
  }, [initialScreen]);

  const navigateToScreen: SetActive = (screen) => {
    setActive(screen);
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
      {active === "run" && <AgentRun setActive={navigateToScreen} />}
      {active === "diff" && <DiffReview setActive={navigateToScreen} />}
      {active === "pr" && <PRResult />}
    </AppShell>
  );
}
