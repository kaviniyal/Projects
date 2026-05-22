# Architecture Notes

A short overview of how the system is organized and the rationale behind the key design choices.

## High-level diagram

```
   ┌────────────────────┐         HTTP/JSON          ┌─────────────────────┐
   │                    │ ─────────────────────────► │                     │
   │   React Frontend   │                            │   FastAPI Backend   │
   │   (port 3000)      │ ◄───────────────────────── │   (port 8000)       │
   │                    │                            │                     │
   └────────────────────┘                            └──────────┬──────────┘
                                                                │ SQLAlchemy ORM
                                                                ▼
                                                       ┌─────────────────────┐
                                                       │   SQLite Database   │
                                                       │   (helpdesk.db)     │
                                                       └─────────────────────┘
```

## Backend layering

The backend follows a layered architecture so each concern lives in one file:

| Layer | File | Responsibility |
|---|---|---|
| Entry point | `main.py` | App setup, middleware, exception handlers |
| Routes | `routers/tickets.py` | HTTP endpoints, request/response handling |
| Schemas | `schemas.py` | Pydantic models for validation & serialization |
| Models | `models.py` | SQLAlchemy ORM models |
| CRUD | `crud.py` | Database operations |
| Database | `database.py` | Connection, session, and `Base` declaration |

The route handlers are intentionally thin — they validate input via Pydantic, call into `crud.py`, and serialize the result. Anything more elaborate (multi-step workflows, business rules) belongs in the `services/` directory once it's needed.

## Why two schemas per entity?

`schemas.py` defines separate `TicketCreate`, `TicketUpdate`, and `TicketResponse` schemas. This:

- Stops clients from setting server-controlled fields (`ticket_id`, `created_at`)
- Allows `TicketUpdate` to have all fields optional for true PATCH-style updates
- Keeps the response shape stable even if internal fields are added later

## Frontend layering

| Layer | File / folder | Responsibility |
|---|---|---|
| Entry point | `main.jsx`, `App.jsx` | Bootstrap, routing |
| Pages | `pages/` | One component per route |
| Components | `components/` | Reusable UI (Navbar, Badge, FilterBar, TicketTable) |
| Services | `services/ticketService.js` | All API calls |
| API client | `api.js` | Configured axios instance |
| Styles | `styles.css` | Single CSS file with design tokens |

Components never call axios directly — they go through `ticketService`. This makes it easy to add request/response transformations, retry logic, or even swap to React Query later, in one place.

## State management

Local component state (`useState`, `useEffect`) is sufficient for Phase 1. Each page fetches what it needs and owns that data. No global state library is necessary at this scale.

If the app grows (auth, shared user info, optimistic updates, caching across routes), the next step would be **React Query** (TanStack Query) — much lighter than Redux and a natural fit for server state.

## Database choice

SQLite is the default because:
- Zero setup — no separate server to install or run
- Single file — easy to back up, ship, or reset
- Plenty fast for the dataset sizes Phase 1 will see

Switching to PostgreSQL is a one-line change in `database.py` because all database access goes through SQLAlchemy. See `docs/SETUP.md` for the exact steps.

## Error handling

- **Validation errors** (422) are returned automatically by FastAPI from Pydantic. A global handler in `main.py` formats them into `{detail, errors}`.
- **Not-found errors** (404) are raised explicitly from each handler when a ticket lookup returns `None`.
- **Database errors** (500) are caught by a global SQLAlchemy exception handler, logged, and returned as a generic 500 — without leaking internal details.

On the frontend, axios responses are intercepted in `api.js` to log errors centrally, and each page catches errors at the call site to show a user-friendly message.

## CORS

The backend allows `http://localhost:3000` and `http://localhost:5173` by default — covering both Vite's default ports and the configured port-3000 dev server. In production, this list should be replaced with the actual frontend origin.

## Future-proofing

The requirements doc mentions Phase 2+ work in data engineering, analytics, semantic search, and RAG. The current schema and architecture support this with minimal friction:

- **Data pipelines** can read directly from the same SQLite/Postgres file
- **Analytics** can be added as new endpoints under `routers/analytics.py`
- **Semantic search** can sit alongside the existing keyword search — embed the `description` and `resolution_notes` columns, store vectors in a separate table or in pgvector
- **RAG assistant** can call into the existing search endpoint, then layer an LLM step on top

Nothing in Phase 1 needs to be undone to get there.
