"""
ETL — Load Stage
=================
Loads the transformed DataFrame into the SQLite knowledge-base database.

Strategy
--------
* For each row, look up (or create) the category and author user.
* Upsert each article: if an article with the same ``title`` already exists,
  update ``view_count``, ``status``, and ``updated_at``; otherwise insert a
  new record.
* Upsert tags and link them to the article.
* Writes load statistics to the ``etl_jobs`` table.

Usage (standalone):
    python -m etl.load
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Add the backend directory to sys.path so we can import backend modules.
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal, engine
import models
from auth import hash_password

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default ETL author (used when a CSV author cannot be matched)
# ---------------------------------------------------------------------------
ETL_AUTHOR_EMAIL = "etl@system.internal"
ETL_AUTHOR_NAME = "ETL Import System"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load(df: pd.DataFrame, job_id: Optional[int] = None) -> Dict:
    """
    Load a transformed DataFrame into the database.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame produced by the transform stage.
    job_id : int, optional
        If provided, update the corresponding ETLJob record with stats.

    Returns
    -------
    dict
        Statistics: inserted, updated, skipped, errors.
    """
    db = SessionLocal()
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0, "total": len(df)}

    try:
        _ensure_schema(db)
        _ensure_etl_author(db)

        author_cache: Dict[str, models.User] = {}
        category_cache: Dict[str, models.Category] = {}
        tag_cache: Dict[str, models.Tag] = {}

        for _, row in df.iterrows():
            try:
                author = _get_or_create_author(db, row, author_cache)
                category = _get_or_create_category(db, str(row.get("category", "Operations")), category_cache)
                tags = _get_or_create_tags(db, row.get("tags_list", []), tag_cache)

                _upsert_article(db, row, author, category, tags, stats)

            except Exception as exc:
                logger.error("Error loading row '%s': %s", row.get("title", "?"), exc)
                stats["errors"] += 1
                db.rollback()

        db.commit()

        # Update ETL job record
        if job_id is not None:
            _update_etl_job(db, job_id, stats)

        logger.info(
            "Load complete — inserted=%d, updated=%d, skipped=%d, errors=%d",
            stats["inserted"], stats["updated"], stats["skipped"], stats["errors"],
        )
    finally:
        db.close()

    return stats


# ---------------------------------------------------------------------------
# Schema / bootstrap helpers
# ---------------------------------------------------------------------------

def _ensure_schema(db) -> None:
    """Create all tables (idempotent) so ETL can run before the API starts."""
    models.Base.metadata.create_all(bind=engine)


def _ensure_etl_author(db) -> models.User:
    """Create a system ETL author user if it doesn't already exist."""
    user = db.query(models.User).filter(models.User.email == ETL_AUTHOR_EMAIL).first()
    if user:
        return user

    author_role = db.query(models.Role).filter(models.Role.role_name == "Author").first()
    if not author_role:
        author_role = models.Role(role_name="Author", description="Article authors")
        db.add(author_role)
        db.flush()

    user = models.User(
        name=ETL_AUTHOR_NAME,
        email=ETL_AUTHOR_EMAIL,
        hashed_password=hash_password("etl-system-user-not-for-login"),
        department="ETL System",
        role_id=author_role.role_id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


# ---------------------------------------------------------------------------
# Lookup / creation helpers
# ---------------------------------------------------------------------------

def _get_or_create_author(db, row: pd.Series, cache: Dict) -> models.User:
    """Return the User matching the row's author_email, or create a new one."""
    email = str(row.get("author_email", "")).strip().lower()
    if not email or email == "nan":
        email = ETL_AUTHOR_EMAIL

    if email in cache:
        return cache[email]

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        author_role = db.query(models.Role).filter(models.Role.role_name == "Author").first()
        if not author_role:
            author_role = models.Role(role_name="Author", description="Article authors")
            db.add(author_role)
            db.flush()

        name = str(row.get("author_name", "Unknown Author")).strip()
        dept = str(row.get("author_department", "")).strip()

        user = models.User(
            name=name if name != "nan" else "Unknown Author",
            email=email,
            hashed_password=hash_password(f"import-{email}-placeholder"),
            department=dept if dept != "nan" else None,
            role_id=author_role.role_id,
            is_active=True,
        )
        db.add(user)
        db.flush()
        logger.info("  Created author user: %s <%s>", user.name, user.email)

    cache[email] = user
    return user


def _get_or_create_category(db, name: str, cache: Dict) -> models.Category:
    """Return or create a category by name."""
    if name in cache:
        return cache[name]

    cat = db.query(models.Category).filter(models.Category.category_name == name).first()
    if not cat:
        cat = models.Category(category_name=name, description=f"Auto-created by ETL: {name}")
        db.add(cat)
        db.flush()
        logger.info("  Created category: %s", name)

    cache[name] = cat
    return cat


def _get_or_create_tags(db, tag_list: list, cache: Dict) -> list:
    """Return or create Tag objects for each tag string."""
    tags = []
    for tag_name in tag_list:
        if not tag_name:
            continue
        if tag_name in cache:
            tags.append(cache[tag_name])
            continue
        tag = db.query(models.Tag).filter(models.Tag.tag_name == tag_name).first()
        if not tag:
            tag = models.Tag(tag_name=tag_name)
            db.add(tag)
            db.flush()
        cache[tag_name] = tag
        tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# Article upsert
# ---------------------------------------------------------------------------

def _upsert_article(db, row: pd.Series, author: models.User,
                    category: models.Category, tags: list, stats: Dict) -> None:
    """Insert a new article or update view_count/status of an existing one."""
    title = str(row.get("title", "")).strip()
    existing = db.query(models.Article).filter(models.Article.title == title).first()

    if existing:
        # Update mutable fields
        new_views = int(row.get("views", 0))
        if new_views > existing.view_count:
            existing.view_count = new_views
        existing.status = str(row.get("status", existing.status))
        existing.updated_at = datetime.utcnow()
        # Refresh tags
        existing.tags = tags
        stats["updated"] += 1
    else:
        # Build Article object
        content = str(row.get("content", "")).strip()
        summary = str(row.get("summary", "")).strip()
        status = str(row.get("status", "Draft"))
        try:
            view_count = int(row.get("views") or 0)
        except (ValueError, TypeError):
            view_count = 0

        created_at = _safe_dt(row.get("created_date")) or datetime.utcnow()
        published_at = _safe_dt(row.get("published_date"))

        article = models.Article(
            title=title,
            content=content,
            summary=summary if summary and summary != "nan" else None,
            category_id=category.category_id,
            author_id=author.user_id,
            status=status,
            view_count=view_count,
            version=1,
            created_at=created_at,
            updated_at=created_at,
            published_at=published_at,
        )
        article.tags = tags
        db.add(article)
        stats["inserted"] += 1


def _safe_dt(value) -> Optional[datetime]:
    """Convert a value (Timestamp, string, NaT, None, float NaN) to datetime or None."""
    if value is None:
        return None
    # Handle NaT and float NaN via pd.isnull (works on all pandas NA sentinels)
    try:
        if pd.isnull(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    try:
        dt = pd.to_datetime(value)
        if pd.isnull(dt):
            return None
        return dt.to_pydatetime()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# ETL Job update
# ---------------------------------------------------------------------------

def _update_etl_job(db, job_id: int, stats: Dict) -> None:
    """Mark the ETLJob record as completed with load statistics."""
    job = db.query(models.ETLJob).filter(models.ETLJob.job_id == job_id).first()
    if job:
        job.status = "completed" if stats["errors"] == 0 else "completed_with_errors"
        job.finished_at = datetime.utcnow()
        job.rows_extracted = stats.get("total", 0)
        job.rows_inserted = stats.get("inserted", 0)
        job.rows_updated = stats.get("updated", 0)
        job.rows_skipped = stats.get("skipped", 0)
        job.rows_errored = stats.get("errors", 0)
        db.flush()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    from etl.extract import extract_all
    from etl.transform import transform

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    datasets_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "datasets"

    try:
        raw = extract_all(datasets_path)
        clean = transform(raw)
        result = load(clean)
        print(f"\n✓ Load complete: {result}")
    except Exception as exc:
        logger.error("Load failed: %s", exc)
        sys.exit(1)
