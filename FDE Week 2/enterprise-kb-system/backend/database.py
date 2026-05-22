"""
Database configuration for the Enterprise Knowledge Base Management System.

Uses SQLAlchemy ORM with SQLite as the default database.
The connection string can be swapped for PostgreSQL or MySQL without
changing application code.

Phase 2 note: The DB path is resolved relative to this file so that the
backend server and the ETL pipeline always point to the same database,
regardless of the current working directory.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Absolute path to the DB file — always co-located with this module.
_DB_PATH = Path(__file__).parent / "knowledge_base.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
