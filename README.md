# P.A.T.C.H. Agent

Web-based AI coding agent. Connect a GitHub repository, describe a change in plain English, watch the agent run inside a sandboxed container, and receive a pull request.

This repository is a Moonrepo-managed monorepo with:

- **`apps/backend`** - FastAPI + SQLModel API, Celery worker, GitHub OAuth, PostgreSQL persistence, Valkey event streaming, and an agno/LiteLLM-powered agent.
- **`apps/frontend`** - React + Vite SPA using TanStack Router, TanStack Query, Tailwind CSS, and a local `@patch/ui` package.
- **Infra** - PostgreSQL with pgvector, Valkey, and a dedicated Docker image (`patch/agent:latest`) spawned once per agent run.

For VM deployment, read [deployment.md](deployment.md).

## Prerequisites

Install these for local development:

1. [Git](https://git-scm.com/)
2. [Docker & Docker Compose](https://www.docker.com/) - runs Postgres, Valkey, and agent sandbox containers.
3. [Node.js](https://nodejs.org/en) 22.x - the Moon toolchain pins `22.12.0`.
4. [pnpm](https://pnpm.io/) 10.x - the frontend package manager.
5. [uv](https://docs.astral.sh/uv/) - backend Python package manager.
6. [Moon](https://moonrepo.dev/docs/install) - monorepo task runner.

## Local Development

### 1. Clone

```bash
git clone git@github.com:Hatvim/patch-agent.git
cd patch-agent
```

### 2. Configure Environment

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env
```

At minimum, fill these in `apps/backend/.env`:

- `LLM_MODEL_ID` and `LLM_API_KEY` - any LiteLLM-supported provider can work.
- `FERNET_KEY` - encrypts stored GitHub tokens.
- `JWT_SECRET` - signs session cookies.
- `GITHUB_OAUTH_CLIENT_ID` and `GITHUB_OAUTH_CLIENT_SECRET` - create an OAuth App at <https://github.com/settings/developers>.
- `GITHUB_OAUTH_REDIRECT_URI` - for local dev, use `http://localhost:8000/auth/github/callback`.
- `FRONTEND_URL` - for local dev, use `http://localhost:5173`.
- `CORS_ORIGINS` - include `http://localhost:5173`.

Generate local secrets:

```bash
python3 -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use the first value for `FERNET_KEY` and the second for `JWT_SECRET`.

### 3. Start Postgres and Valkey

```bash
docker compose up -d postgres valkey
```

Data persists under `./.data/`, which is gitignored.

### 4. Install Dependencies

```bash
(cd apps/frontend && pnpm install)
(cd apps/backend && uv sync)
```

### 5. Run Migrations

```bash
(cd apps/backend && uv run alembic upgrade head)
```

### 6. Build the Agent Sandbox Image

The Celery worker spawns one `patch/agent:latest` container per agent run:

```bash
docker build -f apps/backend/Dockerfile.agent -t patch/agent:latest apps/backend
```

Rebuild it whenever `apps/backend/Dockerfile.agent` or backend agent code changes.

### 7. Start the Dev Stack

Run these in separate terminals:

```bash
moon run server:dev
```

```bash
(cd apps/backend && uv run celery -A src.celery_app worker --loglevel=info --concurrency=2 --queues=celery)
```

```bash
moon run client:dev
```

Open:

- Frontend dev server: <http://localhost:5173>
- Backend health: <http://localhost:8000/health>
- Backend API reference: <http://localhost:8000/scalar>

## Docker Compose

For a containerized local stack:

```bash
docker build -f apps/backend/Dockerfile.agent -t patch/agent:latest apps/backend
docker compose build
docker compose run --rm backend uv run alembic upgrade head
docker compose up
```

The frontend image uses build-time values for:

- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`

For VM deployment, do not rely on localhost defaults. Follow [deployment.md](deployment.md).

## First Run Flow

1. Open the frontend.
2. Click `continue with github`.
3. Pick a repository from your GitHub account.
4. Describe a small change and start a run.
5. Watch the run stream.
6. Follow the PR link when the agent finishes.

GitHub OAuth is currently the only sign-in method.

## Common Commands

Frontend:

```bash
moon run client:check
moon run client:typecheck
moon run client:build
(cd apps/frontend && pnpm run format)
```

Backend:

```bash
moon run server:lint
moon run server:format
(cd apps/backend && uv run pytest)
```

Database:

```bash
(cd apps/backend && uv run alembic revision --autogenerate -m "message")
(cd apps/backend && uv run alembic upgrade head)
```

## Operational Notes

- Keep `FERNET_KEY` stable. Changing it makes existing stored GitHub tokens unreadable.
- `celery_worker` needs Docker socket access so it can spawn sandbox containers.
- The default compose file publishes Postgres and Valkey ports for local convenience. Protect those ports on a VM.
- `ENVIRONMENT=production` enables `Secure` cookies, so production login requires HTTPS.
