"""
FastAPI application entry point for the Enterprise Knowledge Base System.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

import models
from database import SessionLocal, engine
from routers import (
    analytics_router,
    articles_router,
    auth_router,
    categories_router,
    tags_router,
    users_router,
)
from seed import seed_all

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Run seed data (roles, admin user, default categories)
_db = SessionLocal()
try:
    seed_all(_db)
finally:
    _db.close()


# FastAPI app
app = FastAPI(
    title="Enterprise Knowledge Base Management System",
    description=(
        "Phase 1 REST API for the enterprise knowledge base. "
        "Provides authentication, RBAC, articles with approval workflow, "
        "categories, tags, file attachments, comments, ratings, bookmarks, "
        "search, and analytics."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS
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


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error for %s: %s", request.url, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid input", "errors": exc.errors()},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error for %s: %s", request.url, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred"},
    )


# Health endpoints
@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Enterprise Knowledge Base Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


# Register routers
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(categories_router.router)
app.include_router(tags_router.router)
app.include_router(articles_router.router)
app.include_router(analytics_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
