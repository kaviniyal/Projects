# Setup Guide

A step-by-step guide to running the Helpdesk Ticket Management System on a fresh machine.

## Prerequisites

Install these before starting:

- **Python 3.10 or higher** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18 or higher** — [nodejs.org/en/download](https://nodejs.org/en/download/)
- **Git** (recommended) — [git-scm.com/downloads](https://git-scm.com/downloads)

Verify your installations:

```bash
python --version       # Should show 3.10+
node --version         # Should show 18+
npm --version
```

---

## Step 1: Get the code

If you have a git repo:
```bash
git clone <your-repo-url>
cd project-root
```

Or extract the provided ZIP and `cd` into the extracted folder.

---

## Step 2: Start the backend

Open a terminal in the project root.

### 2.1 Create a virtual environment (recommended)

```bash
cd backend
python -m venv venv
```

Activate it:

- **macOS / Linux:** `source venv/bin/activate`
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
- **Windows (cmd):** `venv\Scripts\activate.bat`

You should now see `(venv)` at the start of your shell prompt.

### 2.2 Install dependencies

```bash
pip install -r requirements.txt
```

This installs FastAPI, Uvicorn, SQLAlchemy, and Pydantic.

### 2.3 Run the server

```bash
python main.py
```

You should see output similar to:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2.4 Verify it's working

Open these URLs in your browser:

- http://localhost:8000 — should show a JSON status response
- http://localhost:8000/docs — interactive API documentation
- http://localhost:8000/health — health check

Keep this terminal running. The database file `helpdesk.db` will be created automatically in the `backend/` folder.

---

## Step 3: Start the frontend

Open a **new** terminal in the project root.

### 3.1 Install dependencies

```bash
cd frontend
npm install
```

This downloads React, Vite, Axios, and React Router. The first install can take 1-2 minutes.

### 3.2 Run the dev server

```bash
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:3000/
```

The app should automatically open in your default browser at http://localhost:3000.

---

## Step 4: Try it out

1. You'll see the **Dashboard** with zero tickets.
2. Click **Create Ticket** in the navbar.
3. Fill in the form and submit.
4. You'll be redirected to the ticket detail page.
5. Try clicking **Edit** to change the status.
6. Go to **All Tickets** to see the list, or **Search** to filter.

---

## Stopping the servers

In each terminal, press `Ctrl + C` to stop the server.

To re-activate the Python virtual environment later:
```bash
cd backend
source venv/bin/activate   # macOS / Linux
# or: venv\Scripts\activate  # Windows
python main.py
```

---

## Troubleshooting

### Backend won't start: `Address already in use`
Port 8000 is occupied by another process. Either close that process or run on a different port:
```bash
uvicorn main:app --reload --port 8001
```
Then update the frontend's API URL by creating `frontend/.env`:
```
VITE_API_URL=http://localhost:8001
```

### Frontend can't reach the backend (`Network Error`)
- Confirm the backend is running at http://localhost:8000.
- Open http://localhost:8000/docs in your browser to confirm it responds.
- Check the browser console (F12 → Console) for the exact error.

### CORS errors in the browser console
The backend already allows requests from `http://localhost:3000` and `http://localhost:5173`. If you're using a different frontend URL, add it to the `allow_origins` list in `backend/main.py`.

### `ModuleNotFoundError` for fastapi / sqlalchemy / pydantic
You probably forgot to activate the virtual environment. Run `source venv/bin/activate` (or the Windows equivalent) and try again.

### Database file is corrupted or you want a fresh start
Stop the backend, delete `backend/helpdesk.db`, and restart it. SQLAlchemy will recreate the schema on the next startup.

### `npm install` fails
- Confirm Node.js is version 18 or higher: `node --version`
- Clear the npm cache: `npm cache clean --force`
- Delete `node_modules/` and try again

---

## Switching to PostgreSQL

By default, the app uses SQLite — no setup required.

To switch to PostgreSQL:

1. Install PostgreSQL and the Python driver:
   ```bash
   pip install psycopg2-binary
   ```

2. Create a database:
   ```bash
   createdb helpdesk_db
   ```

3. Edit `backend/database.py`:
   ```python
   SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost:5432/helpdesk_db"
   engine = create_engine(SQLALCHEMY_DATABASE_URL)  # Remove the connect_args line
   ```

4. Restart the backend.

---

## Production Build (for reference)

To build the frontend for production:

```bash
cd frontend
npm run build
```

The output goes to `frontend/dist/` — these are static files you can deploy to any web server (nginx, Apache, Netlify, Vercel, etc.). Make sure to set `VITE_API_URL` in `.env.production` to point to your deployed backend.

For the backend in production, do not use `--reload`. A typical command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```
