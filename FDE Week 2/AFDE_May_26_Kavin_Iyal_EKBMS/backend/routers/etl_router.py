"""
ETL Router — Phase 2
=====================
Provides API endpoints for triggering and monitoring the ETL pipeline
from the admin dashboard.

Endpoints
---------
POST /etl/run          — Trigger a new ETL pipeline run (Admin only).
GET  /etl/jobs         — List recent ETL job history (Admin only).
GET  /etl/jobs/{id}    — Get details of a specific ETL job (Admin only).
POST /etl/reports      — Re-generate analytics report CSVs (Admin only).
"""

import logging
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user, require_roles
from database import get_db

logger = logging.getLogger(__name__)

# Resolve the ETL package path (project root must be on sys.path)
ETL_PARENT = Path(__file__).parent.parent.parent  # project root
if str(ETL_PARENT) not in sys.path:
    sys.path.insert(0, str(ETL_PARENT))

router = APIRouter(prefix="/etl", tags=["ETL"])

DATASETS_DIR = Path(__file__).parent.parent.parent / "datasets"


# ---------------------------------------------------------------------------
# Helper: run pipeline in a background thread
# ---------------------------------------------------------------------------

def _run_pipeline_async(job_id: int, datasets_dir: Path) -> None:
    """Execute the ETL pipeline in a background thread."""
    try:
        from etl.pipeline import run_pipeline
        run_pipeline(datasets_dir=datasets_dir, generate_reports=True, job_id=job_id)
    except Exception as exc:
        logger.error("Background ETL job #%s failed: %s", job_id, exc)
        from database import SessionLocal
        db = SessionLocal()
        try:
            job = db.query(models.ETLJob).filter(models.ETLJob.job_id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/run", response_model=schemas.ETLRunResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_etl(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Admin")),
):
    """
    Trigger a new ETL pipeline run (Admin only).
    The pipeline runs asynchronously in a background thread.
    Returns the job_id immediately so the caller can poll for status.
    """
    # Check if a run is already in progress
    running = (
        db.query(models.ETLJob)
        .filter(models.ETLJob.status.in_(["queued", "running"]))
        .first()
    )
    if running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An ETL job is already in progress (job_id={running.job_id}).",
        )

    # Create the job record
    job = models.ETLJob(
        status="queued",
        datasets_dir=str(DATASETS_DIR),
        triggered_by=current_user.user_id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background thread
    t = threading.Thread(
        target=_run_pipeline_async,
        args=(job.job_id, DATASETS_DIR),
        daemon=True,
    )
    t.start()

    return {
        "job_id": job.job_id,
        "status": "queued",
        "message": f"ETL pipeline queued as job #{job.job_id}. Poll GET /etl/jobs/{job.job_id} for status.",
    }


@router.get("/jobs", response_model=List[schemas.ETLJobResponse])
def list_etl_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("Admin")),
):
    """Return the most recent ETL job runs (Admin only)."""
    jobs = (
        db.query(models.ETLJob)
        .order_by(models.ETLJob.created_at.desc())
        .limit(limit)
        .all()
    )
    return jobs


@router.get("/jobs/{job_id}", response_model=schemas.ETLJobResponse)
def get_etl_job(
    job_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("Admin")),
):
    """Return the details of a specific ETL job (Admin only)."""
    job = db.query(models.ETLJob).filter(models.ETLJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="ETL job not found.")
    return job


@router.post("/reports", status_code=status.HTTP_200_OK)
def generate_reports(
    _: models.User = Depends(require_roles("Admin")),
):
    """
    Re-generate all CSV analytics reports from the current database state.
    Returns the list of generated file paths (Admin only).
    """
    try:
        from etl.reports import generate_all_reports
        paths = generate_all_reports()
        return {"status": "ok", "report_count": len(paths), "reports": paths}
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")
