"""
FastAPI application entry point for the Helpdesk Ticket Management System.

Wires up:
  - the application object and metadata
  - CORS middleware (so the React frontend can call the API)
  - database table creation on startup (Phase 1 tickets + Phase 2 analytics)
  - global exception handlers
  - the tickets router (Phase 1)
  - the analytics router (Phase 2 – ETL-powered)
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import models
import analytics_models
from database import engine
from analytics_db import analytics_engine
from routers import tickets
from routers import analytics

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Create database tables on startup
# ---------------------------------------------------------------------------
# Phase 1: live helpdesk tickets
models.Base.metadata.create_all(bind=engine)
# Phase 2: analytics/reporting tables (populated by ETL pipeline)
analytics_models.AnalyticsBase.metadata.create_all(bind=analytics_engine)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Helpdesk Ticket Management System",
    description=(
        "REST API for managing internal IT support tickets. "
        "Phase 1: Ticket CRUD. Phase 2: ETL Analytics pipeline & dashboard. "
        "Built with FastAPI + SQLAlchemy + Pandas."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
# In production this should be locked down to known frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a 422 with a clean error payload when input validation fails."""
    logger.warning("Validation error for %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid input", "errors": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Convert any unhandled database error into a 500 response."""
    logger.error("Database error for %s: %s", request.url, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred"},
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    """Root endpoint — useful as a basic liveness check."""
    return {
        "message": "Helpdesk Ticket Management System API",
        "version": "2.0.0",
        "docs": "/docs",
        "status": "running",
        "phase2": "ETL Analytics available at /analytics/*",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health-check endpoint for monitoring."""
    return {"status": "healthy"}


app.include_router(tickets.router)
app.include_router(analytics.router)


# ---------------------------------------------------------------------------
# Entry point — allows running with `python main.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
