"""
Database configuration for the Helpdesk Ticket Management System.

Uses SQLAlchemy ORM with SQLite as the default database for Phase 1.
The connection string can be swapped for PostgreSQL without changing
any other application code.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database URL — file will be created in the project root.
# To switch to PostgreSQL, change this to:
# "postgresql://user:password@localhost/helpdesk_db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./helpdesk.db"

# `check_same_thread=False` is required only for SQLite, since FastAPI
# may use the same connection from multiple threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and ensures it is
    closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
