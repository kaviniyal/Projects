# Enterprise Knowledge Base Management System

A full-stack web application for centralized enterprise knowledge management. Built as a Phase 1 capstone project with React + FastAPI + SQLite.

## Features

### Core capabilities
- **Authentication & RBAC** — JWT-based auth with four roles: Admin, Author, Reviewer, Employee
- **Knowledge article management** — Full CRUD with rich content, summaries, tags, and categories
- **Approval workflow** — Draft → Pending → Approved/Rejected → Archived lifecycle
- **Hierarchical categories** — Categories can nest (e.g., IT Support → Networking → VPN)
- **Full-text search** — Search by keyword, category, tag, or author
- **File attachments** — Upload PDF, DOC, XLS, PPT, image files (up to 10MB each)
- **Collaboration** — Comments, 1–5 star ratings, bookmarks
- **Analytics dashboard** — Most viewed, top rated, articles per category, recent uploads

### Roles & permissions
| Role     | Permissions |
|----------|-------------|
| Admin    | Everything — users, categories, all articles, system settings |
| Author   | Create/edit own articles, submit for approval, upload attachments |
| Reviewer | View pending articles, approve or reject with comments |
| Employee | Search & read approved articles, comment, rate, bookmark |

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

Backend runs at **http://localhost:8000**. Interactive API docs at **http://localhost:8000/docs**.

### 2. Frontend setup

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000** and automatically connects to the backend.

### 3. Sign in

Open http://localhost:3000 and sign in with the default admin account:

- **Email:** `admin@example.com`
- **Password:** `admin123`

Or register a new account (you can choose any role at registration).

## Project Structure

```
kb-system/
├── frontend/                       # React 18 + Vite SPA
│   ├── src/
│   │   ├── components/             # Navbar, ArticleCard, Common (Badge, StarRating)
│   │   ├── context/                # AuthContext
│   │   ├── pages/                  # Login, Dashboard, ArticleList, ArticleDetail, etc.
│   │   ├── services/               # API service layer
│   │   ├── api.js                  # Axios instance with auth interceptors
│   │   ├── App.jsx                 # Router + auth guards
│   │   ├── main.jsx                # Entry point
│   │   └── styles.css              # Global styles + design tokens
│   └── package.json
│
├── backend/                        # FastAPI REST API
│   ├── routers/                    # Endpoint groups
│   │   ├── auth_router.py          # /auth/* (register, login, /me, reset)
│   │   ├── users_router.py         # /users/* (admin)
│   │   ├── categories_router.py    # /categories/*
│   │   ├── tags_router.py          # /tags/*
│   │   ├── articles_router.py      # /articles/* (CRUD, workflow, attachments)
│   │   └── analytics_router.py     # /analytics/*
│   ├── uploads/                    # File attachments (created at runtime)
│   ├── main.py                     # FastAPI app entry point
│   ├── models.py                   # SQLAlchemy ORM models
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── database.py                 # DB connection
│   ├── auth.py                     # JWT + bcrypt
│   ├── seed.py                     # Default roles, admin, categories
│   └── requirements.txt
│
├── database/
│   └── schema.sql                  # Reference SQL schema
├── docs/
│   ├── API.md                      # Endpoint reference
│   ├── SETUP.md                    # Full setup walkthrough
│   └── ARCHITECTURE.md             # System design overview
├── screenshots/                    # Screenshots placeholder
└── README.md
```

## Tech Stack

**Frontend:** React 18, Vite, React Router 6, Axios
**Backend:** FastAPI, SQLAlchemy, Pydantic, JWT (python-jose), bcrypt
**Database:** SQLite (easy switch to PostgreSQL/MySQL)

## API Reference

All endpoints (except `/auth/login` and `/auth/register`) require a JWT bearer token via the `Authorization: Bearer <token>` header.

Full reference: see [docs/API.md](docs/API.md).

| Group        | Endpoint                              | Method | Description                |
|--------------|---------------------------------------|--------|----------------------------|
| Auth         | `/auth/register`                      | POST   | Create account             |
| Auth         | `/auth/login`                         | POST   | Get JWT token              |
| Auth         | `/auth/me`                            | GET    | Current user profile       |
| Articles     | `/articles`                           | GET    | List articles              |
| Articles     | `/articles`                           | POST   | Create article (Author)    |
| Articles     | `/articles/{id}`                      | GET    | Get one article            |
| Articles     | `/articles/{id}`                      | PUT    | Update article             |
| Articles     | `/articles/{id}/submit`               | POST   | Submit for approval        |
| Articles     | `/articles/{id}/review`               | POST   | Approve/reject (Reviewer)  |
| Articles     | `/articles/{id}/archive`              | POST   | Archive (Admin)            |
| Articles     | `/articles/search`                    | GET    | Full-text search           |
| Articles     | `/articles/{id}/attachments`          | POST   | Upload file                |
| Articles     | `/articles/{id}/comments`             | POST   | Add comment                |
| Articles     | `/articles/{id}/rate`                 | POST   | Rate 1-5                   |
| Articles     | `/articles/{id}/bookmark`             | POST   | Bookmark                   |
| Categories   | `/categories`                         | GET    | List categories            |
| Users        | `/users`                              | GET    | List users (Admin)         |
| Analytics    | `/analytics/dashboard`                | GET    | Dashboard stats            |
| Analytics    | `/analytics`                          | GET    | Full analytics             |

## Default Data

On first startup, the system creates:
- **4 roles**: Admin, Author, Reviewer, Employee
- **6 categories**: HR Policies, IT Support, Infrastructure, Training Materials, Finance, Operations
- **1 admin user**: `admin@example.com` / `admin123`

## Configuration

### Backend environment variables

| Variable      | Default                          | Purpose                  |
|---------------|----------------------------------|--------------------------|
| `SECRET_KEY`  | (built-in dev key)               | JWT signing key — **change in production** |

### Frontend environment

To point the frontend at a different backend URL, create `frontend/.env`:

```
VITE_API_URL=http://localhost:8000
```

## Testing

The backend has been verified with 64+ end-to-end tests covering:
- Authentication and JWT validation
- RBAC enforcement across all four roles
- Full article approval workflow
- Search, filtering, and sorting
- Comments, ratings (with re-rating), and bookmarks
- File upload validation (type and size)
- Analytics aggregation

Visit http://localhost:8000/docs for the interactive Swagger UI to test endpoints manually.

## Phase 1 Scope

**Included:** auth, RBAC, articles, approval workflow, categories, tags, attachments, search, comments, ratings, bookmarks, analytics.

**Excluded (future phases):** AI suggestions, semantic search, mobile app, multi-language, real-time collaborative editing, Slack/Teams integration, OCR.

## License

This is a capstone project for educational purposes.
