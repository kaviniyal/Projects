"""
Analytics Database – SQLAlchemy setup for the reporting/analytics store.
Separate from the live helpdesk.db so ETL data never interferes with
production operations.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANALYTICS_DB_PATH = os.path.join(BASE_DIR, "analytics.db")
ANALYTICS_DATABASE_URL = f"sqlite:///{ANALYTICS_DB_PATH}"

analytics_engine = create_engine(
    ANALYTICS_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

AnalyticsSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=analytics_engine
)

AnalyticsBase = declarative_base()


def get_analytics_db():
    db = AnalyticsSessionLocal()
    try:
        yield db
    finally:
        db.close()
