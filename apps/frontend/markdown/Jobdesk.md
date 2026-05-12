## Direction

P.A.T.C.H. is a pure autonomous coding agent. A user submits a task → the backend spawns a **fresh Docker container** → the agent loops (read → plan → write → test → iterate) → calls \`submit_pull_request\` → the container is destroyed.

Diff review is **post-PR**. After the PR exists, the user opens our Diff Review screen, inspects changes (fetched on demand from GitHub via Stream 4's \`/agent_runs/:id/diff\`), and can request follow-up changes via a feedback textbox. Submitting feedback hits Stream 4's \`POST /agent_runs/:id/feedback\` and spawns a child run that pushes another commit to the same PR branch.

You own the user-facing surface. Replace the wireframe mocks with real queries; build the live run feed against the WebSocket.

---

## Your task

### Goal
Working autonomous-loop UI: sign in → connect repo → submit task → watch live → review diff → request follow-up changes (or accept) → see the PR link.

### Files to create

- \`apps/frontend/src/lib/api.ts\` — typed client matching Stream 4's Pydantic schemas. Either generate from \`/openapi.json\` or hand-write types. Includes auth, repos, tasks, agent_runs, diff, feedback.

- \`apps/frontend/src/lib/ws.ts\` — \`useAgentRunStream(id)\` hook wrapping a native \`WebSocket\` against \`/ws/agent_runs/:id\`. Reconnect with backoff, surface \`{events, status, prUrl, error}\`, dispatch \`onTerminal\` callback when the server sends \`type: "terminal"\`.

- \`apps/frontend/src/sections/diff-review.tsx\` — **rebuild** (was deleted in commit \`2b1ceb5\` then re-routed in \`e402567\`). New shape:
  - Header with PR title + status badge + "View on GitHub" link.
  - File-list pane on the left, side-by-side diff on the right (\`react-diff-viewer-continued\` or similar) using data from \`GET /agent_runs/:id/diff\`.
  - Footer feedback textbox + "Request changes" button → \`POST /agent_runs/:id/feedback\` → navigate to \`/run/:newRunId\`.

- \`apps/frontend/src/sections/auth/\` — \`login.tsx\`, \`signup.tsx\`, \`connect-pat.tsx\` calling Stream 1's endpoints.

### Files to modify

- \`apps/frontend/src/sections/repository-setup.tsx\` — connect-repo form posting to Stream 2; lists current user's repos via \`useQuery\`.

- \`apps/frontend/src/sections/new-task.tsx\` — task instruction textarea + repo picker → \`POST /tasks\` → \`navigate({ to: "/run/$id", params: { id } })\`.

- \`apps/frontend/src/sections/agent-run.tsx\` — drive with \`useAgentRunStream\`. Render: status badge, live tool-call timeline, current message tail. Terminal states render PR link (\`succeeded\`) or error block (\`failed\`). The "Open Diff Review" button (line 58) should now navigate to the PR's run-scoped diff route.

- \`apps/frontend/src/sections/pr-result.tsx\` — final PR card; consider folding into \`agent-run.tsx\` terminal state. Your call.

- \`apps/frontend/src/wireframe-data.ts\` — replace mocks (\`repoRows\`, \`recentRuns\`, \`useWorkspaceSummary\`) with real \`useQuery\` calls to Stream 4. Keep the \`screens\` / \`screenRoutes\` / \`screenMeta\` constants.

- \`apps/frontend/src/routes/screen-view.tsx\` — re-import \`DiffReview\` and add the \`active === "diff"\` branch when you ship the new component.

- \`apps/frontend/src/sections/dashboard.tsx\`, \`home-page.tsx\`, \`app-shell.tsx\` — replace mock-driven content with live queries; verify nav between \`run\`, \`diff\`, \`pr\` works against real data.

### Reuses

- TanStack Router setup at \`apps/frontend/src/routes/\`.
- TanStack Query (already wired).
- \`@patch/ui\` workspace package primitives (\`Button\`, \`Card\`, \`Badge\`, \`SectionHeading\`, \`FileRow\`).
- framer-motion, lucide-react, Tailwind 4.

### Out of scope

- Inline PR comment threading (use a single feedback textbox; threaded review can come later).
- Mobile layout polish beyond what \`app-shell.tsx\` already does.
- Settings page beyond "Connect GitHub PAT".

### Verification

1. \`moon run client:check && moon run client:typecheck && moon run client:build\` clean.
2. \`pnpm run dev\` (or \`moon run client:dev\`); end-to-end happy path against a running backend.
3. WS reconnect: kill backend mid-run, restart, observe the hook re-subscribe and the timeline catch up.
4. Submit a follow-up via Diff Review → observe a new run kick off via the WS feed and another commit appear on the same PR branch.
