# Frontend Documentation

Dokumentasi ini adalah source of truth untuk frontend P.A.T.C.H. di `apps/frontend`.
Project saat ini adalah prototype React + Vite dengan shared UI package lokal `@patch/ui`.

## Overview

Struktur frontend berada di satu pnpm workspace lokal:

```text
apps/frontend/
  index.html
  package.json
  pnpm-workspace.yaml
  vite.config.mjs
  src/
    index.tsx
    app.tsx
    styles.css
    wireframe-data.ts
    routes/
    sections/
  packages/
    ui/
```

Alur render utama:

```text
src/index.tsx
  -> src/app.tsx
  -> src/routes/index.tsx
  -> src/routes/route-tree.tsx
  -> src/routes/screen-view.tsx
  -> src/sections/*
```

## Tech Stack

- React 19
- Vite 8
- TypeScript 6
- TanStack Router
- TanStack Query
- Tailwind CSS 4
- Framer Motion
- Lucide React
- Biome
- pnpm workspace
- Moon task runner, untuk integrasi root monorepo

## Setup

Jalankan dari folder `apps/frontend`:

```bash
pnpm install
pnpm run dev
```

Dev server memakai Vite. Jangan memakai VS Code Live Server untuk menjalankan file TSX karena app perlu bundling Vite.

## Commands

Command utama dari `apps/frontend`:

```bash
pnpm run dev           # start Vite dev server
pnpm run check         # Biome check untuk app dan packages/ui
pnpm run typecheck     # TypeScript check untuk packages/ui dan app
pnpm run format        # format workspace frontend
pnpm run format:check  # cek format tanpa menulis file
pnpm run build         # production build ke dist/
pnpm run preview       # preview hasil build
pnpm run ci            # check + typecheck + build
```

Command Moon dari root repo tetap tersedia untuk workflow monorepo:

```bash
moon run client:dev
moon run client:check
moon run client:typecheck
moon run client:build
moon run ui:check
moon run ui:typecheck
```

Project Moon terkait:

```text
client -> apps/frontend
ui     -> apps/frontend/packages/ui
```

## App Structure

```text
src/
  index.tsx              React mount ke #root
  app.tsx                QueryClientProvider + AppRouter
  styles.css             Tailwind import + @patch/ui styles
  wireframe-data.ts      mock data, route map, metadata screen
  routes/
    index.tsx            createRouter + RouterProvider
    route-tree.tsx       TanStack Router route tree
    screen-view.tsx      bridge route aktif ke screen component
  sections/
    home-page.tsx
    app-shell.tsx
    dashboard.tsx
    repository-setup.tsx
    new-task.tsx
    agent-run.tsx
    diff-review.tsx
    pr-result.tsx
```

`public/patch.svg` adalah asset publik untuk logo aplikasi. `public/patchLogo.svg` dipakai sebagai favicon web. File manifest/icon lama dari scaffold sudah tidak dipakai.

## Routes

Route didefinisikan di `src/routes/route-tree.tsx`.

```text
/           -> home
/dashboard  -> dashboard
/repo       -> repository setup
/task       -> new task
/run        -> agent run
/diff       -> diff review
/pr         -> PR result
```

Jika menambah screen baru:

1. Tambahkan item di `screens` pada `src/wireframe-data.ts`.
2. Tambahkan path di `screenRoutes`.
3. Tambahkan metadata di `screenMeta`.
4. Tambahkan route di `src/routes/route-tree.tsx`.
5. Render section baru di `src/routes/screen-view.tsx`.

Tidak ada generated route tree yang dipakai saat ini. Jangan menambahkan kembali `routeTree.gen.ts` kecuali app kembali memakai file-router generator.

## Shared UI

Shared UI package berada di `packages/ui`.

```text
packages/ui/
  package.json
  tsconfig.json
  src/
    index.ts
    styles.css
    tokens.ts
    classes.ts
    lib/
      utils.ts
    components/
      badge.tsx
      button.tsx
      card.tsx
      input.tsx
      textarea.tsx
      workspace.tsx
```

Import shared component dari package:

```tsx
import { Badge, Button, Card, SectionHeading } from "@patch/ui";
```

`@patch/ui` mengekspor:

- `Badge`
- `Button`
- `Card`
- `Input`
- `Textarea`
- `SectionHeading`
- `StatusLine`
- `Field`
- `FileRow`
- `cn`
- `patchClasses`
- `patchColors`
- `patchCssVars`

Letakkan primitive lintas screen di `packages/ui/src/components`. Letakkan component yang spesifik workflow produk di `src/sections`.

## Styling

Style app memuat Tailwind dan token UI lewat `src/styles.css`:

```css
@import "tailwindcss";
@import "@patch/ui/styles.css";

@source "../packages/ui/src";
```

Token warna dan CSS variable berada di:

```text
packages/ui/src/styles.css
packages/ui/src/tokens.ts
```

Gunakan variable `--patch-*` untuk warna:

```tsx
<div className="bg-[var(--patch-bg)] text-[var(--patch-ink)]" />
```

Aturan styling:

- Gunakan `@patch/ui` untuk primitive umum.
- Gunakan `lucide-react` untuk icon.
- Gunakan `cn()` untuk class kondisional.
- Hindari hard-coded color di `src/sections`.
- Tombol custom harus punya `type="button"` kecuali memang submit form.
- Jaga tampilan tetap app-like dan operational, bukan landing page marketing.

## Data Flow

Data masih mock di `src/wireframe-data.ts`.

```text
wireframe-data.ts
  -> useWorkspaceSummary()
  -> TanStack Query initialData
  -> HomePage, Dashboard, AppShell
```

Saat backend API siap, pertahankan pola ini:

- fetcher dipisahkan dari component visual
- query key stabil
- loading/error state ditangani dekat surface yang memakainya
- section menerima data melalui props atau hook yang spesifik
- URL backend dibaca dari env Vite, bukan hard-code di section

Contoh env:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Backend Integration Targets

Prioritas integrasi:

1. Workspace summary dan daftar repository.
2. Repository setup.
3. Task creation.
4. Agent run status dan timeline.
5. Diff review.
6. Pull request result.

Suggested endpoints:

```text
GET    /api/workspace/summary
GET    /api/repositories
POST   /api/repositories
GET    /api/runs
POST   /api/runs
GET    /api/runs/:runId
GET    /api/runs/:runId/diff
POST   /api/runs/:runId/approve
POST   /api/runs/:runId/reject
GET    /api/pull-requests/:pullRequestId
```

Response sukses sebaiknya konsisten:

```json
{
  "data": {},
  "meta": {}
}
```

Response error:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Repository URL is required",
    "details": {}
  }
}
```

## Backend Handoff Guide

Bagian ini ditujukan untuk engineer backend yang akan menghubungkan API ke UI. Frontend saat ini masih mock-only, jadi integrasi paling aman adalah menambahkan layer API tanpa mengubah struktur visual besar di `src/sections`.

### Frontend Runtime Contract

Frontend akan membaca backend base URL dari env Vite:

```text
VITE_API_BASE_URL=http://localhost:8000
```

Jika env belum ada, frontend boleh fallback ke `http://localhost:8000` saat development. Semua request API sebaiknya masuk lewat satu client, misalnya:

```text
src/api/client.ts
src/api/repositories.ts
src/api/runs.ts
```

Jangan menyebar `fetch("/api/...")` langsung di banyak section. Section harus tetap fokus pada UI; hook/query API boleh berada di file data/API khusus.

### CORS And Local Development

Saat frontend dev server berjalan di Vite, backend perlu mengizinkan origin lokal berikut:

```text
http://localhost:5173
http://127.0.0.1:5173
```

Jika Vite dijalankan di port lain, gunakan nilai origin dari environment backend. Untuk auth berbasis cookie, aktifkan credentials di CORS dan gunakan cookie `HttpOnly`, `Secure` untuk production, serta `SameSite=Lax` atau `Strict` sesuai kebutuhan flow login.

### Endpoint Ownership

| UI Surface | File Frontend | Endpoint Backend | Tujuan |
| --- | --- | --- | --- |
| Home summary | `src/sections/home-page.tsx` | `GET /api/workspace/summary` | Angka repo, run aktif, review, PR, usage label |
| Repository list | `src/sections/home-page.tsx`, `dashboard.tsx` | `GET /api/repositories` | Daftar repo untuk sidebar dan dashboard |
| Repository setup | `src/sections/repository-setup.tsx` | `POST /api/repositories` | Simpan repository, branch, command, credential ref |
| New task | `src/sections/new-task.tsx`, `home-page.tsx` | `POST /api/runs` | Membuat run agent dari instruksi user |
| Agent run | `src/sections/agent-run.tsx` | `GET /api/runs/:runId` | Status, plan, tool calls, logs, changed files |
| Diff review | `src/sections/diff-review.tsx` | `GET /api/runs/:runId/diff` | Summary diff, patch per file, hasil verifikasi |
| Approve/reject | `src/sections/diff-review.tsx` | `POST /api/runs/:runId/approve`, `POST /api/runs/:runId/reject` | Gate sebelum PR dibuat |
| PR result | `src/sections/pr-result.tsx` | `GET /api/pull-requests/:pullRequestId` | URL PR, branch, status, verification badges |

Route frontend sekarang masih static (`/run`, `/diff`, `/pr`). Backend tetap sebaiknya mengembalikan `runId` dan `pullRequestId` agar frontend nanti mudah naik ke route dynamic seperti `/runs/:runId`.

### Minimum Payloads

Workspace summary:

```json
{
  "data": {
    "repositoryCount": 3,
    "activeRunCount": 2,
    "reviewRequiredCount": 1,
    "pullRequestCount": 7,
    "verificationStatus": "pytest passed - ruff passed - review required",
    "usageLabel": "Daily agent run usage (6/15)"
  }
}
```

Repository list:

```json
{
  "data": [
    {
      "id": "repo_123",
      "name": "fastapi-auth-app",
      "url": "git@github.com:user/fastapi-auth-app.git",
      "branch": "main",
      "status": "indexed",
      "language": "Python",
      "credentialRef": "github_token_prod_01",
      "setupCommand": "uv sync",
      "testCommand": "uv run pytest",
      "lintCommand": "uv run ruff check .",
      "workingDirectory": "./"
    }
  ],
  "meta": {
    "total": 1,
    "cursor": null
  }
}
```

Create repository request:

```json
{
  "name": "fastapi-auth-app",
  "url": "git@github.com:user/fastapi-auth-app.git",
  "branch": "main",
  "credentialRef": "github_token_prod_01",
  "setupCommand": "uv sync",
  "testCommand": "uv run pytest",
  "lintCommand": "uv run ruff check .",
  "workingDirectory": "./"
}
```

Create run request:

```json
{
  "repositoryId": "repo_123",
  "targetBranch": "main",
  "instruction": "Tambahkan unit test untuk endpoint login.",
  "setupCommandOverride": null,
  "testCommandOverride": "uv run pytest",
  "lintCommandOverride": "uv run ruff check ."
}
```

Create run response:

```json
{
  "data": {
    "runId": "run_123",
    "status": "queued",
    "traceId": "lf_9a12"
  }
}
```

Run detail:

```json
{
  "data": {
    "id": "run_123",
    "repositoryId": "repo_123",
    "repositoryName": "fastapi-auth-app",
    "task": "Tambahkan unit test untuk endpoint login.",
    "branch": "patch/run_123",
    "status": "review_required",
    "traceId": "lf_9a12",
    "plan": [
      "Inspect repository structure.",
      "Add login success and invalid password tests.",
      "Run pytest and ruff check."
    ],
    "toolCalls": [
      {
        "id": "tool_1",
        "name": "run_command",
        "value": "uv run pytest",
        "status": "success"
      }
    ],
    "logs": [
      {
        "id": "log_1",
        "level": "info",
        "message": "12 passed in 2.41s",
        "createdAt": "2026-05-06T13:00:00Z"
      }
    ],
    "verification": {
      "testStatus": "passed",
      "lintStatus": "passed",
      "summary": "pytest passed - ruff passed"
    },
    "changedFiles": [
      {
        "path": "tests/test_auth.py",
        "additions": 82,
        "deletions": 0
      }
    ]
  }
}
```

Diff response:

```json
{
  "data": {
    "runId": "run_123",
    "status": "review_required",
    "summary": "Unit test login ditambahkan dan verifikasi berhasil.",
    "files": [
      {
        "path": "tests/test_auth.py",
        "additions": 82,
        "deletions": 0,
        "patch": "diff --git a/tests/test_auth.py b/tests/test_auth.py\n..."
      }
    ],
    "verification": {
      "testsPassed": true,
      "lintPassed": true
    }
  }
}
```

Approve response:

```json
{
  "data": {
    "pullRequestId": "pr_123",
    "url": "https://github.com/user/fastapi-auth-app/pull/42",
    "branch": "patch/run_123",
    "status": "created"
  }
}
```

Pull request result:

```json
{
  "data": {
    "id": "pr_123",
    "runId": "run_123",
    "url": "https://github.com/user/fastapi-auth-app/pull/42",
    "branch": "patch/run_123",
    "status": "created",
    "verificationBadges": ["pytest passed", "ruff passed", "Langfuse trace saved"]
  }
}
```

### Status And Polling

Frontend bisa polling `GET /api/runs/:runId` dengan TanStack Query setiap 1 sampai 3 detik selama status belum terminal.

Status terminal:

```text
review_required
pr_created
failed
cancelled
```

Jika backend menyediakan streaming, prioritaskan Server-Sent Events untuk logs/status:

```text
GET /api/runs/:runId/events
```

Event stream cukup mengirim event `status`, `log`, `tool_call`, `verification`, dan `changed_files`. Polling tetap perlu tersedia sebagai fallback.

### Error Codes Expected By Frontend

Gunakan `error.code` stabil agar frontend bisa menampilkan state yang tepat.

```text
VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
REPOSITORY_NOT_FOUND
CREDENTIAL_INVALID
RUN_NOT_FOUND
RUN_NOT_REVIEWABLE
VERIFICATION_FAILED
PR_CREATE_FAILED
RATE_LIMITED
INTERNAL_ERROR
```

### Secret And Credential Rules

- Frontend hanya boleh menerima `credentialRef`.
- Backend tidak boleh mengirim raw token, private key, GitHub app private key, atau secret value lain.
- Jika credential tidak valid, kirim `CREDENTIAL_INVALID` tanpa membocorkan detail secret.
- Jangan masukkan secret ke `logs`, `toolCalls.value`, `verification.summary`, atau `patch`.
- Jika command output mengandung secret, backend harus melakukan redaction sebelum response dikirim.

### Integration Checklist

1. Tambahkan CORS untuk origin Vite lokal.
2. Implement `GET /api/workspace/summary` dan `GET /api/repositories`.
3. Ganti mock `repoRows`, `recentRuns`, dan `useWorkspaceSummary()` secara bertahap dengan TanStack Query fetcher.
4. Implement `POST /api/repositories` tanpa pernah mengembalikan secret.
5. Implement `POST /api/runs`, lalu polling `GET /api/runs/:runId`.
6. Implement diff gate: `GET /api/runs/:runId/diff`, approve, dan reject.
7. Implement `GET /api/pull-requests/:pullRequestId`.
8. Pastikan semua response memakai envelope `data/meta` atau `error`.
9. Jalankan frontend quality gate setelah integrasi:

```bash
pnpm run check
pnpm run typecheck
pnpm run build
```

## Current Data Contracts

`WorkspaceSummary` dipakai oleh `HomePage`, `Dashboard`, dan `AppShell`:

```ts
type WorkspaceSummary = {
  repositoryCount: number;
  activeRunCount: number;
  reviewRequiredCount: number;
  pullRequestCount: number;
  verificationStatus: string;
  usageLabel: string;
};
```

Repository setup hanya boleh menampilkan credential reference. Backend tidak boleh mengirim raw token, private key, atau secret value ke frontend.

Run status yang sudah dipakai UI:

```ts
type AgentRunStatus =
  | "queued"
  | "preparing_workspace"
  | "cloning_repo"
  | "indexing"
  | "planning"
  | "executing"
  | "verifying"
  | "review_required"
  | "pr_created"
  | "failed"
  | "cancelled";
```

## Files Removed From Scaffold

Frontend sudah dibersihkan dari file yang tidak lagi dipakai:

- `vite.config.ts`, config lama TanStack Start/Nitro
- `public/manifest.json`, karena masih menunjuk icon scaffold yang sudah tidak ada
- `.cta.json`, metadata generator Create TanStack App
- `DESIGN.md` dan `ux-researcher.md`, catatan/generated local yang tidak dibutuhkan runtime
- `.DS_Store`, artefak macOS

File Vite aktif sekarang hanya `vite.config.mjs`.

## Quality Gate

Sebelum submit perubahan frontend:

```bash
pnpm run check
pnpm run typecheck
pnpm run build
```

Untuk validasi Moon dari root repo:

```bash
moon run client:check
moon run client:typecheck
moon run client:build
```
