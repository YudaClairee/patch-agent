# PRD Project P.A.T.C.H.

# PRD Project P.A.T.C.H.

# **P.A.T.C.H.**

## **Programming Assistant for Tasks, Code, and Handoffs**

> **P.A.T.C.H. adalah web AI coding agent yang membantu developer mengambil task coding dari repository GitHub, mengerjakan perubahan kode di cloud workspace, menampilkan diff untuk review, dan membuat Pull Request setelah disetujui user.**
> 

---

# Product Requirements Document

# P.A.T.C.H. — Programming Assistant for Tasks, Code, and Handoffs

## 1. Document Control

| Item | Detail |
| --- | --- |
| Product Name | **P.A.T.C.H.** |
| Full Name | **Programming Assistant for Tasks, Code, and Handoffs** |
| Product Type | Web-based AI Coding Agent |
| Document Type | Product Requirements Document |
| Version | v1.0 |
| Status | MVP Planning |
| Target Delivery | 2 Weeks |
| Primary User | Developer / Student Developer |
| Main Platform | Web Application |
| Core Output | Code Diff and Pull Request |
| Main Concept | Human-in-the-loop AI coding workflow |

---

# 2. Executive Summary

**P.A.T.C.H.** adalah aplikasi web berbasis AI agent yang berfungsi sebagai **asisten programmer** untuk membantu menyelesaikan task coding dari repository GitHub.

User dapat memilih repository dan branch, menulis instruksi seperti “fix bug login”, “tambahkan unit test”, atau “upgrade dependency”, lalu P.A.T.C.H. akan membaca codebase, mencari konteks yang relevan, membuat rencana kerja, melakukan perubahan kode di cloud workspace, menjalankan verifikasi seperti test/lint, dan menampilkan hasil perubahan dalam bentuk **diff**.

Setelah user melakukan review dan approval, P.A.T.C.H. dapat membuat branch baru dan membuka **Pull Request** ke GitHub.

---

# 3. Product Vision

Visi produk:

> Membuat AI coding assistant yang tidak hanya memberi saran kode, tetapi benar-benar mampu membaca repository, memahami task, mengubah kode, menjalankan verifikasi, dan menyerahkan perubahan dalam format yang siap direview oleh developer.
> 

P.A.T.C.H. tidak dirancang untuk menggantikan programmer, tetapi menjadi **AI pair programmer** yang membantu pekerjaan kecil sampai menengah secara terstruktur, aman, dan transparan.

---

# 4. Problem Statement

Developer sering menghabiskan banyak waktu untuk task yang sebenarnya kecil tetapi tetap membutuhkan context reading, seperti:

- mencari file yang relevan,
- memahami struktur repository,
- menambahkan unit test,
- memperbaiki bug minor,
- menjalankan test,
- melihat diff,
- membuat branch,
- membuat pull request.

Chatbot AI biasa dapat memberi contoh kode, tetapi sering tidak cukup untuk workflow engineering nyata karena tidak selalu bisa membaca repository, menjalankan command, menghasilkan diff, atau membuat PR.

P.A.T.C.H. menyelesaikan masalah ini dengan menyediakan workflow:

```
Task → Codebase Understanding → Plan → Code Execution → Diff Review → Pull Request Handoff
```

---

# 5. Goals and Objectives

## 5.1 Product Goals

| ID | Goal | Success Indicator |
| --- | --- | --- |
| PG-01 | Membantu developer menyelesaikan coding task kecil | Agent dapat menghasilkan diff dari instruksi user |
| PG-02 | Membuat workflow AI coding lebih transparan | User dapat melihat plan, progress, tool call, dan diff |
| PG-03 | Mengurangi pekerjaan manual GitHub | Sistem dapat membuat branch dan Pull Request |
| PG-04 | Menjaga kontrol manusia | PR hanya dibuat setelah user approve |
| PG-05 | Menjadi final project yang layak demo | MVP selesai dalam 2 minggu dan bisa dipresentasikan end-to-end |

## 5.2 Technical Goals

| ID | Goal | Success Indicator |
| --- | --- | --- |
| TG-01 | Backend API berjalan stabil | FastAPI dapat menangani repo, task, diff, dan approval |
| TG-02 | Data tersimpan rapi | PostgreSQL + SQLModel + Alembic berjalan |
| TG-03 | Agent task tidak blocking | Celery + Redis memproses task di background |
| TG-04 | Agent dapat memakai tools | File, Git, command, dan RAG tools dapat dipanggil |
| TG-05 | Codebase bisa dicari secara semantic | ChromaDB/vector DB menyimpan embeddings codebase |
| TG-06 | Agent dapat menjalankan command aman | Code execution berjalan di workspace dengan guardrail |
| TG-07 | Agent dapat diobservasi | Langfuse mencatat trace, tool call, latency, token, dan error |

---

# 6. Target Users

## 6.1 Primary User — Developer

Developer yang ingin menyelesaikan task kecil seperti bug fix, unit test, atau refactor sederhana tanpa harus membaca seluruh codebase secara manual.

Kebutuhan utama:

- memilih repo dan branch,
- memberi instruksi coding,
- menerima diff,
- review sebelum PR,
- approve jika perubahan sudah sesuai.

## 6.2 Secondary User — Student Developer

Pelajar atau peserta bootcamp AI engineering yang ingin memahami cara membangun AI agent dengan tools, MCP, RAG, code execution, dan observability.

Kebutuhan utama:

- project yang dapat didemokan,
- arsitektur jelas,
- workflow agent mudah dijelaskan,
- menggunakan teknologi yang sudah dipelajari.

---

# 7. Product Scope

## 7.1 In Scope

| Scope | Description |
| --- | --- |
| Coding task creation | User dapat membuat instruksi coding |
| Workspace preparation | Sistem clone repo ke cloud workspace |
| Codebase indexing | Codebase di-index ke Vector DB |
| Agent planning | Agent membuat rencana sebelum mengubah kode |
| Tool usage | Agent memakai file tools, git tools, command tools, RAG tools |
| Code editing | Agent dapat mengubah file di workspace |
| Code execution | Agent menjalankan test/lint command |
| Diff review | User melihat perubahan dalam bentuk git diff |
| Human approval | User approve/reject perubahan |
| Pull Request handoff | Sistem membuat PR setelah approval |
| Observability | Langfuse mencatat agent run |
| Frontend dashboard | UI untuk repo, task, progress, diff, dan PR result |
| Deployment | Aplikasi dapat dijalankan di VM/VPS |

## 7.2 Out of Scope

| Out of Scope | Reason |
| --- | --- |
| Full browser IDE | Terlalu besar untuk MVP 2 minggu |
| Merge otomatis ke main | Risiko tinggi |
| Complex multi-repository refactor | Di luar scope MVP |
| Advanced GitHub App OAuth | Bisa diganti token/deploy key untuk MVP |
| Real-time collaborative coding | Tidak diperlukan untuk final project |
| Container sandbox production-grade | Stretch goal, bukan MVP |
| Support semua bahasa programming | MVP fokus ke repo Python/FastAPI dan React sederhana |
| Automatic production deployment | Fokus hanya sampai PR |

---

# 8. Core User Flow

## 8.1 Main Flow

```markdown
1. User membuka dashboard P.A.T.C.H.
2. User menambahkan GitHub repository.
3. User memilih repository dan branch.
4. User menulis instruksi coding.
5. Sistem membuat agent run.
6. Celery worker clone repo ke workspace.
7. Sistem melakukan indexing codebase ke Vector DB.
8. Agent membaca codebase dan mencari file relevan.
9. Agent membuat plan.
10. Agent mengubah kode.
11. Agent menjalankan test/lint.
12. Sistem menghasilkan diff.
13. User review diff.
14. User approve.
15. Sistem membuat branch dan Pull Request.
16. User menerima PR URL.
```

![patch_git_branch_pr_flow.svg](patch_git_branch_pr_flow.svg)

**Rejected Flow:**

### **1. Flow Sederhana (MVP): *Hard Reject***

Sesuai panduan awal, jika di-reject, task dianggap selesai/gagal dan workspace dihapus. User harus membuat task baru dari awal jika ingin mencoba lagi. Ini paling gampang dibuat untuk versi pertama.

### **2. Flow Ideal (Iterative Feedback): *Request Changes***

user bisa "ngobrol" lagi untuk benerin kode (seperti fitur *Request Changes* di GitHub), flownya akan berubah menjadi **looping**.

## 8.2 Failure Flow

| Scenario | Expected Behavior |
| --- | --- |
| Repo gagal di-clone | Status task menjadi failed dan error ditampilkan |
| Branch tidak ditemukan | Sistem memberi pesan branch invalid |
| Agent tidak menemukan file relevan | Agent berhenti dan menjelaskan konteks tidak cukup |
| Test gagal | Agent mencoba memperbaiki maksimal 1 kali |
| PR gagal dibuat | Sistem memberi fallback manual command / compare link |
| Command berbahaya terdeteksi | Sistem block atau minta approval |

---

# 9. Functional Requirements

## 9.1 Repository Management

### FR-01 — Add Repository

User dapat menambahkan repository GitHub.

Input:

| Field | Required | Description |
| --- | --- | --- |
| repo_url | Yes | URL repository GitHub |
| default_branch | Yes | Branch utama |
| access_token / deploy_key | Yes | Credential untuk clone/push |
| setup_command | No | Command setup dependency |
| test_command | No | Command test |
| lint_command | No | Command lint |

Acceptance Criteria:

- User dapat menyimpan repository.
- Sistem dapat memvalidasi URL repository.
- Secret/token tidak ditampilkan ulang di UI.
- Repository dapat digunakan untuk membuat agent task.

---

### FR-02 — List Repository

User dapat melihat daftar repository yang sudah ditambahkan.

Acceptance Criteria:

- Dashboard menampilkan daftar repository.
- Tiap repository menampilkan nama, URL, default branch, dan status.
- User dapat membuka detail repository.

---

## 9.2 Coding Task Management

### FR-03 — Create Coding Task

User dapat membuat task coding dengan instruksi natural language.

Contoh:

```
Tambahkan unit test untuk endpoint login.
Pastikan test dapat dijalankan dengan pytest.
Jangan ubah logic utama jika tidak perlu.
```

Acceptance Criteria:

- Sistem membuat `agent_run`.
- Status awal adalah `queued`.
- Task diproses oleh Celery worker.
- User diarahkan ke halaman detail agent run.

---

### FR-04 — Track Agent Run Status

Sistem menampilkan status agent run.

Status yang digunakan:

| Status | Meaning |
| --- | --- |
| queued | Task masuk antrean |
| preparing_workspace | Workspace sedang dibuat |
| cloning_repo | Repository sedang di-clone |
| indexing | Codebase sedang di-index |
| planning | Agent membuat rencana |
| executing | Agent mengubah kode |
| verifying | Agent menjalankan test/lint |
| review_required | Diff siap direview |
| approved | User menyetujui perubahan |
| rejected | User menolak perubahan |
| pr_created | Pull Request berhasil dibuat |
| failed | Task gagal |

Acceptance Criteria:

- Status task tersimpan di database.
- User dapat melihat status terbaru di UI.
- Status dapat dikirim melalui streaming event.

---

## 9.3 Workspace and Git

### FR-05 — Prepare Workspace

Setiap task memiliki workspace terpisah.

Format:

```
/workspaces/{agent_run_id}/repo
```

Acceptance Criteria:

- Workspace dibuat otomatis.
- Repository di-clone ke workspace.
- Branch target di-checkout.
- Agent hanya boleh bekerja di workspace tersebut.

---

### FR-06 — Generate Working Branch

Sistem membuat branch kerja untuk perubahan agent.

Format branch:

```
patch/task-{agent_run_id}
```

Contoh:

```
patch/task-102
```

Acceptance Criteria:

- Branch dibuat dari target branch.
- Perubahan tidak langsung dilakukan di `main`.
- Branch digunakan untuk commit dan PR.

---

### FR-07 — Generate Git Diff

Setelah agent selesai, sistem mengambil diff.

Acceptance Criteria:

- Sistem menampilkan daftar file berubah.
- Sistem menampilkan line added/deleted.
- Diff disimpan ke database.
- Diff dapat dibuka di halaman review.

---

### FR-08 — Create Pull Request

Setelah user approve, sistem membuat PR ke GitHub.

PR title format:

```
[P.A.T.C.H.] {Short Task Title}
```

Contoh:

```
[P.A.T.C.H.] Add unit tests for login endpoint
```

PR body format:

```
## Summary
P.A.T.C.H. added unit tests for login endpoint.

## Verification
- pytest: passed
- ruff: passed

## Changed Files
- tests/test_auth.py

## Agent Notes
Generated by P.A.T.C.H. — Programming Assistant for Tasks, Code, and Handoffs.

## Trace
Langfuse Trace ID: {trace_id}
```

Acceptance Criteria:

- PR hanya dibuat setelah approval.
- Branch berhasil di-push.
- PR URL disimpan.
- Jika PR gagal, sistem memberi fallback instruction.

---

## 9.4 Agent Planning

### FR-09 — Generate Plan Before Code Change

Agent wajib membuat plan sebelum mengubah file.

Contoh plan:

```
## P.A.T.C.H. Execution Plan

1. Inspect repository structure.
2. Search files related to authentication and login.
3. Read existing router and test files.
4. Add unit tests for login success and invalid password.
5. Run pytest.
6. Review git diff.
7. Prepare result for human review.
```

Acceptance Criteria:

- Agent tidak boleh langsung mengubah kode tanpa plan.
- Plan disimpan di database.
- Plan ditampilkan ke user.
- Plan harus ringkas, jelas, dan relevan.

---

## 9.5 Agent Tools

P.A.T.C.H. menggunakan tools agar agent bisa berinteraksi dengan codebase secara aman.

### File Tools

| Tool | Function |
| --- | --- |
| `list_files` | Melihat struktur file |
| `read_file` | Membaca isi file |
| `write_file` | Mengubah isi file |
| `search_file` | Mencari file berdasarkan nama/path |

### Git Tools

| Tool | Function |
| --- | --- |
| `git_status` | Melihat status repository |
| `git_diff` | Mengambil diff |
| `create_branch` | Membuat branch kerja |
| `commit_changes` | Commit perubahan |
| `push_branch` | Push branch ke remote |
| `create_pull_request` | Membuat PR |

### RAG Tools

| Tool | Function |
| --- | --- |
| `index_codebase` | Membuat index codebase |
| `search_code` | Mencari chunk kode relevan |
| `get_code_context` | Mengambil konteks file tertentu |

### Command Tools

| Tool | Function |
| --- | --- |
| `run_command` | Menjalankan command aman |
| `run_test` | Menjalankan test command |
| `run_lint` | Menjalankan lint command |

Acceptance Criteria:

- Semua tool call dicatat.
- Tool call terlihat di Langfuse.
- Tool hanya bekerja di workspace task.
- Tool tidak boleh membaca file rahasia.

---

# 10. RAG and Vector DB Requirements

## 10.1 Codebase Indexing

P.A.T.C.H. harus dapat meng-index codebase agar agent bisa mencari konteks secara semantic.

Process:

```
Scan files → Filter ignored files → Chunk source code → Generate embeddings → Store in Vector DB
```

Ignored paths:

```
.git/
node_modules/
.venv/
dist/
build/
.env
.env.local
*.pem
*.key
*.png
*.jpg
*.zip
```

Metadata yang disimpan:

| Metadata | Description |
| --- | --- |
| repository_id | ID repository |
| branch | Branch yang di-index |
| commit_hash | Commit hash saat indexing |
| file_path | Path file |
| language | Bahasa/file type |
| chunk_index | Nomor chunk |
| content | Isi chunk |

Acceptance Criteria:

- File rahasia tidak di-index.
- Search result menyertakan file path.
- Agent dapat mencari konteks dari Vector DB.
- Index dapat dibuat ulang jika branch berubah.

---

## 10.2 Search Code

Input:

```
{
  "query": "login endpoint password validation",
  "repository_id": "repo_123",
  "branch": "main"
}
```

Output:

```
{
  "results": [
    {
      "file_path": "app/routers/auth.py",
      "score": 0.89,
      "content": "..."
    }
  ]
}
```

Acceptance Criteria:

- Search result maksimal 5–10 chunks.
- Result relevan dengan query.
- Result tidak mengandung secret.
- Agent menggunakan search result sebagai konteks sebelum edit.

bisa menggunakan library AST-GREP : [https://ast-grep.github.io/](https://ast-grep.github.io/)

---

# 11. MCP Requirements

## 11.1 MCP Server

P.A.T.C.H. menggunakan MCP sebagai interface tools agar agent tidak mengakses sistem secara liar.

MCP tools:

| MCP Tool | Description |
| --- | --- |
| `list_files` | Menampilkan struktur repo |
| `read_file` | Membaca file |
| `write_file` | Menulis file |
| `search_code` | Mencari kode dari vector DB |
| `run_command` | Menjalankan command |
| `get_git_diff` | Mengambil diff |
| `create_pull_request` | Membuat PR setelah approval |

Acceptance Criteria:

- MCP server dapat dijalankan.
- Agent dapat consume MCP tools.
- Tool result dikembalikan dalam format terstruktur.
- Tool call dicatat di database dan Langfuse.

---

# 12. Code Execution Requirements

## 12.1 Safe Command Execution

Agent dapat menjalankan command di workspace.

Allowed command examples:

```
uv sync
uv run pytest
uv run ruff check .
pnpm install
pnpm test
npm test
git status
git diff
```

Blocked command examples:

```
sudo
rm -rf
mkfs
dd if=
chmod -R 777 /
cat .env
printenv
```

Acceptance Criteria:

- Command hanya berjalan di workspace.
- Command memiliki timeout.
- stdout, stderr, dan return code disimpan.
- Dangerous command diblokir.
- Unknown command membutuhkan approval atau ditolak.

---

# 13. Observability Requirements

P.A.T.C.H. harus terintegrasi dengan Langfuse.

Data yang dicatat:

| Data | Description |
| --- | --- |
| trace_id | ID trace agent run |
| instruction | Instruksi user |
| agent_plan | Plan agent |
| model | Model yang digunakan |
| prompt | Prompt agent |
| retrieved_context | Konteks dari Vector DB |
| tool_calls | Daftar tool call |
| command_output | Output command |
| error | Error jika ada |
| latency | Durasi proses |
| token_usage | Penggunaan token |
| final_summary | Summary hasil agent |

Acceptance Criteria:

- Setiap agent run memiliki trace ID.
- Tool call dapat dilihat di Langfuse.
- Error agent dapat ditelusuri.
- UI menyimpan trace ID untuk debugging.

---

# 14. Frontend Requirements

## 14.1 Pages

| Page | Description |
| --- | --- |
| Dashboard | Daftar repository dan agent run |
| Repository Setup | Form tambah/edit repository |
| New Task | Form membuat coding task |
| Agent Run Detail | Progress, plan, tool call, logs |
| Diff Review | Review perubahan kode |
| PR Result | Menampilkan PR URL atau fallback instruction |

---

## 14.2 Dashboard

Dashboard menampilkan:

- repository list,
- recent task list,
- status task,
- button create task,
- button add repository.

---

## 14.3 New Task Page

Form:

| Field | Description |
| --- | --- |
| Repository | Pilih repository |
| Branch | Pilih/input branch |
| Instruction | Instruksi coding |
| Setup command | Optional override |
| Test command | Optional override |
| Lint command | Optional override |

---

## 14.4 Agent Run Detail Page

Halaman ini menampilkan:

- instruction,
- current status,
- streaming progress,
- agent plan,
- tool calls,
- command logs,
- changed files,
- verification result,
- diff summary,
- approve/reject button,
- Langfuse trace ID.

---

## 14.5 Diff Review Page

Diff review harus menampilkan:

| UI Element | Description |
| --- | --- |
| Changed file list | Daftar file yang berubah |
| Diff viewer | Tampilan added/deleted lines |
| Summary card | Ringkasan perubahan |
| Verification card | Hasil test/lint |
| Approve button | Lanjut membuat PR |
| Reject button | Menolak perubahan |

---

# 15. Data Model

## 15.1 `repositories`

| Field | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| name | string | Nama repository |
| repo_url | string | URL GitHub |
| default_branch | string | Branch utama |
| setup_command | text/null | Command setup |
| test_command | text/null | Command test |
| lint_command | text/null | Command lint |
| credential_ref | string/null | Reference credential |
| created_at | datetime | Created timestamp |
| updated_at | datetime | Updated timestamp |

---

## 15.2 `agent_runs`

| Field | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| repository_id | UUID | FK repository |
| target_branch | string | Branch target |
| working_branch | string | Branch kerja |
| instruction | text | Instruksi user |
| status | string | Status task |
| plan | text/null | Plan agent |
| summary | text/null | Summary hasil |
| verification_result | json/null | Hasil test/lint |
| langfuse_trace_id | string/null | Trace ID |
| error_message | text/null | Error |
| created_at | datetime | Created timestamp |
| updated_at | datetime | Updated timestamp |

---

## 15.3 `agent_steps`

| Field | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| agent_run_id | UUID | FK agent run |
| step_type | string | status/tool_call/command/error |
| content | json/text | Payload step |
| created_at | datetime | Created timestamp |

---

## 15.4 `code_changes`

| Field | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| agent_run_id | UUID | FK agent run |
| file_path | string | File berubah |
| diff | text | Git diff |
| additions | int | Line added |
| deletions | int | Line deleted |
| created_at | datetime | Created timestamp |

---

## 15.5 `pull_requests`

| Field | Type | Description |
| --- | --- | --- |
| id | UUID | Primary key |
| agent_run_id | UUID | FK agent run |
| pr_url | string/null | URL PR |
| pr_number | int/null | Nomor PR |
| status | string | created/failed |
| error_message | text/null | Error jika gagal |
| created_at | datetime | Created timestamp |

---

# 16. API Requirements

## 16.1 Repository APIs

```
POST   /repositories
GET    /repositories
GET    /repositories/{id}
PATCH  /repositories/{id}
DELETE /repositories/{id}
```

Example request:

```
{
  "name": "FastAPI Auth App",
  "repo_url": "git@github.com:user/fastapi-auth-app.git",
  "default_branch": "main",
  "setup_command": "uv sync",
  "test_command": "uv run pytest",
  "lint_command": "uv run ruff check ."
}
```

---

## 16.2 Agent Run APIs

```
POST /agent-runs
GET  /agent-runs
GET  /agent-runs/{id}
GET  /agent-runs/{id}/events
GET  /agent-runs/{id}/diff
POST /agent-runs/{id}/approve
POST /agent-runs/{id}/reject
POST /agent-runs/{id}/create-pr
```

Example request:

```
{
  "repository_id": "repo_123",
  "target_branch": "main",
  "instruction": "Tambahkan unit test untuk endpoint login dan jalankan pytest."
}
```

Example response:

```
{
  "agent_run_id": "run_123",
  "status": "queued",
  "message": "P.A.T.C.H. agent run created successfully."
}
```

---

# 17. System Architecture

```
┌────────────────────────────┐
│        User Browser         │
│  React / TanStack Frontend  │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│          FastAPI API        │
│ REST API + Streaming Events │
└──────────────┬─────────────┘
               │
 ┌─────────────┼──────────────────────┐
 ▼             ▼                      ▼
PostgreSQL    Redis                 Langfuse
SQLModel      Celery Broker          Observability
Alembic
               │
               ▼
┌────────────────────────────┐
│        Celery Worker        │
│   P.A.T.C.H. Agent Runtime  │
└──────────────┬─────────────┘
               │
 ┌─────────────┼──────────────────────┐
 ▼             ▼                      ▼
MCP Server    ChromaDB              Workspace
Agent Tools   Vector DB              Git Clone/Edit/Test
               │
               ▼
          GitHub API
      Branch + Pull Request
```

---

# 18. Agent Workflow

```
User Task
  ↓
Prepare Workspace
  ↓
Clone Repository
  ↓
Index Codebase
  ↓
Search Relevant Code
  ↓
Create Plan
  ↓
Edit Files
  ↓
Run Test/Lint
  ↓
Generate Diff
  ↓
Human Review
  ↓
Create Pull Request
```

---

# 19. Multi-Agent Design

Untuk MVP, multi-agent dibuat secara modular.

| Agent | Responsibility |
| --- | --- |
| Orchestrator Agent | Mengatur seluruh workflow |
| Explorer Agent | Membaca struktur repository dan mencari file relevan |
| Planner Agent | Membuat execution plan |
| Coder Agent | Mengubah kode |
| Reviewer Agent | Memeriksa diff dan menjalankan verification |

Catatan: multi-agent ini tidak perlu dibuat sebagai service terpisah. Cukup sebagai module/class agar development tetap realistis.

---

# 20. Security Requirements

## 20.1 Secret Protection

Sistem tidak boleh menampilkan:

```
GitHub token
Private key
.env
API key
Password
Langfuse secret key
OpenAI/OpenRouter API key
```

## 20.2 Blocked Files

```
.env
.env.local
*.pem
*.key
id_rsa
id_ed25519
secrets.*
```

## 20.3 Approval Required

Approval wajib untuk:

- push branch,
- create Pull Request,
- destructive file operation,
- unknown shell command,
- command yang mengakses environment variable.

---

# 21. Non-Functional Requirements

## 21.1 Performance

| Requirement | Target |
| --- | --- |
| Dashboard load | < 3 seconds |
| Task creation response | < 5 seconds |
| First streaming event | < 5 seconds after worker starts |
| Repo clone timeout | 3–5 minutes |
| Command timeout | 60–180 seconds |
| Diff generation | < 10 seconds for small repo |

## 21.2 Reliability

| Requirement | Target |
| --- | --- |
| Failed task handling | Status failed + error message |
| Retry | Minimal 1 retry for transient error |
| Agent max iteration | 10–15 steps |
| PR fallback | Compare link/manual instruction |
| Workspace cleanup | Manual or scheduled cleanup |

## 21.3 Scalability

| Item | MVP Target |
| --- | --- |
| Concurrent users | 1–5 users (kalo menurutku untuk mvp better single tenant dulu aja, gausah ada auth) |
| Concurrent agent runs | 1–3 runs |
| Repo size | Small to medium |
| Worker scaling | Celery worker can be scaled |
| Vector DB | Local ChromaDB for MVP |

---

# 22. Success Metrics

| Metric | Target |
| --- | --- |
| Valid task created successfully | ≥ 95% |
| Repository clone success | ≥ 90% |
| Agent plan generated before edit | 100% |
| Diff generated for simple task | ≥ 80% |
| Verification executed when command exists | ≥ 80% |
| PR created after approval | ≥ 80% with valid credential |
| Langfuse trace coverage | ≥ 90% |
| Dangerous command blocked | 100% |
| First streaming event | < 5 seconds |

---

# 23. Timeline Development — 2 Weeks

## Week 1 — Foundation

| Day | Focus | Deliverable |
| --- | --- | --- |
| Day 1 | Project setup | Repo structure, backend, frontend, docker-compose |
| Day 2 | Backend foundation | FastAPI, SQLModel, Alembic, PostgreSQL |
| Day 3 | Repository module | CRUD repo config |
| Day 4 | Celery + Redis | Background job pipeline |
| Day 5 | Workspace + Git | Clone repo, checkout branch, git diff |
| Day 6 | Vector DB | Codebase indexing and search_code |
| Day 7 | MCP tools | File tools, git tools, command tools |

## Week 2 — Agent, UI, PR, Demo

| Day | Focus | Deliverable |
| --- | --- | --- |
| Day 8 | Agent planner | Plan generation |
| Day 9 | Agent executor | File editing and verification |
| Day 10 | Diff review | Diff API and database storage |
| Day 11 | Frontend dashboard | Repository/task UI |
| Day 12 | Streaming UI | Agent progress event |
| Day 13 | PR + Langfuse | Pull Request and observability |
| Day 14 | Deployment + demo | VM deployment and final testing |

---

# 24. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope terlalu besar | Tidak selesai 2 minggu | Fokus pada MVP small coding task |
| Agent mengubah file salah | Kode rusak | Plan + diff review + human approval |
| Retrieval tidak akurat | Patch salah | Metadata file path + search_code |
| Command berbahaya | Security issue | Command allowlist/blocklist |
| GitHub PR gagal | Demo terganggu | Fallback compare link |
| Worker stuck | Task menggantung | Timeout + failed status |
| Secret bocor | Security issue | Secret redaction |
| Multi-agent terlalu kompleks | Development lambat | Implement as modules only |
| Langfuse setup gagal | Observability kurang | Simpan local agent_steps as fallback |

---

# 25. Definition of Done

```
# P.A.T.C.H. MVP Definition of Done

- [ ] PRD selesai
- [ ] Backend FastAPI berjalan
- [ ] PostgreSQL terhubung
- [ ] SQLModel models tersedia
- [ ] Alembic migration berjalan
- [ ] Celery worker berjalan
- [ ] Redis berjalan
- [ ] Repository dapat ditambahkan
- [ ] Repository dapat di-clone
- [ ] Agent run dapat dibuat
- [ ] Workspace dibuat per task
- [ ] Codebase dapat di-index ke Vector DB
- [ ] Agent dapat menggunakan tools
- [ ] MCP server/consumer berjalan
- [ ] Agent dapat membuat plan
- [ ] Agent dapat mengubah file
- [ ] Agent dapat menjalankan test/lint
- [ ] Diff dapat ditampilkan
- [ ] User dapat approve/reject
- [ ] Pull Request dapat dibuat atau fallback tersedia
- [ ] Langfuse trace tersedia
- [ ] Frontend menampilkan streaming progress
- [ ] App dapat dideploy
- [ ] Demo end-to-end berhasil
```

---

# 26. Final Product Positioning

> **P.A.T.C.H. adalah web AI coding agent yang membantu developer menyelesaikan task coding dari repository GitHub dengan cara membaca codebase, membuat rencana perubahan, mengedit kode secara aman, menampilkan diff untuk review, dan membuat Pull Request setelah disetujui user.**
> 

## One-Line Pitch

> **P.A.T.C.H. turns natural-language coding tasks into reviewable GitHub pull requests.**
> 

# 27. Pembagian Task (Need Approval dari semua anggota)

## Orang 1 — Backend Core

- FastAPI
- SQLModel
- Alembic
- Repository CRUD
- Agent run CRUD/status

## Orang 2 — Worker, Workspace, GitHub

- Celery + Redis
- Clone repo
- Workspace management
- Git diff
- Branch
- Commit
- Push
- Create PR

## Orang 3 — Agent + Tools + Guardrail

- Agent runtime
- Planner
- File tools
- Command tools
- Policy enforcement
- Stack limitation

## Orang 4 — RAG + Langfuse

- Code indexing
- ChromaDB
- Search code
- Embeddings
- Langfuse tracing
- Agent steps logging

## Orang 5 — Frontend

- Dashboard
- Repository form
- New task
- Agent run detail
- Diff review
- Approve/reject
- PR result