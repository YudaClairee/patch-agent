# P.A.T.C.H. Agent

Web-based AI coding agent project. This repository is a monorepo managed with [Moonrepo](https://moonrepo.dev/), containing a FastAPI backend and a React (TanStack Start) frontend.

## 📋 Prerequisites

Pastikan Anda sudah menginstall tools berikut di komputer lokal Anda:

1. **[Git](https://git-scm.com/)**
2. **[Docker & Docker Compose](https://www.docker.com/)** (Untuk PostgreSQL & Redis)
3. **[Node.js](https://nodejs.org/en)** (v20+ direkomendasikan)
4. **[pnpm](https://pnpm.io/)** (Package manager untuk Frontend)
   ```bash
   npm install -g pnpm
   ```
5. **[uv](https://docs.astral.sh/uv/)** (Package manager untuk Python/Backend)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
6. **[Moon](https://moonrepo.dev/docs/install)** (Task runner untuk monorepo)
   ```bash
   npm install -g @moonrepo/cli
   # atau
   curl -fsSL https://moonrepo.dev/install/moon.sh | bash
   ```

## 🚀 Getting Started

Ikuti langkah-langkah di bawah ini untuk setup project di lokal Anda.

### 1. Clone Repository

```bash
git clone git@github.com:Hatvim/patch-agent.git
cd patch-agent
```

### 2. Setup Environment Variables

Copy template environment variable untuk backend:

```bash
cp apps/backend/.env.example apps/backend/.env
```

_(Jangan lupa isi kredensial yang dibutuhkan seperti API Keys di dalam file `.env` tersebut)._

### 3. Jalankan Infrastructure (Database & Redis)

Project ini butuh PostgreSQL dan Redis untuk berjalan. Jalankan via Docker dari root directory:

```bash
docker-compose up -d
```

### 4. Install Dependencies

Install seluruh dependency untuk frontend dan inisialisasi monorepo:

```bash
pnpm install
```

Untuk backend, install dependency menggunakan `uv`:

```bash
cd apps/backend
uv sync
cd ../..
```

### 5. Jalankan Development Server

Gunakan `moon` untuk menjalankan server di lokal. Buka dua terminal terpisah:

**Terminal 1 (Backend):**

```bash
moon run server:dev
```

**Terminal 2 (Frontend):**

```bash
moon run client:dev
```

- Frontend dapat diakses di `http://localhost:3000`
- Backend API dapat diakses di `http://localhost:8000`

---

## 🛠 Common Development Commands

Berikut adalah command yang berguna selama proses development. Semua command dijalankan dari root directory menggunakan Moon.

### Frontend (React / Biome)

- `moon run client:lint` — Menjalankan linter
- `moon run client:format` — Melakukan formatting kode
- `moon run client:typecheck` — Mengecek TypeScript error

### Backend (FastAPI / Ruff)

- `moon run server:lint` — Mengecek error kode Python
- `moon run server:format` — Melakukan formatting kode Python

## 💡 Aturan Kolaborasi (Workflow)

1. Selalu buat _branch_ baru dari `main` untuk setiap fitur/bugfix: `git checkout -b feature/nama-fitur`.
2. Pastikan tidak ada _error_ linter (baik Frontend maupun Backend) sebelum melakukan `git commit`.
3. Setelah selesai, `push` branch Anda dan buka _Pull Request_ di GitHub untuk di-review.
