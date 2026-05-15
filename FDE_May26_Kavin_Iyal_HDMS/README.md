# Helpdesk Ticket Management System

A full-stack web application for managing internal IT support tickets. Phase 1 of a capstone project, built with **React** (frontend), **FastAPI** (backend), and **SQLite** (database).

## Overview

Modern organizations rely on internal IT support teams to resolve employee technical issues such as VPN failures, software installations, password resets, and hardware problems. This system replaces manual handling via email and spreadsheets with a centralized, searchable ticket management platform.

## Features

- **Dashboard** — at-a-glance ticket counts by status and priority, plus recent tickets
- **Create tickets** — employees can raise support requests with category and priority
- **View & manage tickets** — complete CRUD operations on tickets
- **Update tickets** — support admins can change status, priority, and add resolution notes
- **Search & filter** — find tickets by keyword, status, category, or priority
- **REST API** — clean FastAPI implementation with automatic OpenAPI docs
- **Responsive UI** — works on desktop, tablet, and mobile

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, React Router, Axios, Vite |
| Backend | FastAPI, Pydantic, SQLAlchemy |
| Database | SQLite (PostgreSQL-ready) |
| Build | Vite (frontend), Uvicorn (backend) |

## Project Structure

```
project-root/
│
├── frontend/                  # React application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route-level pages
│   │   ├── services/          # API service layer
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/                   # FastAPI application
│   ├── routers/
│   │   └── tickets.py         # Ticket endpoints
│   ├── services/              # Reserved for future business logic
│   ├── main.py                # App entry point
│   ├── database.py            # SQLAlchemy setup
│   ├── models.py              # ORM models
│   ├── schemas.py             # Pydantic schemas
│   ├── crud.py                # DB operations
│   └── requirements.txt
│
├── database/
│   └── schema.sql             # SQL schema reference
│
├── screenshots/               # Application screenshots
├── docs/                      # API documentation
├── README.md
├── requirements.txt
└── .gitignore
```

## Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- Git (recommended)

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd project-root
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
python main.py
# or:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API is now running at **http://localhost:8000**.
Interactive API docs are at **http://localhost:8000/docs**.

The SQLite database file `helpdesk.db` is created automatically on first run.

### 3. Frontend setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend is now running at **http://localhost:3000** and will automatically open in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root health check |
| GET | `/health` | Health check |
| GET | `/tickets` | List all tickets (with optional filters) |
| GET | `/tickets/summary` | Get aggregate ticket statistics |
| GET | `/tickets/{id}` | Get a single ticket by ID |
| POST | `/tickets` | Create a new ticket |
| PUT | `/tickets/{id}` | Update a ticket (partial updates supported) |
| DELETE | `/tickets/{id}` | Delete a ticket |
| GET | `/search` | Search tickets by keyword and filters |

Full interactive documentation: `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

See [`docs/API.md`](docs/API.md) for detailed request/response examples.

## Database Schema

The `tickets` table:

| Column | Type | Description |
|---|---|---|
| ticket_id | Integer (PK) | Auto-incrementing ID |
| employee_name | String(100) | Employee who raised the ticket |
| department | String(100) | Department of the employee |
| issue_category | String(100) | Type of issue (VPN, Password Reset, etc.) |
| description | Text | Detailed description |
| priority | String(20) | Low / Medium / High / Critical |
| status | String(20) | Open / In Progress / Resolved / Closed |
| resolution_notes | Text | Notes added during resolution |
| created_at | DateTime | Ticket creation timestamp |
| updated_at | DateTime | Last modification timestamp |

See [`database/schema.sql`](database/schema.sql) for the full schema.

## Ticket Categories

- VPN Issue
- Password Reset
- Software Installation
- Laptop Issue
- Email Access
- Network Connectivity
- Hardware Request

## Priority Levels

Low · Medium · High · Critical

## Status Values

Open · In Progress · Resolved · Closed

## Switching to PostgreSQL

The application uses SQLite by default. To switch to PostgreSQL:

1. Install the Postgres driver: `pip install psycopg2-binary`
2. In `backend/database.py`, change the connection URL:
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/helpdesk_db"
   ```
3. Remove the `connect_args={"check_same_thread": False}` argument (SQLite-only).
4. Create the database manually: `createdb helpdesk_db`

## Testing the API with curl

```bash
# Create a ticket
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "employee_name": "John Doe",
    "department": "Engineering",
    "issue_category": "VPN Issue",
    "description": "Cannot connect to VPN from home",
    "priority": "High"
  }'

# List tickets
curl http://localhost:8000/tickets

# Search
curl "http://localhost:8000/search?keyword=VPN&status=Open"

# Update a ticket
curl -X PUT http://localhost:8000/tickets/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "In Progress", "resolution_notes": "Investigating"}'

# Delete a ticket
curl -X DELETE http://localhost:8000/tickets/1
```

## Out of Scope for Phase 1

These features are intentionally deferred to future phases:

- Authentication and authorization
- Email notifications
- AI / ML integrations
- Analytics dashboards
- Semantic / RAG search
- Cloud deployment

## Future Enhancements

The architecture supports:
- Data engineering pipelines on top of the tickets database
- Analytics dashboards
- AI-powered semantic search (e.g., embedding the `description` column)
- RAG-based enterprise support assistant

## License

This project is part of a capstone exercise and is provided as-is for educational purposes.
