"""
ETL — Pipeline Orchestrator
=============================
Runs the full Extract → Transform → Load sequence and records a job entry in
the ``etl_jobs`` table.

Usage (standalone):
    python -m etl.pipeline                        # uses ./datasets/
    python -m etl.pipeline path/to/datasets/      # custom datasets dir
    python -m etl.pipeline --report               # run pipeline + generate reports
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Ensure backend is on sys.path
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, engine
import models

from etl.extract import extract_all
from etl.transform import transform
from etl.load import load

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pipeline(
    datasets_dir: str | Path | None = None,
    generate_reports: bool = False,
    job_id: Optional[int] = None,
) -> dict:
    """
    Execute the full ETL pipeline.

    Parameters
    ----------
    datasets_dir : str or Path, optional
        Directory containing dataset files. Defaults to ``../datasets``.
    generate_reports : bool
        If True, run the reports module after load to produce CSV analytics.
    job_id : int, optional
        Pre-created ETLJob id to update during the run.

    Returns
    -------
    dict
        Pipeline result containing ``stats`` and ``duration_seconds``.
    """
    if datasets_dir is None:
        datasets_dir = Path(__file__).parent.parent / "datasets"
    datasets_dir = Path(datasets_dir)

    start_time = time.time()

    # ------------------------------------------------------------------
    # Create or update the ETLJob record
    # ------------------------------------------------------------------
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if job_id is None:
            job = models.ETLJob(
                status="running",
                datasets_dir=str(datasets_dir),
                started_at=datetime.utcnow(),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.job_id
        else:
            job = db.query(models.ETLJob).filter(models.ETLJob.job_id == job_id).first()
            if job:
                job.status = "running"
                job.started_at = datetime.utcnow()
                db.commit()
    finally:
        db.close()

    logger.info("=" * 60)
    logger.info("ETL Pipeline — Job #%s", job_id)
    logger.info("Dataset dir: %s", datasets_dir)
    logger.info("=" * 60)

    result = {"job_id": job_id, "stats": {}, "duration_seconds": 0, "error": None}

    try:
        # ------------------------------------------------------------------
        # 1. EXTRACT
        # ------------------------------------------------------------------
        logger.info("[1/3] EXTRACT")
        raw_df = extract_all(datasets_dir)
        logger.info("      %d raw rows extracted.", len(raw_df))

        # ------------------------------------------------------------------
        # 2. TRANSFORM
        # ------------------------------------------------------------------
        logger.info("[2/3] TRANSFORM")
        clean_df = transform(raw_df)
        logger.info("      %d rows after transformation.", len(clean_df))

        # ------------------------------------------------------------------
        # 3. LOAD
        # ------------------------------------------------------------------
        logger.info("[3/3] LOAD")
        stats = load(clean_df, job_id=job_id)
        result["stats"] = stats
        logger.info("      %s", stats)

        # ------------------------------------------------------------------
        # 4. Optional reports
        # ------------------------------------------------------------------
        if generate_reports:
            logger.info("[4/4] GENERATE REPORTS")
            try:
                from etl.reports import generate_all_reports
                report_paths = generate_all_reports()
                result["reports"] = report_paths
                logger.info("      Reports written: %s", report_paths)
            except Exception as rep_err:
                logger.warning("Report generation failed: %s", rep_err)

    except Exception as exc:
        result["error"] = str(exc)
        logger.error("Pipeline failed: %s", exc)

        # Mark job as failed
        db = SessionLocal()
        try:
            job_record = db.query(models.ETLJob).filter(models.ETLJob.job_id == job_id).first()
            if job_record:
                job_record.status = "failed"
                job_record.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()

    result["duration_seconds"] = round(time.time() - start_time, 2)
    logger.info("Pipeline finished in %.2fs.", result["duration_seconds"])
    return result


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )

    datasets_arg: Optional[Path] = None
    generate_reports = False

    for arg in sys.argv[1:]:
        if arg == "--report":
            generate_reports = True
        else:
            datasets_arg = Path(arg)

    outcome = run_pipeline(
        datasets_dir=datasets_arg,
        generate_reports=generate_reports,
    )

    print("\n" + "=" * 50)
    if outcome.get("error"):
        print(f"FAILED: {outcome['error']}")
        sys.exit(1)
    else:
        s = outcome["stats"]
        print(f"OK: Pipeline completed in {outcome['duration_seconds']}s")
        print(f"  Inserted : {s.get('inserted', 0)}")
        print(f"  Updated  : {s.get('updated', 0)}")
        print(f"  Skipped  : {s.get('skipped', 0)}")
        print(f"  Errors   : {s.get('errors', 0)}")
        if "reports" in outcome:
            print(f"  Reports  : {len(outcome['reports'])} files written to datasets/reports/")
