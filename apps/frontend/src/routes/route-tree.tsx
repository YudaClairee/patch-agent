import { createRootRoute, createRoute, Outlet } from "@tanstack/react-router";
import { ConnectPat } from "../sections/auth/connect-pat";
import { LoginPage } from "../sections/login-page";
import { SignUpPage } from "../sections/signup-page";
import type { ScreenId } from "../wireframe-data";
import ScreenView from "./screen-view";

type ScreenRoutePath = "/" | "dashboard" | "repo" | "task" | "run" | "diff" | "pr" | "settings/github";

const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

const makeScreenRoute = <TPath extends ScreenRoutePath>(path: TPath, initialScreen: ScreenId) =>
  createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <ScreenView initialScreen={initialScreen} />,
  });

const indexRoute = makeScreenRoute("/", "home");
const dashboardRoute = makeScreenRoute("dashboard", "dashboard");
const repoRoute = makeScreenRoute("repo", "repo");
const taskRoute = makeScreenRoute("task", "task");
const runRoute = makeScreenRoute("run", "run");
const diffRoute = makeScreenRoute("diff", "diff");
const prRoute = makeScreenRoute("pr", "pr");
const settingsRoute = makeScreenRoute("settings/github", "settings");
const runDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "run/$id",
  component: RunDetailRoute,
});
const runDiffRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "run/$id/diff",
  component: RunDiffRoute,
});
const runPrRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "run/$id/pr",
  component: RunPrRoute,
});
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "login",
  component: LoginPage,
});
const signupRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "signup",
  component: SignUpPage,
});
const connectPatRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "auth/connect-pat",
  component: ConnectPat,
});

function RunDetailRoute() {
  const { id } = runDetailRoute.useParams();

  return <ScreenView initialScreen="run" runId={id} />;
}

function RunDiffRoute() {
  const { id } = runDiffRoute.useParams();

  return <ScreenView initialScreen="diff" runId={id} />;
}

function RunPrRoute() {
  const { id } = runPrRoute.useParams();

  return <ScreenView initialScreen="pr" runId={id} />;
}

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  signupRoute,
  connectPatRoute,
  dashboardRoute,
  repoRoute,
  taskRoute,
  runRoute,
  runDetailRoute,
  diffRoute,
  runDiffRoute,
  prRoute,
  runPrRoute,
  settingsRoute,
]);
