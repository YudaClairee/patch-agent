# Multiagent Auto-Review — Architecture & Implementation

## Overview

P.A.T.C.H. now automatically reviews every PR it opens and, when it finds critical or high-severity issues, dispatches a targeted fixer agent to correct them before the user sees the PR.

This document records what was built, why each decision was made, and how to extend the system.

---

## Problem Statement

The original single-agent architecture had one agent do everything: explore the repo, plan changes, write code, verify, and submit a PR. This produced PRs of variable quality with no automated safety net. Users had to manually review every PR and request changes via the feedback form.

---

## Solution: Auto-Review + Self-Heal Loop

```
[Developer Agent]          ← unchanged existing agent
        │
        │ PR opened (submit_pull_request succeeds)
        ▼
[Reviewer Agent]           ← new, runs in Celery worker (no Docker)
  · fetches PR diff from GitHub API
  · single LiteLLM call → structured JSON findings
  · stores findings as review_finding events
        │
        │ if critical or high findings exist
        ▼
[Fixer Agent]              ← existing developer agent, targeted instruction
  · inherits developer run's branch
  · fixes only the reported issues
  · pushes to same branch → PR auto-updates
```

Every stage streams live to the frontend via the existing WebSocket + Redis pub/sub. The "Review" tab appears on the run detail page as soon as the reviewer run is created.

---

## Key Design Decisions

### 1. Reviewer runs in the Celery worker — not in Docker

The reviewer is read-only (no file writes, no shell exec). Running it in a Docker container would add ~10–30s overhead for no security benefit. Instead, `dispatch_review_run` runs the LLM call directly in the Celery worker process via `litellm.completion()`.

### 2. Single structured LLM call, not a ReAct loop

The reviewer does not need a tool loop. It receives the full diff as context and produces one JSON object. This is faster, cheaper, and more reliable than running a full agno agent loop for what is essentially a classification task.

### 3. Fixer reuses the existing developer agent

The fix run is an `AgentRun` with `run_role=fixer` and a targeted `follow_up_instruction`. The existing `_load_run_context` + `dispatch_agent_run` pipeline handles it unchanged — it checks out the developer run's branch (via `parent_run_id → branch_name`) and pushes the fix to the same PR.

### 4. `run_role` enum, not a separate table

Adding a single `run_role` column to `agent_runs` keeps the data model simple. All three agent types (developer, reviewer, fixer) are rows in the same table, linked by `parent_run_id` and `reviewer_run_id`. Querying the run chain is a simple FK traversal.

### 5. Findings stored as events, not a separate table

Review findings are stored as `review_finding` events in `agent_run_events` (JSONB payload). This reuses the existing event streaming infrastructure — findings appear in the live WebSocket stream for free, and the frontend can query them via the same event API.

---

## New Files

| File | Purpose |
|---|---|
| `apps/backend/src/ai/reviewer.py` | Reviewer LLM system prompt and `run_review()` function |
| `apps/backend/src/services/review_dispatch.py` | `enqueue_review_run()` — thin Celery dispatch wrapper |
| `apps/backend/src/services/review_runner.py` | `dispatch_review_run` Celery task — orchestrates the full reviewer + fixer flow |
| `apps/backend/alembic/versions/d4e5f6a7b8c9_add_run_role_reviewer.py` | DB migration: adds `run_role` and `reviewer_run_id` to `agent_runs` |

---

## Modified Files

| File | Change |
|---|---|
| `apps/backend/src/models/enums.py` | Added `RunRole` enum (`developer`, `reviewer`, `fixer`); added `review_finding` to `EventType` |
| `apps/backend/src/models/agent_run.py` | Added `run_role` and `reviewer_run_id` columns |
| `apps/backend/src/schemas/agent_run.py` | Added `run_role` and `reviewer_run_id` to both read schemas |
| `apps/backend/src/core/config.py` | Added `llm_reviewer_model_id` and `auto_review_enabled` settings |
| `apps/backend/src/services/agent_runner.py` | Calls `enqueue_review_run()` after a successful developer run exits |
| `apps/backend/src/routes/agent_runs.py` | Added `GET /agent_runs/:id/review` endpoint + `ReviewRunRead` / `ReviewFindingRead` schemas |
| `apps/frontend/src/lib/api.ts` | Added `RunRole`, `ReviewFinding`, `ReviewRunRead` types; added `agentRunReview` endpoint and `getAgentRunReview` method |
| `apps/frontend/src/lib/queries.ts` | Added `useAgentRunReview` hook with polling while review is in progress |
| `apps/frontend/src/sections/run-detail.tsx` | Added "Review" tab with `ReviewTab` and `FindingCard` components |

---

## Configuration

Add to your `.env`:

```env
# Optional: use a different (e.g. more capable) model for reviewing
# Defaults to LLM_MODEL_ID if blank
LLM_REVIEWER_MODEL_ID=anthropic/claude-sonnet-4-6

# Set to false to disable auto-review globally
AUTO_REVIEW_ENABLED=true
```

**Recommended reviewer model**: A reasoning-capable model (Claude Sonnet, GPT-4o) gives better findings than a fast model. Since the reviewer makes a single call and not a multi-step loop, the cost delta is small.

---

## Database Migration

Run the migration before deploying:

```bash
cd apps/backend
alembic upgrade head
```

The migration adds:
- `run_role` column (PostgreSQL ENUM: `developer`, `reviewer`, `fixer`) with default `developer`
- `reviewer_run_id` column (nullable UUID FK → `agent_runs.id`)

Existing rows get `run_role = developer` automatically via the server default.

---

## API Reference

### `GET /agent_runs/:id/review`

Returns the review result for a developer run.

**Response** (200):
```json
{
  "reviewer_run_id": "uuid",
  "status": "succeeded",
  "findings": [
    {
      "file_path": "src/auth.py",
      "severity": "critical",
      "category": "security",
      "issue": "user_id is not validated before use in SQL query",
      "suggestion": "Add isinstance(user_id, int) check before the query"
    }
  ],
  "fix_run_id": "uuid or null"
}
```

**404** if the developer run has no reviewer run yet.

---

## Frontend: Review Tab

The "Review" tab appears on the run detail page only when the developer run has a `reviewer_run_id`. It shows:

- Reviewer run status (`running` / `succeeded` / `failed`)
- Findings grouped by severity: **CRITICAL** → **HIGH** → **MEDIUM** → **LOW**
- Each finding is collapsible: shows issue on the header row, expands to reveal category + suggestion
- A "view fix run →" button if a fixer agent was auto-dispatched

---

## Run Chain Relationships

```
AgentRun (developer)
  ├── reviewer_run_id ──► AgentRun (reviewer)
  │                           └── events: review_finding × N
  └── ◄── parent_run_id ── AgentRun (fixer)
                                └── parent_run_id points back to developer run
                                    (inherits branch via head_branch logic)
```

All three share the same `task_id`. The fixer run appears in the run list alongside the developer run.

---

## Extending the Reviewer

### Change the severity threshold for auto-fix

In `review_runner.py`:
```python
FIX_SEVERITIES = {"critical", "high"}  # change to {"critical"} for less aggressive auto-fix
```

### Use a different model for the reviewer

```env
LLM_REVIEWER_MODEL_ID=openrouter/openai/gpt-4o
```

### Disable auto-review per-run (future)

Add a `skip_review: bool` field to `TaskCreate` and propagate it to the `AgentRun` row. Check it in `dispatch_agent_run` before calling `enqueue_review_run`.

### Add a reviewer-specific step count / timeout

The reviewer currently has `max_turns=1` (it's a single LLM call). If you extend the reviewer to use a ReAct loop, set `agent_max_wall_time_sec` to a lower value (e.g., 120s) for the reviewer container.

---

## What's Next (Option B: Planner-Executor)

The next upgrade is a **Planner + Executor** architecture. The planner reads the repo and produces a structured work plan; each executor handles a focused subset of files with a smaller step budget. This solves the 40-step cap problem for large refactors.

The `run_role` enum is already extended to support this — add `planner` and `executor` values and build the Celery fan-out in `plan_runner.py` following the same pattern as `review_runner.py`.
