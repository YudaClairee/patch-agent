# P.A.T.C.H. Frontend

React + Vite frontend for P.A.T.C.H. It uses TanStack Router, TanStack Query, Tailwind CSS, Biome, pnpm workspaces, and the local shared UI package `@patch/ui`.

Deployment notes for the full app live in [../../deployment.md](../../deployment.md).

## Quick Start

Run from `apps/frontend`:

```bash
pnpm install
pnpm run dev
```

The Vite dev server defaults to:

```text
http://localhost:5173
```

Make sure the backend env allows this origin:

```env
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173
```

## Environment

Copy the example env when running locally:

```bash
cp .env.example .env
```

Variables:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

These are Vite build-time variables. For Docker/VM deployment, export production values before `docker compose build`:

```bash
export VITE_API_BASE_URL=https://api.patch.example.com
export VITE_WS_BASE_URL=wss://api.patch.example.com
```

## Commands

```bash
pnpm run check         # Biome check
pnpm run typecheck     # TypeScript check for @patch/ui and app
pnpm run format        # Format frontend workspace
pnpm run build         # Production build to dist/
pnpm run preview       # Preview production build
pnpm run ci            # check + typecheck + build
```

Moon equivalents from the repository root:

```bash
moon run client:dev
moon run client:check
moon run client:typecheck
moon run client:build
```

## Structure

```text
apps/frontend/
  index.html              Vite HTML shell and #root
  vite.config.mjs         Vite config
  package.json            scripts and dependencies
  pnpm-workspace.yaml     local workspace for packages/*
  biome.json              formatter/linter config
  nginx.conf              production static file server config
  Dockerfile              production frontend image
  public/
    patch.svg
    patchLogo.svg
  src/
    index.tsx             React mount
    app.tsx               QueryClientProvider + AppRouter
    api-contract.ts       frontend-facing API contract helpers/types
    styles.css            Tailwind + @patch/ui styles
    lib/
      api.ts              API client and WebSocket URL creation
      queries.ts          TanStack Query hooks
      run-format.ts       run display helpers
      ws.ts               WebSocket helpers
    routes/
      index.tsx           TanStack Router provider
      route-tree.tsx      route definitions
    sections/
      login-page.tsx
      runs-list.tsx
      repo-detail.tsx
      run-detail.tsx
  packages/
    ui/                   shared UI primitives, tokens, utilities
```

## Routes

```text
/                 runs list / home
/login            GitHub OAuth login
/repo/$id         repository detail
/run/$id          agent run detail
```

## Production Build

```bash
pnpm run build
```

The Docker image builds the static app and serves `dist/` with Nginx on container port `3000`.

For production, the frontend must be built with public backend URLs. If the image was built with localhost values, browser requests from users will try to reach their own machines instead of your VM.

## Shared UI

Import reusable UI from the local package:

```tsx
import { Badge, Button, Card, SectionHeading } from "@patch/ui";
```

The shared package lives in `packages/ui` and includes component primitives, CSS tokens, `patchClasses`, and `cn()`.
