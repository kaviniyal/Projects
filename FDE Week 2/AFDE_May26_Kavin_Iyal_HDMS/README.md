# Helpdesk Ticket Management System

A full-stack IT support ticket management application extended with an ETL analytics pipeline.

- **Phase 1** — Ticket CRUD (create, view, filter, search, update, delete)
- **Phase 2** — ETL pipeline + analytics dashboards powered by historical ticket data

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Recharts, React Router v6, Axios, Vite |
| Backend | FastAPI 0.115, SQLAlchemy 2, Pydantic 2, Uvicorn |
| ETL | Python, Pandas 2.2 |
| Databases | SQLite (`helpdesk.db` live, `analytics.db` reporting) |

---

## Project Structure

```
Helpdesk-System/
├── datasets/
│   ├── generate_dataset.py        # Script to generate sample CSV
│   └── tickets_historical.csv    # 270 rows (250 base + 20 duplicates)
│
├── etl/
│   └── etl_pipeline.py            # Extract -> Transform -> Load script
│
├── backend/
│   ├── main.py                    # FastAPI app (tickets + analytics routers)
│   ├── database.py                # Live DB (helpdesk.db) setup
│   ├── analytics_db.py            # Analytics DB (analytics.db) setup
│   ├── models.py                  # Phase 1: Ticket ORM model
│   ├── analytics_models.py        # Phase 2: ReportingTicket, ETLRun models
│   ├── crud.py                    # Phase 1: ticket CRUD operations
│   ├── analytics_crud.py          # Phase 2: analytics queries
│   ├── schemas.py                 # Pydantic schemas
│   ├── routers/
│   │   ├── tickets.py             # /tickets/* endpoints
│   │   └── analytics.py           # /analytics/* endpoints
│   ├── helpdesk.db                # Live ticket database (auto-created)
│   ├── analytics.db               # Reporting database (populated by ETL)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TicketList.jsx
│   │   │   ├── TicketDetail.jsx
│   │   │   ├── CreateTicket.jsx
│   │   │   ├── SearchTickets.jsx
│   │   │   └── Analytics.jsx      # Phase 2 analytics dashboard
│   │   ├── services/
│   │   │   ├── ticketService.js
│   │   │   └── analyticsService.js  # Phase 2 API calls
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── TicketTable.jsx
│   │   │   ├── FilterBar.jsx
│   │   │   └── Badge.jsx
│   │   ├── App.jsx
│   │   └── styles.css
│   └── package.json
│
├── database/
│   └── schema.sql
└── docs/
    ├── API.md
    ├── ARCHITECTURE.md
    └── SETUP.md
```

---

## Quick Start

### 1 - Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py          # http://localhost:8000
```

### 2 - Run ETL Pipeline

```bash
# From project root (generates analytics.db from the historical CSV)
python etl/etl_pipeline.py

# Also sync live tickets from helpdesk.db
python etl/etl_pipeline.py --sync-live

# Custom source file
python etl/etl_pipeline.py --source datasets/my_tickets.csv
```

### 3 - Frontend

```bash
cd frontend
npm install
npm run dev     # http://localhost:3000
```

---

## ETL Workflow

```
+------------------------------------------------------------------+
|                        ETL PIPELINE                              |
|                                                                  |
|  +-----------+    +----------------+    +--------------------+  |
|  |  EXTRACT  | -> |   TRANSFORM    | -> |        LOAD        |  |
|  |           |    |                |    |                    |  |
|  | Read CSV  |    | * Dedup rows   |    | INSERT OR IGNORE   |  |
|  | (270 rows)|    | * Normalize    |    | into analytics.db  |  |
|  |           |    |   categories   |    |                    |  |
|  | Optional: |    | * Title-case   |    | 250 clean records  |  |
|  | sync from |    |   priorities   |    |                    |  |
|  | live DB   |    | * Parse dates  |    | Log run in         |  |
|  +-----------+    | * Calc resol-  |    | etl_runs table     |  |
|                   |   ution days   |    +--------------------+  |
|                   | * Add month /  |                            |
|                   |   date cols    |                            |
|                   +----------------+                            |
+------------------------------------------------------------------+
```

### Extract Stage
- Reads `datasets/tickets_historical.csv` (270 rows)
- Optionally reads live tickets from `backend/helpdesk.db`

### Transform Stage

| Operation | Detail |
|---|---|
| Blank row removal | Drop rows with no employee_name or description |
| Deduplication | Remove rows with identical employee + category + description + date |
| Category normalization | Maps 15+ variants to 7 canonical categories (e.g. `"VPN"` to `"VPN Issue"`) |
| Priority normalization | Title-case + fallback to `"Medium"` for unknowns |
| Status normalization | Title-case + fallback to `"Open"` |
| Date parsing | `created_at`, `resolved_at` to datetime |
| Resolution time | `resolved_at - created_at` in days |
| Date enrichment | `created_date` (DATE), `created_month` (YYYY-MM) |

### Load Stage
- `INSERT OR IGNORE` into `reporting_tickets` - idempotent, safe to re-run
- Every run is logged in `etl_runs` (extracted, deduped, loaded counts, status)

---

## Dataset

`datasets/tickets_historical.csv` - 270 rows generated by `generate_dataset.py`

| Field | Description |
|---|---|
| `ticket_id` | Unique ID (TKT-0001 to TKT-0270) |
| `employee_name` | Full name of reporting employee |
| `department` | Engineering, Marketing, Sales, HR, Finance, Operations, Legal, Customer Support |
| `issue_category` | Raw category (may contain variants/typos before ETL) |
| `description` | Short issue description |
| `priority` | Low / Medium / High / Critical |
| `status` | Open / In Progress / Resolved / Closed |
| `resolution_notes` | Notes for resolved/closed tickets |
| `created_at` | Timestamp (2024-05-01 to 2025-05-01) |
| `resolved_at` | Timestamp for resolved/closed tickets |

**Intentional dirty data (for ETL demo):**
- 20 exact duplicate rows
- 30% of categories use non-standard names (`"VPN"`, `"pwd reset"`, `"network problem"`, etc.)

---

## Analytics API Endpoints (Phase 2)

All endpoints are prefixed with `/analytics` and served from `analytics.db`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/analytics/summary` | KPI cards (total, open, resolved, avg resolution, critical, dept count) |
| GET | `/analytics/category-distribution` | Ticket count per issue category |
| GET | `/analytics/priority-distribution` | Ticket count per priority level |
| GET | `/analytics/status-distribution` | Ticket count per status |
| GET | `/analytics/department-counts` | Ticket count per department |
| GET | `/analytics/monthly-volume` | Monthly ticket volume trend |
| GET | `/analytics/resolution-trends` | Avg resolution time per month |
| GET | `/analytics/category-by-department` | Cross-tab: category x department |
| GET | `/analytics/etl-status` | Last ETL run metadata |
| GET | `/analytics/etl-history?limit=10` | ETL run audit log |

Full Swagger UI: `http://localhost:8000/docs`

---

## Dashboard - Analytics Page

Navigate to **Analytics** in the top navbar.

| Widget | Chart Type | Data |
|---|---|---|
| KPI Cards | Stat cards | Total, open, resolved, avg resolution, critical, departments |
| Issue Category | Bar chart | Tickets per category |
| Priority Split | Donut chart | Critical / High / Medium / Low |
| Monthly Volume | Area chart | Ticket count per month |
| Resolution Trend | Line chart | Avg days to resolve + resolved count |
| Department Load | Horizontal bar | Tickets per department |
| Status Split | Pie chart | Open / In Progress / Resolved / Closed |
| Top Issues | Ranked table | Category volume with progress bars |
| ETL Status | Info panel | Last run time, records loaded, duplicates removed |

---

## Reporting Database Schema

```sql
-- Cleaned ticket records (populated by ETL)
CREATE TABLE reporting_tickets (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ticket_id     TEXT UNIQUE,
    employee_name        TEXT,
    department           TEXT,
    issue_category       TEXT,
    description          TEXT,
    priority             TEXT,
    status               TEXT,
    resolution_notes     TEXT,
    created_at           DATETIME,
    resolved_at          DATETIME,
    resolution_time_days REAL,
    created_date         DATE,
    created_month        TEXT,     -- YYYY-MM format for grouping
    source               TEXT,     -- 'csv_import' or 'live_db'
    loaded_at            DATETIME
);

-- ETL pipeline audit log
CREATE TABLE etl_runs (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at               DATETIME,
    source_file          TEXT,
    records_extracted    INTEGER,
    records_after_dedup  INTEGER,
    records_transformed  INTEGER,
    records_loaded       INTEGER,
    duplicates_removed   INTEGER,
    status               TEXT,     -- 'SUCCESS' or 'FAILED'
    error_message        TEXT
);
```

---

## Phase 1 API Endpoints (Tickets)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tickets` | List tickets (filter by status, category, priority) |
| GET | `/tickets/summary` | Live ticket stats |
| GET | `/tickets/{id}` | Single ticket detail |
| POST | `/tickets` | Create new ticket |
| PUT | `/tickets/{id}` | Update ticket |
| DELETE | `/tickets/{id}` | Delete ticket |
| GET | `/search` | Full-text + filter search |

---

## Submission Checklist

- [x] ETL implementation (Python + Pandas) - `etl/etl_pipeline.py`
- [x] Dataset (200+ tickets) - `datasets/tickets_historical.csv`
- [x] Extract stage - reads CSV / live DB
- [x] Transform stage - dedup, normalize, enrich
- [x] Load stage - analytics.db (idempotent)
- [x] Analytics APIs - `/analytics/*` (10 endpoints)
- [x] Dashboard UI - Recharts charts, KPI cards
- [x] Cleaned reporting database - `analytics.db`
- [x] README with ETL workflow explanation
- [x] `datasets/` folder with dataset files
