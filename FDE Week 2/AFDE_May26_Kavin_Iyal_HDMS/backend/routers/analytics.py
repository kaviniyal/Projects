"""
Analytics Router – Phase 2 API endpoints.
All data is served from analytics.db (populated by the ETL pipeline).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from analytics_db import get_analytics_db
import analytics_crud

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ── Summary / KPIs ──────────────────────────────────────────────────────────

@router.get("/summary", summary="Analytics KPI summary")
def analytics_summary(db: Session = Depends(get_analytics_db)):
    """
    Returns high-level KPIs:
    - total_tickets, resolved_tickets, open_tickets
    - avg_resolution_days, critical_tickets
    - departments_tracked, resolution_rate_pct
    """
    return analytics_crud.get_analytics_summary(db)


# ── Category Distribution ────────────────────────────────────────────────────

@router.get("/category-distribution", summary="Tickets per issue category")
def category_distribution(db: Session = Depends(get_analytics_db)):
    """
    Returns ticket counts grouped by issue category, sorted by volume.
    Use for bar charts or ranked lists.
    """
    data = analytics_crud.get_category_distribution(db)
    if not data:
        raise HTTPException(status_code=404, detail="No analytics data found. Run the ETL pipeline first.")
    return data


# ── Priority Distribution ────────────────────────────────────────────────────

@router.get("/priority-distribution", summary="Tickets per priority level")
def priority_distribution(db: Session = Depends(get_analytics_db)):
    """
    Returns ticket counts grouped by priority (Critical → Low).
    Use for pie/donut charts.
    """
    data = analytics_crud.get_priority_distribution(db)
    if not data:
        raise HTTPException(status_code=404, detail="No analytics data found. Run the ETL pipeline first.")
    return data


# ── Status Distribution ──────────────────────────────────────────────────────

@router.get("/status-distribution", summary="Tickets per status")
def status_distribution(db: Session = Depends(get_analytics_db)):
    """Returns ticket counts grouped by status."""
    return analytics_crud.get_status_distribution(db)


# ── Department Counts ────────────────────────────────────────────────────────

@router.get("/department-counts", summary="Tickets per department")
def department_counts(db: Session = Depends(get_analytics_db)):
    """
    Returns total ticket counts per department, sorted descending.
    Use for horizontal bar chart.
    """
    data = analytics_crud.get_department_counts(db)
    if not data:
        raise HTTPException(status_code=404, detail="No analytics data found. Run the ETL pipeline first.")
    return data


# ── Monthly Volume Trend ─────────────────────────────────────────────────────

@router.get("/monthly-volume", summary="Monthly ticket volume trend")
def monthly_volume(db: Session = Depends(get_analytics_db)):
    """
    Returns ticket count per month (YYYY-MM), sorted chronologically.
    Use for line/area charts.
    """
    data = analytics_crud.get_monthly_volume(db)
    if not data:
        raise HTTPException(status_code=404, detail="No analytics data found. Run the ETL pipeline first.")
    return data


# ── Resolution Time Trend ────────────────────────────────────────────────────

@router.get("/resolution-trends", summary="Average resolution time per month")
def resolution_trends(db: Session = Depends(get_analytics_db)):
    """
    Returns average resolution time (days) per month for resolved tickets.
    Use for trend line charts.
    """
    data = analytics_crud.get_resolution_trends(db)
    if not data:
        raise HTTPException(status_code=404, detail="No resolution data found. Run the ETL pipeline first.")
    return data


# ── Category × Department Breakdown ─────────────────────────────────────────

@router.get("/category-by-department", summary="Category breakdown per department")
def category_by_department(db: Session = Depends(get_analytics_db)):
    """
    Cross-tab: ticket counts for each (category, department) pair.
    Use for grouped bar charts or heatmaps.
    """
    return analytics_crud.get_category_by_department(db)


# ── ETL Status / History ─────────────────────────────────────────────────────

@router.get("/etl-status", summary="Latest ETL run status")
def etl_status(db: Session = Depends(get_analytics_db)):
    """Returns info about the most recent ETL pipeline execution."""
    run = analytics_crud.get_latest_etl_run(db)
    if not run:
        return {"status": "ETL has never run", "message": "Execute etl/etl_pipeline.py to populate analytics data."}
    return run


@router.get("/etl-history", summary="ETL run history")
def etl_history(limit: int = 10, db: Session = Depends(get_analytics_db)):
    """Returns the last N ETL run audit records."""
    return analytics_crud.get_etl_runs(db, limit=limit)
