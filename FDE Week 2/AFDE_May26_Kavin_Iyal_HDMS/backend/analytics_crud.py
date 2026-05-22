"""
Analytics CRUD – all database queries for the analytics API.
Queries run against analytics.db (populated by ETL pipeline).
"""
from sqlalchemy import func, text, case
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from analytics_models import ReportingTicket, ETLRun


# ──────────────────────────────────────────────────────────────────────────────
# Overview / Summary
# ──────────────────────────────────────────────────────────────────────────────

def get_analytics_summary(db: Session) -> Dict[str, Any]:
    """High-level KPIs for the analytics dashboard header cards."""
    total = db.query(func.count(ReportingTicket.id)).scalar() or 0
    resolved = (
        db.query(func.count(ReportingTicket.id))
        .filter(ReportingTicket.status.in_(["Resolved", "Closed"]))
        .scalar() or 0
    )
    avg_res = (
        db.query(func.avg(ReportingTicket.resolution_time_days))
        .filter(ReportingTicket.resolution_time_days.isnot(None))
        .scalar()
    )
    critical = (
        db.query(func.count(ReportingTicket.id))
        .filter(ReportingTicket.priority == "Critical")
        .scalar() or 0
    )
    departments = (
        db.query(func.count(func.distinct(ReportingTicket.department))).scalar() or 0
    )
    open_tickets = (
        db.query(func.count(ReportingTicket.id))
        .filter(ReportingTicket.status.in_(["Open", "In Progress"]))
        .scalar() or 0
    )
    return {
        "total_tickets": total,
        "resolved_tickets": resolved,
        "open_tickets": open_tickets,
        "avg_resolution_days": round(avg_res, 2) if avg_res else None,
        "critical_tickets": critical,
        "departments_tracked": departments,
        "resolution_rate_pct": round(resolved / total * 100, 1) if total else 0,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Category Distribution
# ──────────────────────────────────────────────────────────────────────────────

def get_category_distribution(db: Session) -> List[Dict[str, Any]]:
    """Count of tickets per issue category, sorted descending."""
    rows = (
        db.query(
            ReportingTicket.issue_category,
            func.count(ReportingTicket.id).label("count"),
        )
        .group_by(ReportingTicket.issue_category)
        .order_by(func.count(ReportingTicket.id).desc())
        .all()
    )
    return [{"category": r.issue_category, "count": r.count} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Priority Distribution
# ──────────────────────────────────────────────────────────────────────────────

def get_priority_distribution(db: Session) -> List[Dict[str, Any]]:
    """Ticket count per priority level."""
    rows = (
        db.query(
            ReportingTicket.priority,
            func.count(ReportingTicket.id).label("count"),
        )
        .group_by(ReportingTicket.priority)
        .order_by(
            case(
                (ReportingTicket.priority == "Critical", 1),
                (ReportingTicket.priority == "High",     2),
                (ReportingTicket.priority == "Medium",   3),
                (ReportingTicket.priority == "Low",      4),
                else_=5,
            )
        )
        .all()
    )
    return [{"priority": r.priority, "count": r.count} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Department-wise Counts
# ──────────────────────────────────────────────────────────────────────────────

def get_department_counts(db: Session) -> List[Dict[str, Any]]:
    """Ticket count per department, sorted descending."""
    rows = (
        db.query(
            ReportingTicket.department,
            func.count(ReportingTicket.id).label("count"),
        )
        .group_by(ReportingTicket.department)
        .order_by(func.count(ReportingTicket.id).desc())
        .all()
    )
    return [{"department": r.department, "count": r.count} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Monthly Volume Trend
# ──────────────────────────────────────────────────────────────────────────────

def get_monthly_volume(db: Session) -> List[Dict[str, Any]]:
    """Ticket volume per calendar month (YYYY-MM), sorted chronologically."""
    rows = (
        db.query(
            ReportingTicket.created_month,
            func.count(ReportingTicket.id).label("count"),
        )
        .filter(ReportingTicket.created_month.isnot(None))
        .group_by(ReportingTicket.created_month)
        .order_by(ReportingTicket.created_month)
        .all()
    )
    return [{"month": r.created_month, "count": r.count} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Resolution Time Trend
# ──────────────────────────────────────────────────────────────────────────────

def get_resolution_trends(db: Session) -> List[Dict[str, Any]]:
    """Average resolution time (days) per month, for resolved tickets."""
    rows = (
        db.query(
            ReportingTicket.created_month,
            func.avg(ReportingTicket.resolution_time_days).label("avg_days"),
            func.count(ReportingTicket.id).label("resolved_count"),
        )
        .filter(ReportingTicket.resolution_time_days.isnot(None))
        .group_by(ReportingTicket.created_month)
        .order_by(ReportingTicket.created_month)
        .all()
    )
    return [
        {
            "month": r.created_month,
            "avg_resolution_days": round(r.avg_days, 2) if r.avg_days else None,
            "resolved_count": r.resolved_count,
        }
        for r in rows
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Status Distribution
# ──────────────────────────────────────────────────────────────────────────────

def get_status_distribution(db: Session) -> List[Dict[str, Any]]:
    """Ticket count per status."""
    rows = (
        db.query(
            ReportingTicket.status,
            func.count(ReportingTicket.id).label("count"),
        )
        .group_by(ReportingTicket.status)
        .all()
    )
    return [{"status": r.status, "count": r.count} for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Category × Department heatmap data
# ──────────────────────────────────────────────────────────────────────────────

def get_category_by_department(db: Session) -> List[Dict[str, Any]]:
    """Cross-tab: ticket counts broken down by category AND department."""
    rows = (
        db.query(
            ReportingTicket.issue_category,
            ReportingTicket.department,
            func.count(ReportingTicket.id).label("count"),
        )
        .group_by(ReportingTicket.issue_category, ReportingTicket.department)
        .order_by(ReportingTicket.issue_category, ReportingTicket.department)
        .all()
    )
    return [
        {"category": r.issue_category, "department": r.department, "count": r.count}
        for r in rows
    ]


# ──────────────────────────────────────────────────────────────────────────────
# ETL Run History
# ──────────────────────────────────────────────────────────────────────────────

def get_etl_runs(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Return the most recent ETL run audit records."""
    runs = (
        db.query(ETLRun)
        .order_by(ETLRun.run_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "run_at": str(r.run_at),
            "source_file": r.source_file,
            "records_extracted": r.records_extracted,
            "duplicates_removed": r.duplicates_removed,
            "records_loaded": r.records_loaded,
            "status": r.status,
            "error_message": r.error_message,
        }
        for r in runs
    ]


def get_latest_etl_run(db: Session) -> Optional[Dict[str, Any]]:
    """Return the most recent ETL run, or None if ETL has never run."""
    run = db.query(ETLRun).order_by(ETLRun.run_at.desc()).first()
    if not run:
        return None
    return {
        "id": run.id,
        "run_at": str(run.run_at),
        "source_file": run.source_file,
        "records_extracted": run.records_extracted,
        "duplicates_removed": run.duplicates_removed,
        "records_loaded": run.records_loaded,
        "status": run.status,
    }
