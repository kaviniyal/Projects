# Architecture Overview

A 3-tier architecture: React SPA frontend, FastAPI REST backend, SQLite database. Designed to be modular and easy to swap pieces.

```
┌────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER                                            │
│  React 18 SPA (Vite) — http://localhost:3000                   │
│  React Router, Axios with auth interceptors                    │
└────────────────────────────────────────────────────────────────┘
                            ↕  REST/JSON + JWT
┌────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                             │
│  FastAPI (Python) — http://localhost:8000                      │
│  Routers · Auth (JWT) · Services · Pydantic validation         │
└────────────────────────────────────────────────────────────────┘
                            ↕  SQLAlchemy ORM
┌────────────────────────────────────────────────────────────────┐
│  DATA LAYER                                                    │
│  SQLite (default) — file: knowledge_base.db                    │
│  Easily swappable for PostgreSQL or MySQL                      │
└────────────────────────────────────────────────────────────────┘
```

## Frontend Architecture

### Folder organization

```
src/
├── components/       # Reusable, stateless UI components
├── pages/            # Top-level route components
├── context/          # React Context providers (auth)
├── services/         # API client layer
├── api.js            # Configured axios instance
├── App.jsx           # Router with auth guards
├── main.jsx          # Entry point
└── styles.css        # Global styles + design tokens
```

### State management

- **Global auth state** via React Context (`AuthContext`). Stores the current user and JWT token.
- **Local state** via `useState` and `useEffect` in each page. No Redux, no Zustand — kept intentionally simple.
- **URL state** (filters, sort) via React Router's `useSearchParams` so URLs are bookmarkable.

### Authentication flow

1. User logs in via `/auth/login` → backend returns `{ access_token, user }`.
2. Token and user object stored in `localStorage` under `kb_token` and `kb_user`.
3. Axios request interceptor automatically attaches `Authorization: Bearer <token>` to every request.
4. Axios response interceptor catches 401 → clears storage and redirects to `/login`.
5. Routes wrapped in `<ProtectedRoute>` enforce auth and (optionally) role membership.

### Route protection

```jsx
<ProtectedRoute roles={['Admin']}>
  <UserManagement />
</ProtectedRoute>
```

Without `roles`, just requires authentication. With `roles`, also enforces role membership.

## Backend Architecture

### Folder organization

```
backend/
├── routers/                 # Endpoint groups
│   ├── auth_router.py       # /auth/*
│   ├── users_router.py      # /users/*
│   ├── categories_router.py # /categories/*
│   ├── tags_router.py       # /tags/*
│   ├── articles_router.py   # /articles/* (largest)
│   └── analytics_router.py  # /analytics/*
├── uploads/                 # File attachments (runtime)
├── main.py                  # FastAPI app factory
├── models.py                # SQLAlchemy ORM
├── schemas.py               # Pydantic validation
├── database.py              # DB session + engine
├── auth.py                  # JWT + bcrypt + role dependencies
└── seed.py                  # Initial data
```

### Layers

1. **Routers** parse requests, enforce auth/roles, call domain logic, return responses.
2. **Schemas** (Pydantic) validate inputs and serialize outputs.
3. **Models** (SQLAlchemy) define the database schema and ORM relationships.
4. **Auth utilities** (`auth.py`) provide reusable dependencies for current-user and role enforcement.

### Authentication

- **Password hashing:** bcrypt (industry standard, configurable cost).
- **Token:** JWT signed with HS256. Default expiry: 8 hours.
- **Token claims:** `{ "sub": "<user_id>", "exp": <unix-ts> }`.

### Role-based access control

Implemented as FastAPI dependencies:

```python
@router.post("/articles", dependencies=[Depends(require_roles("Author", "Admin"))])
def create_article(...): ...
```

`require_roles` is a dependency factory — it returns a callable that raises 403 if the user's role isn't in the allowed list.

Permission rules embedded in business logic:
- Authors edit their own articles when in `Draft` or `Rejected` status.
- Reviewers see and decide on `Pending Approval` articles only.
- Employees see only `Approved` articles.

### Approval workflow

```
   ┌───────┐  submit   ┌──────────────────┐
   │ Draft │──────────▶│ Pending Approval │
   └───────┘           └──────────────────┘
       ▲                  │             │
       │                  │ approve     │ reject
       │ edit             ▼             ▼
       │              ┌──────────┐  ┌──────────┐
       └──────────────│ Rejected │  │ Approved │
                      └──────────┘  └──────────┘
                                          │
                                          │ archive (Admin)
                                          ▼
                                    ┌──────────┐
                                    │ Archived │
                                    └──────────┘
```

State transitions are enforced server-side. Authors can resubmit from `Rejected`.

### View tracking

Each approved-article fetch:
1. Increments `articles.view_count`.
2. Inserts a row into `article_views` (for time-series analytics).
3. Skips both if the viewer is the author.

## Data Model

10 tables. Key relationships:

```
roles ──< users ──< articles >── categories
                         ├──── attachments
                         ├──── comments
                         ├──── ratings
                         ├──── bookmarks
                         └──── article_views

articles >──< tags  (via article_tags)
categories >── categories  (self-FK for hierarchy)
```

Notes:
- `articles.author_id` and `articles.reviewer_id` both reference `users.user_id`. SQLAlchemy disambiguates via `foreign_keys=`.
- `article_tags` is a pure many-to-many join table.
- `categories.parent_id` makes categories hierarchical (self-referencing FK).
- File attachments are stored on disk under `backend/uploads/<uuid-name>`. Only the metadata lives in the DB.

## File Upload Handling

1. Client POSTs `multipart/form-data` to `/articles/{id}/attachments`.
2. Server validates extension and size (10MB cap).
3. Saves to `backend/uploads/<uuid>.<ext>` with a UUID-prefixed name to avoid collisions.
4. Inserts an `Attachment` row pointing to the on-disk file.
5. On download, the file is streamed back with the original filename.
6. On article deletion, all attachments are cascaded via `cascade="all, delete-orphan"`, and the disk files are cleaned up explicitly.

## Search Implementation

Phase 1 uses SQL `ILIKE` (case-insensitive LIKE) across `title`, `content`, and `summary`. This is enough for thousands of articles. For tens or hundreds of thousands, swap in:

- **PostgreSQL full-text search** — `tsvector` + `tsquery` with a GIN index.
- **Elasticsearch / Meilisearch** — index articles on save and search via their REST API.

The search router is isolated, so this swap doesn't touch the rest of the code.

## Performance Considerations

| Aspect          | Current approach                       | Production upgrade            |
|-----------------|----------------------------------------|--------------------------------|
| Database        | SQLite                                 | PostgreSQL/MySQL              |
| Search          | SQL ILIKE                              | Full-text index / Elasticsearch |
| File storage    | Local `uploads/`                       | S3 or equivalent              |
| Auth tokens     | JWT in localStorage                    | httpOnly secure cookies       |
| API rate limit  | None                                   | Slowapi or nginx              |
| Pagination      | offset/limit                           | Keyset pagination on large lists |

## Security

- **Passwords:** bcrypt, never stored in plaintext.
- **Tokens:** signed JWT, 8-hour expiry.
- **CORS:** configured for localhost origins; widen for production.
- **File uploads:** extension whitelist + size cap.
- **Input validation:** Pydantic schemas on every endpoint.
- **SQL injection:** SQLAlchemy ORM uses parameterized queries throughout.

**Action items for production:**
1. Set a real `SECRET_KEY` via environment variable.
2. Use HTTPS everywhere.
3. Switch to httpOnly cookies for tokens (mitigates XSS-driven token theft).
4. Restrict CORS to your real frontend domain.
5. Add rate limiting on auth endpoints.
6. Add a password-strength check and lock-out after failed attempts.

## Scalability Notes

The current design scales well to ~100k articles and ~10k concurrent users with these upgrades:
- Move to PostgreSQL with proper indexes (already defined in `models.py`).
- Move file storage to object storage (S3).
- Add Redis for caching dashboard stats and analytics.
- Add a background worker (Celery/RQ) for non-blocking tasks (email notifications, OCR indexing).
- Horizontal scale the FastAPI layer behind a load balancer — the app is stateless.
