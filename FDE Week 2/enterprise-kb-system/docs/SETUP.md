# Setup Guide

This walkthrough covers a clean install on Windows, macOS, or Linux.

## Prerequisites

| Tool      | Version | Check                       |
|-----------|---------|-----------------------------|
| Python    | 3.10+   | `python --version`          |
| Node.js   | 18+     | `node --version`            |
| npm       | 9+      | `npm --version`             |
| Git       | any     | `git --version` (optional)  |

## Backend setup

### 1. Open a terminal and navigate to the backend folder

```bash
cd backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate it

**Windows (cmd):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```
If PowerShell blocks the script, allow it once: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`.

**macOS/Linux:**
```bash
source venv/bin/activate
```

When active, your prompt shows `(venv)`.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the server

```bash
python main.py
```

You should see:
```
✓ Default admin created — email: admin@example.com, password: admin123
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

The server auto-reloads on code changes. Visit http://localhost:8000/docs for the interactive Swagger UI.

### On first startup the server creates:
- `knowledge_base.db` — SQLite database file
- 4 roles (Admin, Author, Reviewer, Employee)
- 6 categories (HR Policies, IT Support, etc.)
- Default admin user

The database file persists across restarts. To reset, stop the server and delete `knowledge_base.db`.

## Frontend setup

### 1. In a **new** terminal (leave the backend running)

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

This takes a minute. You may see warnings about deprecated transitive packages — these are safe to ignore.

### 3. Start the dev server

```bash
npm run dev
```

You should see:
```
  VITE v5.4.x  ready in 400 ms
  ➜  Local:   http://localhost:3000/
```

Your browser should open automatically. If not, visit http://localhost:3000.

## First login

The login page appears. Use the default admin:

- **Email:** `admin@example.com`
- **Password:** `admin123`

After logging in, you'll see the dashboard.

## Production build (frontend)

To build the frontend for production:

```bash
cd frontend
npm run build
```

The output is in `frontend/dist/`. Serve it with any static file server, or behind a reverse proxy that also proxies `/api/*` to the FastAPI backend.

## Switching to a different database

The default SQLite database is great for development. To use PostgreSQL or MySQL:

1. Install the appropriate driver:
   ```bash
   pip install psycopg2-binary   # for PostgreSQL
   # or
   pip install pymysql           # for MySQL
   ```

2. Edit `backend/database.py` and change the connection string:
   ```python
   # PostgreSQL example
   SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost/kb"

   # MySQL example
   SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:pass@localhost/kb"
   ```

3. Remove the SQLite-specific `connect_args`:
   ```python
   engine = create_engine(SQLALCHEMY_DATABASE_URL)
   ```

4. Restart the backend. Tables will be created automatically.

## Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`**
Your virtual environment isn't activated. Run the activation command for your OS.

**`port 8000 already in use`**
Something else is on that port. Edit the last line of `backend/main.py` to use a different port (e.g. 8001) and update `VITE_API_URL` in the frontend.

**`CORS error in browser`**
The frontend is hitting a backend URL not in the CORS whitelist. Add it to the `allow_origins` list in `backend/main.py`.

**`Login fails with 401`**
Double-check the email (`admin@example.com`, not `admin@kb.local`) and password (`admin123`). If you've forgotten and there's no other admin, delete `knowledge_base.db` and restart the backend.

**`npm install` fails on Windows with native build errors**
Make sure you're on Node 18+ (`node --version`). Older Node versions can choke on some Vite dependencies.

**Frontend shows blank page**
Open browser DevTools (F12) and check the console for errors. The most common cause is the backend not running — confirm http://localhost:8000/health returns `{"status":"healthy"}`.
