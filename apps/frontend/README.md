# P.A.T.C.H. Frontend

React + Vite frontend prototype untuk P.A.T.C.H. Aplikasi ini memakai TanStack Router, TanStack Query, Tailwind CSS, Framer Motion, Lucide React, Biome, pnpm workspace, dan shared UI package lokal `@patch/ui`.

Dokumentasi lengkap frontend dan panduan integrasi backend ada di [FRONTEND.md](./FRONTEND.md). Product requirement ada di [PRD Project P A T C H.md](./PRD%20Project%20P%20A%20T%20C%20H.md).

## Quick Start

Jalankan dari folder `apps/frontend`:

```bash
pnpm install
pnpm run dev
```

Command umum:

```bash
pnpm run check         # Biome check
pnpm run typecheck     # TypeScript check untuk @patch/ui dan app
pnpm run format        # format frontend workspace
pnpm run build         # production build ke dist/
pnpm run preview       # preview hasil build
pnpm run ci            # check + typecheck + build
```

## Structure

```text
apps/frontend/
  index.html              Vite HTML shell dan #root
  vite.config.mjs         Vite config aktif
  package.json            scripts dan dependency frontend
  pnpm-workspace.yaml     workspace lokal untuk packages/*
  biome.json              formatter/linter config
  moon.yml                Moon project config untuk client
  public/
    patch.svg             logo aplikasi
    patchLogo.svg         favicon SVG
  src/
    index.tsx             React mount
    app.tsx               QueryClientProvider + AppRouter
    styles.css            Tailwind + @patch/ui styles
    wireframe-data.ts     mock data, route map, screen metadata
    routes/
      index.tsx           TanStack Router provider
      route-tree.tsx      route definitions
      screen-view.tsx     route-to-section bridge
    sections/
      home-page.tsx
      app-shell.tsx
      dashboard.tsx
      repository-setup.tsx
      new-task.tsx
      agent-run.tsx
      diff-review.tsx
      pr-result.tsx
  packages/
    ui/                   shared UI primitives, tokens, utilities
```

## Routes

```text
/           home
/dashboard  operations dashboard
/repo       repository setup
/task       new task
/run        agent run
/diff       diff review
/pr         pull request result
```

## Shared UI

Import reusable UI dari package lokal:

```tsx
import { Badge, Button, Card, SectionHeading } from "@patch/ui";
```

Shared package berada di `packages/ui` dan berisi component primitive, token CSS `--patch-*`, `patchClasses`, dan helper `cn()`.

## Notes

- Data UI saat ini masih mock di `src/wireframe-data.ts`.
- Backend integration contract ada di bagian **Backend Handoff Guide** pada [FRONTEND.md](./FRONTEND.md).
- File Vite aktif hanya `vite.config.mjs`; tidak ada generated route tree yang dipakai saat ini.
