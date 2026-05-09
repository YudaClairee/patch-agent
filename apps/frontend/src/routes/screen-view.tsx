import { useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AgentRun } from "../sections/agent-run";
import { AppShell } from "../sections/app-shell";
import { Dashboard } from "../sections/dashboard";
import { HomePage } from "../sections/home-page";
import { NewTask } from "../sections/new-task";
import { PRResult } from "../sections/pr-result";
import { RepositorySetup } from "../sections/repository-setup";
import { type ScreenId, type SetActive, screenRoutes, useWorkspaceSummary } from "../wireframe-data";

type ScreenViewProps = {
  initialScreen?: ScreenId;
};

export default function ScreenView({ initialScreen = "home" }: ScreenViewProps) {
  const [active, setActive] = useState<ScreenId>(initialScreen);
  const navigate = useNavigate();
  const { data: summary } = useWorkspaceSummary();

  useEffect(() => {
    setActive(initialScreen);
  }, [initialScreen]);

  const navigateToScreen: SetActive = (screen) => {
    setActive(screen);
    void navigate({ to: screenRoutes[screen] });
  };

  if (active === "home") {
    return <HomePage setActive={navigateToScreen} workspaceSummary={summary} />;
  }

  return (
    <AppShell active={active} setActive={navigateToScreen} workspaceSummary={summary}>
      {active === "dashboard" && <Dashboard setActive={navigateToScreen} workspaceSummary={summary} />}
      {active === "repo" && <RepositorySetup setActive={navigateToScreen} />}
      {active === "task" && <NewTask setActive={navigateToScreen} />}
      {active === "run" && <AgentRun setActive={navigateToScreen} />}
      {active === "pr" && <PRResult />}
    </AppShell>
  );
}
