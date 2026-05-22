# Enterprise Knowledge Base Management System
## Phase 2 — ETL Pipeline & Analytics Dashboard

A full-stack enterprise knowledge management platform with a complete ETL pipeline for bulk article ingestion, advanced analytics, and a reporting dashboard. Built with **React + FastAPI + SQLite + Pandas**.

---

## What's New in Phase 2

| Feature | Details |
|---------|---------|
| 📦 **ETL Pipeline** | Extract → Transform → Load using Python & Pandas. Ingests 120+ articles from CSV/JSON datasets. |
| 🗄️ **Dataset** | `datasets/knowledge_articles.csv` — 120 knowledge articles across 6 categories with rich metadata. |
| 📊 **Analytics Dashboard** | Comprehensive reporting: category trends, author activity, search keywords, monthly publication, tag cloud. |
| 🔍 **Search Analytics** | Every search query is logged to `search_logs` table; keyword frequency visible in the dashboard. |
| ⚙️ **ETL API** | REST endpoints to trigger pipelines, monitor job history, and regenerate CSV reports. |
| 📈 **CSV Reports** | Auto-generated reports in `datasets/reports/`: popular articles, category distribution, author activity, tags, keywords. |
| 🔗 **New DB Tables** | `search_logs` (keyword analytics) and `etl_jobs` (pipeline run history). |

---

## ETL Workflow

```
datasets/knowledge_articles.csv
            │
            ▼
   ┌─────────────────┐
   │   1. EXTRACT    │  etl/extract.py
   │  Read CSV/JSON  │  ──► Validates schema, loads raw DataFrame
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  2. TRANSFORM   │  etl/transform.py
   │  Clean & Enrich │  ──► Dedup, normalise categories & tags,
   │                 │       cast types, derive word counts
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │    3. LOAD      │  etl/load.py
   │  Upsert to DB   │  ──► Creates users/categories/tags if needed,
   │                 │       inserts new articles, updates existing
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │   4. REPORT     │  etl/reports.py
   │  Generate CSVs  │  ──► 7 analytics CSV reports → datasets/reports/
   └─────────────────┘
```

### Transformation Steps

1. **Strip whitespace** — all string columns
2. **Deduplicate** — by `id` then by `title`
3. **Drop empty rows** — title or content must be present
4. **Normalise categories** — fuzzy-mapped to the 6 canonical categories
5. **Parse tags** — comma-separated string → lowercase list
6. **Cast views** — to integer (0 on error)
7. **Parse dates** — `created_date` and `published_date` to datetime
8. **Normalise status** — mapped to Draft / Pending Approval / Approved / Rejected / Archived
9. **Derived columns** — `tag_count`, `content_word_count`, `etl_loaded_at`

### Running the ETL Pipeline

**Option A — Command line:**
```bash
# From the project root (with venv active)
cd backend
python -m etl.pipeline              # uses ./datasets/
python -m etl.pipeline --report     # also generates CSV reports
```

**Option B — Via the Admin Dashboard:**
1. Log in as Admin.
2. Navigate to **📊 Analytics → ⚙️ ETL Pipeline** tab.
3. Click **▶ Run Full ETL Pipeline**.
4. Monitor status in the Job History table.

**Option C — Via the API:**
```bash
POST /etl/run       # triggers async pipeline, returns job_id
GET  /etl/jobs      # lists recent job runs
GET  /etl/jobs/{id} # poll a specific job
POST /etl/reports   # regenerate CSV reports only
```

### Generated Reports

After running the pipeline, these CSV files appear in `datasets/reports/`:

| File | Contents |
|------|----------|
| `popular_articles.csv` | Top 20 most-viewed approved articles with ratings |
| `category_distribution.csv` | Article count and total views per category |
| `author_activity.csv` | Articles written, total views, avg rating per author |
| `tag_frequency.csv` | Top 30 most-used tags |
| `status_summary.csv` | Article count per status |
| `monthly_publication.csv` | Articles published per month (last 12 months) |
| `search_keywords.csv` | Top 30 search keywords |

---

## Phase 1 Features (retained)

- **Authentication & RBAC** — JWT with 4 roles: Admin, Author, Reviewer, Employee
- **Article management** — CRUD with approval workflow (Draft → Pending → Approved/Rejected → Archived)
- **Hierarchical categories** — Unlimited nesting
- **Full-text search** — Keyword, category, tag, author filters *(now logs keywords for analytics)*
- **File attachments** — PDF, DOC, XLS, PPT, image (up to 10 MB)
- **Collaboration** — Comments, 1–5 star ratings, bookmarks
- **Basic analytics** — Most viewed, top rated, articles per category

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm 9+

### 1. Backend setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

Backend runs at **http://localhost:8000** · Swagger UI at **http://localhost:8000/docs**

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**.

### 3. Run the ETL pipeline (optional — loads the 120 sample articles)

```bash
# With venv active, from the project root:
cd backend
python -m etl.pipeline --report
```

This imports 120 articles from `datasets/knowledge_articles.csv` and writes CSV reports to `datasets/reports/`.

### 4. Sign in

| Email | Password | Role |
|-------|----------|------|
| admin@example.com | admin123 | Admin |

Or register a new account and choose your role.

---

## Project Structure

```
enterprise-kb-system/
│
├── datasets/                          ← Phase 2: input data and reports
│   ├── knowledge_articles.csv         ← 120+ knowledge articles (ETL input)
│   └── reports/                       ← Generated CSV analytics reports
│       ├── popular_articles.csv
│       ├── category_distribution.csv
│       ├── author_activity.csv
│       ├── tag_frequency.csv
│       ├── status_summary.csv
│       ├── monthly_publication.csv
│       └── search_keywords.csv
│
├── etl/                               ← Phase 2: ETL package
│   ├── __init__.py
│   ├── extract.py                     ← Stage 1: Read CSV/JSON → DataFrame
│   ├── transform.py                   ← Stage 2: Clean & normalise data
│   ├── load.py                        ← Stage 3: Upsert into SQLite
│   ├── pipeline.py                    ← Orchestrator (runs all 3 stages)
│   └── reports.py                     ← Stage 4: Generate CSV reports
│
├── backend/                           ← FastAPI REST API
│   ├── routers/
│   │   ├── auth_router.py             ← /auth/*
│   │   ├── users_router.py            ← /users/*
│   │   ├── categories_router.py       ← /categories/*
│   │   ├── tags_router.py             ← /tags/*
│   │   ├── articles_router.py         ← /articles/* (search now logs keywords)
│   │   ├── analytics_router.py        ← /analytics/* (extended Phase 2)
│   │   └── etl_router.py              ← /etl/* (Phase 2 new)
│   ├── main.py
│   ├── models.py                      ← Added: SearchLog, ETLJob tables
│   ├── schemas.py                     ← Added: ETL + analytics schemas
│   ├── database.py
│   ├── auth.py
│   ├── seed.py
│   └── requirements.txt               ← Added: pandas, openpyxl, numpy
│
├── frontend/                          ← React 18 + Vite SPA
│   └── src/
│       ├── pages/
│       │   ├── AnalyticsDashboard.jsx ← Phase 2 new: full reporting dashboard
│       │   ├── Dashboard.jsx
│       │   └── ... (all Phase 1 pages retained)
│       ├── services/
│       │   └── apiService.js          ← Added: analyticsService (extended), etlService
│       ├── components/
│       │   └── Navbar.jsx             ← Added: Analytics link
│       └── App.jsx                    ← Added: /analytics route
│
├── database/
│   └── schema.sql
├── docs/
│   ├── API.md
│   ├── SETUP.md
│   └── ARCHITECTURE.md
├── screenshots/
└── README.md
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, React Router 6, Axios |
| Backend | FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2.9 |
| ETL | Python 3.10+, **Pandas 2.2**, openpyxl |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | SQLite (zero-config; swap to PostgreSQL with one env var) |

---

## Phase 2 API Reference

### Analytics (extended)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analytics/dashboard` | GET | Dashboard stat counters |
| `/analytics` | GET | Full Phase 2 analytics payload |
| `/analytics/category-trends` | GET | Views + article count per category |
| `/analytics/search-keywords` | GET | Top search keywords |
| `/analytics/author-activity` | GET | Per-author productivity metrics |
| `/analytics/monthly-publish` | GET | Monthly publication trend |
| `/analytics/top-tags` | GET | Most-used tags |
| `/analytics/etl-summary` | GET | Latest ETL job status |

### ETL Pipeline (Admin only)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/etl/run` | POST | Trigger a new ETL pipeline run (async) |
| `/etl/jobs` | GET | List recent ETL job runs |
| `/etl/jobs/{id}` | GET | Poll a specific job |
| `/etl/reports` | POST | Regenerate CSV reports |

---

## Database Schema (Phase 2 additions)

```sql
-- Search keyword analytics
CREATE TABLE search_logs (
    log_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword      VARCHAR(255) NOT NULL,
    user_id      INTEGER REFERENCES users(user_id),
    result_count INTEGER,
    searched_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ETL pipeline run history
CREATE TABLE etl_jobs (
    job_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    status         VARCHAR(30) DEFAULT 'queued',  -- queued|running|completed|failed
    datasets_dir   VARCHAR(500),
    started_at     DATETIME,
    finished_at    DATETIME,
    rows_extracted INTEGER DEFAULT 0,
    rows_inserted  INTEGER DEFAULT 0,
    rows_updated   INTEGER DEFAULT 0,
    rows_skipped   INTEGER DEFAULT 0,
    rows_errored   INTEGER DEFAULT 0,
    triggered_by   INTEGER REFERENCES users(user_id),
    error_message  TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Dataset

`datasets/knowledge_articles.csv` contains **120 knowledge articles** with the following fields:

| Column | Description |
|--------|-------------|
| id | Unique article identifier |
| title | Article title |
| category | One of: HR Policies, IT Support, Infrastructure, Training Materials, Finance, Operations |
| tags | Comma-separated tags (e.g., `vpn,remote-access,security`) |
| views | Historical view count |
| author_name | Full name of the author |
| author_email | Author's email address |
| author_department | Author's department |
| summary | Short description (up to 500 chars) |
| content | Full article text |
| status | Draft / Pending Approval / Approved |
| created_date | YYYY-MM-DD |
| published_date | YYYY-MM-DD (blank for drafts) |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | built-in dev key | JWT signing key — **change in production** |
| `VITE_API_URL` | `http://localhost:8000` | Frontend → backend URL |

---

## License

Capstone project — Phase 2. For educational purposes.
