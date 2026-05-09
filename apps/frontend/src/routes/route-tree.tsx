import { createRootRoute, createRoute, Outlet } from "@tanstack/react-router";
import type { ScreenId } from "../wireframe-data";
import ScreenView from "./screen-view";

type ScreenRoutePath = "/" | "dashboard" | "repo" | "task" | "run" | "diff" | "pr";

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

export const routeTree = rootRoute.addChildren([
  indexRoute,
  dashboardRoute,
  repoRoute,
  taskRoute,
  runRoute,
  diffRoute,
  prRoute,
]);
