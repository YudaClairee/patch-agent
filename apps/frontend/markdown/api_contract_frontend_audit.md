# API Contract vs Frontend Audit

Sumber kontrak: `apps/frontend/markdown/api_contract.md`  
Sumber frontend yang diaudit: `apps/frontend/src` dan `apps/frontend/packages/ui/src`

## Ringkasan

- Semua endpoint HTTP/WS yang tertulis di `api_contract.md` sudah ada sebagai konstanta dan method typed client di `src/api-contract.ts`.
- Semua schema field utama dari kontrak sudah direpresentasikan sebagai TypeScript type di `src/api-contract.ts`.
- Sebagian besar endpoint Stream 4 utama sudah dipakai aktif oleh layar UI melalui React Query hook atau form submit.
- Masih ada beberapa endpoint yang tersedia di API client, tetapi belum dipakai secara aktif oleh layar UI.
- Ada beberapa variabel frontend-only untuk routing, state UI, mock data, dan helper client. Item ini tidak ada di kontrak karena bukan request/response backend.

## Perubahan Terbaru Yang Terdeteksi

- Route `/signup` sudah ditambahkan dan memakai `SignUpPage`.
- `LoginPage` sekarang memakai komponen auth bersama dari `auth-components.tsx`.
- `SignUpPage` memakai `POST /auth/signup` dan redirect ke `/dashboard` setelah cookie auth dibuat.
- `AppShell` sekarang punya tombol `Log out` untuk desktop dan mobile.
- `patchApi.logout()` sekarang dipakai aktif oleh UI, membersihkan cache React Query, lalu redirect ke `/login`.
- `fetchJson` sekarang aman untuk response sukses tanpa body, termasuk pola `204` atau body kosong dari endpoint logout/delete.

## Endpoint Kontrak Yang Sudah Ada Di Frontend

Endpoint berikut sudah ada di `apiEndpoints` dan/atau `patchApi`.

| Endpoint kontrak | Frontend |
| --- | --- |
| `POST /auth/signup` | `patchApi.signup`, `apiEndpoints.signup` |
| `POST /auth/login` | `patchApi.login`, `apiEndpoints.login` |
| `POST /auth/logout` | `patchApi.logout`, `apiEndpoints.logout` |
| `GET /me` | `patchApi.getMe`, `apiEndpoints.me` |
| `POST /me/github-credentials` | `patchApi.createGitHubCredential`, `apiEndpoints.githubCredentials` |
| `DELETE /me/github-credentials/{id}` | `patchApi.deleteGitHubCredential`, `apiEndpoints.githubCredential(id)` |
| `GET /repositories` | `patchApi.listRepositories`, `apiEndpoints.repositories` |
| `POST /repositories` | `patchApi.createRepository`, `apiEndpoints.repositories` |
| `DELETE /repositories/{id}` | `patchApi.deleteRepository`, `apiEndpoints.repository(id)` |
| `POST /tasks` | `patchApi.createTask`, `apiEndpoints.tasks` |
| `GET /tasks` | `patchApi.listTasks`, `apiEndpoints.tasksWithLimit(limit)` |
| `GET /tasks/{task_id}` | `patchApi.getTask`, `apiEndpoints.task(task_id)` |
| `GET /agent_runs/{id}` | `patchApi.getAgentRun`, `apiEndpoints.agentRun(id)` |
| `GET /agent_runs/{id}/events` | `patchApi.getAgentRunEvents`, `apiEndpoints.agentRunEvents(id, limit)` |
| `GET /agent_runs/{id}/pull_request` | `patchApi.getAgentRunPullRequest`, `apiEndpoints.agentRunPullRequest(id)` |
| `GET /agent_runs/{id}/diff` | `patchApi.getAgentRunDiff`, `apiEndpoints.agentRunDiff(id)` |
| `POST /agent_runs/{id}/feedback` | `patchApi.submitFeedback`, `apiEndpoints.agentRunFeedback(id)` |
| `GET /me/dashboard` | `patchApi.getDashboard`, `apiEndpoints.dashboard` |
| `WS /ws/agent_runs/{id}` | `createAgentRunWebSocket`, `apiEndpoints.agentRunWebSocket(id)` |

## Endpoint Kontrak Yang Sudah Dipakai Aktif Oleh UI

| Endpoint | Pemakaian UI |
| --- | --- |
| `POST /auth/signup` | `SignupPage` mengirim form account creation dan redirect ke `/dashboard` setelah cookie auth dibuat. |
| `POST /auth/login` | `LoginPage` mengirim email/password dan redirect ke `/dashboard` setelah cookie auth dibuat. |
| `POST /auth/logout` | `AppShell` menyediakan tombol `Log out`, memanggil `patchApi.logout`, membersihkan cache React Query, lalu redirect ke `/login`. |
| `GET /repositories` | `useRepositories` dipakai oleh `Dashboard` dan `NewTask` untuk daftar repository/picker repository. |
| `POST /repositories` | `RepositorySetup` mengirim body `{ owner, name }` lalu mengarahkan user ke flow task. |
| `POST /tasks` | `NewTask` mengirim `TaskCreate` dan mengarahkan user ke layar run. |
| `GET /tasks` | `useTasks` dipakai `Dashboard` untuk recent tasks. |
| `GET /agent_runs/{id}` | `useAgentRun` dipakai `AgentRun`, `DiffReview`, dan `PRResult` sebagai sumber run utama. |
| `GET /agent_runs/{id}/events` | `useAgentRunEvents` dipakai `AgentRun` untuk plan dan command logs. |
| `GET /agent_runs/{id}/diff` | `useAgentRunDiff` dipakai `AgentRun` dan `DiffReview` untuk changed files dan patch. |
| `POST /agent_runs/{id}/feedback` | `DiffReview` mengirim `FeedbackCreate` untuk follow-up instruction. |
| `GET /me/dashboard` | `useDashboardRead` dipakai `ScreenView`, `AppShell`, dan `Dashboard` untuk metrik workspace. |

## Alur Workflow Logout

1. User menekan tombol `Log out` di sidebar desktop atau mobile navigation.
2. UI masuk state `loading`, tombol dinonaktifkan, dan label berubah menjadi `Logging out`.
3. Frontend memanggil `patchApi.logout()`, yang mengirim `POST /auth/logout` dengan `credentials: "include"` sesuai catatan auth cookie di `api_contract.md`.
4. Backend Stream 1 membersihkan httpOnly auth cookie.
5. Frontend menerima response sukses `204` atau body kosong melalui `fetchJson` tanpa error parse JSON.
6. Setelah sukses, frontend menjalankan `queryClient.clear()` agar data session/dashboard/repository tidak tersisa di cache browser.
7. Frontend mengarahkan user ke route `/login`.
8. Jika API mengembalikan `401`, frontend tetap membersihkan cache dan redirect ke `/login` karena sesi sudah tidak valid.
9. Jika request gagal karena error lain, UI menampilkan error inline dan user dapat menekan `Log out` lagi.

## Endpoint Kontrak Yang Belum Dipakai Aktif Oleh UI

Item ini bukan "hilang" dari frontend, karena sudah ada di client. Statusnya: belum ada layar, tombol, atau hook UI yang memanggilnya secara aktif.

| Endpoint | Status di frontend saat ini | Catatan |
| --- | --- | --- |
| `GET /me` | Client ada, UI belum ada | Belum ada session bootstrap/profile fetch. |
| `POST /me/github-credentials` | Client ada, UI belum ada | Belum ada form GitHub PAT. |
| `DELETE /me/github-credentials/{id}` | Client ada, UI belum ada | Belum ada revoke credential action. |
| `DELETE /repositories/{id}` | Client ada, UI belum ada | Repository setup baru create/list, belum delete. |
| `GET /tasks/{task_id}` | Client ada, UI belum ada | UI memakai `GET /tasks` list, belum detail task by id. |
| `GET /agent_runs/{id}/pull_request` | Client ada, UI belum memanggil langsung | `PRResult` membaca `agentRun.pull_request` dari `GET /agent_runs/{id}` fallback/mock, bukan request endpoint pull request terpisah. |
| `WS /ws/agent_runs/{id}` | Helper ada, UI belum membuka socket | `AgentRun` masih memakai polling/query history via `/events`; belum live WebSocket. |

## Endpoint Yang Ada Di Frontend Tapi Tidak Ada Di API Contract

Tidak ditemukan endpoint backend tambahan yang dipanggil frontend di luar kontrak.

Yang terlihat di frontend tetapi bukan endpoint backend:

| Frontend path/string | Jenis | Catatan |
| --- | --- | --- |
| `/` | Frontend route | Route home TanStack Router. |
| `/login` | Frontend route | Route login page. |
| `/signup` | Frontend route | Route signup page. |
| `/dashboard` | Frontend route | Route dashboard UI. |
| `/repo` | Frontend route | Route repository setup UI. |
| `/task` | Frontend route | Route new task UI. |
| `/run` | Frontend route | Route agent run UI. |
| `/diff` | Frontend route | Route diff review UI. |
| `/pr` | Frontend route | Route PR result UI. |
| `/patch.svg` | Static asset | Logo, bukan API. |
| `app/routers/auth.py` dan `app/auth/routes.py` | Sample file path | Contoh path repository di mock/timeline, bukan endpoint. |

Query variant berikut dianggap sesuai kontrak, bukan endpoint tambahan:

- `/tasks?limit=${limit}` sesuai `GET /tasks` dengan query param `limit?`.
- `/agent_runs/{id}/events?limit=${limit}` sesuai `GET /agent_runs/{id}/events` dengan query param `limit?`.

## Field Schema Kontrak Yang Sudah Ada Di Type Frontend

Semua field berikut sudah direpresentasikan di `src/api-contract.ts`.

### `UserRead`

- `id`
- `email`
- `name`
- `daily_run_quota`
- `created_at`

### `RepositoryRead`

- `id`
- `github_owner`
- `github_repo`
- `default_branch`
- `language`
- `clone_url`
- `created_at`

### `TaskCreate`

- `repository_id`
- `instruction`
- `target_branch`
- `parent_run_id`
- `follow_up_instruction`

### `TaskRead`

- `id`
- `user_id`
- `repository_id`
- `title`
- `instruction`
- `target_branch`
- `created_at`
- `updated_at`

### `AgentRunRead`

- `id`
- `task_id`
- `status`
- `parent_run_id`
- `follow_up_instruction`
- `branch_name`
- `model_id`
- `prompt_version`
- `max_turns`
- `total_tool_calls`
- `total_tokens`
- `cost_usd`
- `error_message`
- `queued_at`
- `started_at`
- `finished_at`
- `tool_calls`
- `pull_request`

### `AgentRunEventRead`

- `id`
- `agent_run_id`
- `sequence`
- `event_type`
- `payload`
- `created_at`

### `ToolCallRead`

- `id`
- `agent_run_id`
- `sequence`
- `tool_name`
- `tool_input`
- `tool_output`
- `status`
- `error_message`
- `duration_ms`
- `started_at`
- `finished_at`

### `PullRequestRead`

- `id`
- `agent_run_id`
- `repository_id`
- `github_pr_number`
- `title`
- `body`
- `head_branch`
- `base_branch`
- `url`
- `state`
- `merged_at`
- `created_at`
- `updated_at`

### `DashboardRead`

- `repository_count`
- `active_run_count`
- `succeeded_run_count`
- `today_run_count`
- `daily_run_quota`

### `FeedbackCreate`

- `instruction`

### `DiffFileRead`

- `file_path`
- `status`
- `additions`
- `deletions`
- `patch`

### WebSocket Frames

- `AgentRunWebSocketFrame.type`
- `AgentRunWebSocketFrame.payload`
- `AgentRunWebSocketFrame.sequence`
- `TerminalWebSocketFrame.type`
- `TerminalWebSocketFrame.status`
- `TerminalWebSocketFrame.pr_url`
- `TerminalWebSocketFrame.pr_number`

## Field Kontrak Yang Ada Di Type Tetapi Belum Banyak Dipakai UI

Field berikut sudah ada di type/mock, tetapi belum punya rendering atau flow UI yang jelas.

| Schema | Field belum aktif di UI |
| --- | --- |
| `UserRead` | `id`, `name`, `daily_run_quota`, `created_at` |
| `RepositoryRead` | `clone_url`, `created_at` |
| `TaskCreate` | `parent_run_id`, `follow_up_instruction` |
| `TaskRead` | `user_id`, `created_at`, `updated_at` |
| `AgentRunRead` | `parent_run_id`, `follow_up_instruction`, `prompt_version`, `max_turns`, `total_tool_calls`, `total_tokens`, `cost_usd`, `error_message`, `queued_at`, `started_at`, `finished_at`, `tool_calls` |
| `AgentRunEventRead` | `id`, `sequence`, `created_at` |
| `ToolCallRead` | Hampir semua field baru dipakai sebagai type/mock, belum sebagai timeline utama. UI saat ini lebih banyak membaca `AgentRunEventRead.payload`. |
| `PullRequestRead` | `id`, `agent_run_id`, `repository_id`, `title`, `body`, `merged_at`, `created_at`, `updated_at` |
| `DiffFileRead` | `status` |
| `AgentRunWebSocketFrame` | Semua field belum aktif di UI karena WebSocket belum dibuka oleh component. |
| `TerminalWebSocketFrame` | Semua field belum aktif di UI karena WebSocket belum dibuka oleh component. |
| `ApiErrorResponse` | `detail`, `loc`, `msg`, `type` baru dipakai lewat `ApiClientError.message`; UI belum merender detail validasi per-field dari backend. |

## Field/Variabel Frontend Yang Tidak Ada Di API Contract

Item di bawah ini ada di frontend, tetapi bukan schema field kontrak backend.

### API Client/Internal Config

- `apiBaseUrl`
- `wsBaseUrl`
- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`
- `ApiClientError`
- `getApiErrorMessage`
- `fetchJson`
- `patchApi`
- `apiEndpoints`

Catatan: ini adalah helper frontend, bukan field backend.

### Request Body Stream Lain Yang Tidak Dirinci Di Schema Section

| Variabel frontend | Lokasi/pemakaian | Catatan |
| --- | --- | --- |
| `password` | `patchApi.signup`, `patchApi.login`, `LoginPage`, `SignUpPage` | Endpoint auth ada di kontrak, tetapi request body login/signup tidak dirinci di schema section. |
| `confirmPassword` | `SignUpPage` | Field validasi UI lokal, tidak dikirim ke backend. |
| `token` | `patchApi.createGitHubCredential` | Endpoint GitHub credential ada di kontrak, tetapi body PAT tidak dirinci di schema section. |
| `owner` | `patchApi.createRepository`, `RepositorySetup` | Disebut di kontrak sebagai body `{ owner, name }`, tetapi bukan schema formal seperti `RepositoryCreate`. |
| `name` | `patchApi.signup`, `SignUpPage`, `patchApi.createRepository`, `RepositorySetup` | `UserRead.name` ada di kontrak; `name` untuk repository body hanya disebut di catatan Stream 2. |

### Frontend Routing/UI State

- `screens`
- `ScreenId`
- `SetActive`
- `screenRoutes`
- `ScreenRoutePath`
- `SetActiveProps`
- `screenMeta`
- `active`
- `initialScreen`
- `navigateToScreen`
- `LoginState`
- `AuthFlowState`
- `SignupField`
- `SignupFieldErrors`
- `SubmitState`
- `showPassword`
- `rememberWorkspace`
- `loginState`
- `signupState`
- `submitState`
- `logoutState`
- `logoutError`
- `isLoggingOut`
- `fieldErrors`
- `submitError`
- `errorMessage`
- `primaryRepository`
- `primaryTask`
- `primaryRun`
- `primaryRepositoryLabel`
- `selectedRepository`

### Mock Data Dan Hooks Frontend

- `repositoryRows`
- `taskRows`
- `pullRequestRow`
- `agentRunRows`
- `agentRunEventRows`
- `diffFileRows`
- `dashboardRead`
- `repositoryLabel`
- `formatDashboardUsage`
- `findRepository`
- `useDashboardRead`
- `useRepositories`
- `useTasks`
- `useAgentRun`
- `useAgentRunEvents`
- `useAgentRunDiff`
- `statusSteps`

### UI Component Props

- `SectionHeadingProps`
- `StatusLineProps`
- `FieldProps`
- `FileRowProps`
- `MetricProps`
- `RouteStepProps`
- `MiniMeterProps`
- `LogoutButtonProps`
- `FormFieldProps`
- `AuthSubmitButtonProps`
- `AuthWorkspacePreviewProps`
- `AuthSignal`
- `ChatBubbleProps`
- `HomeRunStepProps`
- `OutcomeCheckProps`
- `ToolCallProps`
- `JourneyItemProps`
- `HomeSidebarSectionProps`
- `label`
- `value`
- `tone`
- `icon`
- `secure`
- `path`

Catatan khusus: `FileRow.path` adalah prop presentasi UI. Di kontrak backend, field diff bernama `file_path`, bukan `path`.

## Event Payload Keys

Kontrak mendefinisikan payload event secara longgar lewat `Record<string, any>`, lalu memberi contoh key per `event_type`.

### Sudah Dipakai Frontend

- `text` untuk event `plan`
- `tool_name` untuk event `tool_result`
- `tool_output` untuk event `tool_result`

### Ada Di Mock/Type Tetapi Belum Dirender Aktif

- `old_status`
- `new_status`
- `tool_input`
- `success`
- `message`

## Kesimpulan

Secara definition-level, endpoint dan field kontrak sudah ada di frontend melalui `src/api-contract.ts`.

Gap yang masih tersisa ada pada consumption-level:

1. UI sudah aktif memakai auth signup/login/logout, dashboard summary, repository list/create, task list/create, agent run read, event history, diff, dan feedback.
2. UI belum memakai beberapa endpoint yang sudah disediakan client, terutama current user, GitHub credential, delete repository, task detail, pull request lookup terpisah, dan WebSocket live run.
3. Banyak field response sudah typed tetapi belum dirender, terutama metadata run, timestamps, usage detail user, error details, dan WebSocket terminal frame.
4. Variabel frontend-only cukup banyak, tetapi mayoritas adalah routing, state UI, mock data, hooks, dan helper display. Itu normal dan tidak perlu masuk `api_contract.md` kecuali ingin menstandarkan contract baru untuk Stream 5 frontend.
