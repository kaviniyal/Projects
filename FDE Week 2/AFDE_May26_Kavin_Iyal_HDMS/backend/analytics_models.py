"""
SQLAlchemy ORM models for the analytics / reporting database.
These tables are populated by the ETL pipeline (etl/etl_pipeline.py).
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text
from sqlalchemy.sql import func

from analytics_db import AnalyticsBase


class ReportingTicket(AnalyticsBase):
    """Cleaned, enriched ticket record loaded by the ETL pipeline."""
    __tablename__ = "reporting_tickets"

    id                   = Column(Integer, primary_key=True, index=True)
    source_ticket_id     = Column(String(50), unique=True, index=True)
    employee_name        = Column(String(100))
    department           = Column(String(100), index=True)
    issue_category       = Column(String(100), index=True)
    description          = Column(Text)
    priority             = Column(String(20), index=True)
    status               = Column(String(20), index=True)
    resolution_notes     = Column(Text)
    created_at           = Column(DateTime)
    resolved_at          = Column(DateTime, nullable=True)
    resolution_time_days = Column(Float, nullable=True)
    created_date         = Column(Date)
    created_month        = Column(String(7), index=True)   # YYYY-MM
    source               = Column(String(50), default="csv_import")
    loaded_at            = Column(DateTime, server_default=func.now())


class ETLRun(AnalyticsBase):
    """Audit log of every ETL pipeline execution."""
    __tablename__ = "etl_runs"

    id                   = Column(Integer, primary_key=True, index=True)
    run_at               = Column(DateTime, server_default=func.now())
    source_file          = Column(String(255))
    records_extracted    = Column(Integer, default=0)
    records_after_dedup  = Column(Integer, default=0)
    records_transformed  = Column(Integer, default=0)
    records_loaded       = Column(Integer, default=0)
    duplicates_removed   = Column(Integer, default=0)
    status               = Column(String(20))       # SUCCESS | FAILED
    error_message        = Column(Text, nullable=True)
