# P.A.T.C.H. Agent

Web-based AI coding agent. Connect a GitHub repository, describe a change in plain English, and watch the agent live-stream its reasoning, run shell commands inside a sandboxed container, edit files via unified diffs, and open a pull request for you.

This repository is a Moonrepo-managed monorepo with:

- **`apps/backend`** — FastAPI + SQLModel API, Celery worker that dispatches agent containers, agno-powered ReAct agent with a Codex-style 4-tool surface (`exec_command`, `write_stdin`, `patch_file`, `submit_pull_request`).
- **`apps/frontend`** — React + TanStack Start SPA. Repository picker, run history, and a live agent-run screen wired to a WebSocket event stream.
- **Infra** — PostgreSQL, Valkey (Redis-compatible), and a dedicated Docker image (`patch/agent:latest`) the worker spawns per run.

## 📋 Prerequisites

Install these on your machine:

1. **[Git](https://git-scm.com/)**
2. **[Docker & Docker Compose](https://www.docker.com/)** — runs Postgres, Valkey, and the agent sandbox containers spawned by Celery.
3. **[Node.js](https://nodejs.org/en)** v20+
4. **[pnpm](https://pnpm.io/)** — frontend package manager (`npm install -g pnpm`)
5. **[uv](https://docs.astral.sh/uv/)** — backend Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
6. **[Moon](https://moonrepo.dev/docs/install)** — monorepo task runner (`npm install -g @moonrepo/cli`)

## 🚀 Getting Started

### 1. Clone

```bash
git clone git@github.com:Hatvim/patch-agent.git
cd patch-agent
```

### 2. Configure environment

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env   # optional; defaults work for local dev
```

You **must** fill in at least:

- `LLM_MODEL_ID` + `LLM_API_KEY` — any LiteLLM-supported provider works (OpenAI, Anthropic, OpenRouter, Gemini, Groq, …). The `LLM_MODEL_ID` prefix selects the provider; `LLM_BASE_URL` is only needed for proxies like OpenRouter.
- `FERNET_KEY` — encrypts stored GitHub tokens. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
- `JWT_SECRET` — signs session cookies. Generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"`.
- `GITHUB_OAUTH_CLIENT_ID` / `GITHUB_OAUTH_CLIENT_SECRET` — create a GitHub OAuth App at <https://github.com/settings/developers> with callback `http://localhost:8000/auth/github/callback`.
- `LANGFUSE_*` (optional) — enables OpenTelemetry tracing of every LLM call and tool use.

### 3. Start Postgres + Valkey

```bash
docker compose up -d postgres valkey
```

Data persists under `./.data/` (gitignored).

### 4. Build the agent sandbox image

The Celery worker spawns one `patch/agent:latest` container per agent run. Build it once (and any time `apps/backend/Dockerfile.agent` or backend source changes):

```bash
docker build -f apps/backend/Dockerfile.agent -t patch/agent:latest apps/backend
```

### 5. Install dependencies

```bash
pnpm install                  # frontend workspaces
(cd apps/backend && uv sync)  # backend
```

### 6. Run database migrations

```bash
cd apps/backend
uv run alembic upgrade head
cd ../..
```

### 7. Start the dev stack

You need **three** processes running locally. Open three terminals:

**Terminal 1 — API server:**

```bash
moon run server:dev
```

**Terminal 2 — Celery worker** (dispatches agent containers; needs Docker socket access):

```bash
cd apps/backend
uv run celery -A src.celery_app worker --loglevel=info --concurrency=2 --queues=celery
```

**Terminal 3 — Frontend:**

```bash
moon run client:dev
```

Then open:

- Frontend: <http://localhost:3000>
- Backend API + docs: <http://localhost:8000/docs>

### 8. First-run flow

1. Sign up / log in (email + password, or “Continue with GitHub”).
2. Click **Connect GitHub** to authorize the OAuth app — this stores an encrypted token used to clone repos and open PRs.
3. Pick a repository, then on the repo detail screen describe the change you want and start a run.
4. Watch the live event stream; when the agent finishes, follow the PR link.

## 🐳 All-in-one with Docker Compose

If you'd rather run everything in containers (API + worker + frontend + Postgres + Valkey):

```bash
docker compose up --build
```

The compose file mounts the host Docker socket into the worker so it can spawn agent containers. Make sure you've built `patch/agent:latest` first (step 4).

## 🛠 Common Development Commands

Run from the repo root via Moon:

### Frontend (React / Biome)

- `moon run client:lint` — lint
- `moon run client:format` — format
- `moon run client:typecheck` — TypeScript check

### Backend (FastAPI / Ruff / Pytest)

- `moon run server:lint` — Ruff lint
- `moon run server:format` — Ruff format
- `(cd apps/backend && uv run pytest)` — run tests

### Database

- `(cd apps/backend && uv run alembic revision --autogenerate -m "msg")` — create a migration
- `(cd apps/backend && uv run alembic upgrade head)` — apply migrations

## 💡 Workflow

1. Branch from `main`: `git checkout -b feature/short-name`.
2. Make sure lint, typecheck, and tests pass before committing.
3. Push and open a PR for review.
