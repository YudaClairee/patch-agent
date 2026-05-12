import { createRootRoute, createRoute, Outlet } from "@tanstack/react-router";
import { LoginPage } from "../sections/login-page";
import { SignUpPage } from "../sections/signup-page";
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

export const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  signupRoute,
  dashboardRoute,
  repoRoute,
  taskRoute,
  runRoute,
  diffRoute,
  prRoute,
]);
