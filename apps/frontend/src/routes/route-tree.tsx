import { createRootRoute, createRoute, Outlet, redirect } from "@tanstack/react-router";
import { ApiClientError, patchApi } from "../lib/api";
import { LoginPage } from "../sections/login-page";
import { RepoDetail } from "../sections/repo-detail";
import { RunDetail } from "../sections/run-detail";
import { RunsList } from "../sections/runs-list";

const rootRoute = createRootRoute({
  component: () => <Outlet />,
});

const requireAuth = async () => {
  try {
    await patchApi.getMe();
  } catch (err) {
    if (err instanceof ApiClientError && err.status === 401) {
      throw redirect({ to: "/login" });
    }
    throw err;
  }
};

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  beforeLoad: requireAuth,
  component: RunsList,
});

const runDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "run/$id",
  beforeLoad: requireAuth,
  component: RunDetailRoute,
});

function RunDetailRoute() {
  const { id } = runDetailRoute.useParams();
  return <RunDetail runId={id} />;
}

const repoDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "repo/$id",
  beforeLoad: requireAuth,
  component: RepoDetailRoute,
});

function RepoDetailRoute() {
  const { id } = repoDetailRoute.useParams();
  return <RepoDetail repoId={id} />;
}

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "login",
  component: LoginPage,
});

export const routeTree = rootRoute.addChildren([indexRoute, loginRoute, runDetailRoute, repoDetailRoute]);
