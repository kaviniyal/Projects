"""
ETL — Analytics Reports
========================
Generates CSV analytics reports from the loaded database data.

Reports produced
----------------
1. popular_articles.csv       — Top 20 most-viewed approved articles.
2. category_distribution.csv — Article count and total views per category.
3. author_activity.csv        — Article count, total views, avg rating per author.
4. tag_frequency.csv          — How often each tag is used (top 30).
5. status_summary.csv         — Article count by status.
6. monthly_publication.csv    — Articles published per month (last 12 months).
7. search_keywords.csv        — Top 30 search keywords from the search log.

All reports are written to ``./datasets/reports/``.

Usage (standalone):
    python -m etl.reports
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd

# ---------------------------------------------------------------------------
# Ensure backend is on sys.path
# ---------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal
import models
from sqlalchemy import func

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "datasets" / "reports"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_all_reports(output_dir: Path | None = None) -> List[str]:
    """
    Generate all analytics reports and write them as CSV files.

    Parameters
    ----------
    output_dir : Path, optional
        Directory to write CSV files. Defaults to ``datasets/reports/``.

    Returns
    -------
    list of str
        Paths to the generated CSV files.
    """
    out = Path(output_dir) if output_dir else REPORTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    paths = []
    try:
        paths.append(_report_popular_articles(db, out))
        paths.append(_report_category_distribution(db, out))
        paths.append(_report_author_activity(db, out))
        paths.append(_report_tag_frequency(db, out))
        paths.append(_report_status_summary(db, out))
        paths.append(_report_monthly_publication(db, out))
        paths.append(_report_search_keywords(db, out))
    finally:
        db.close()

    logger.info("Generated %d report(s) in %s", len(paths), out)
    return [str(p) for p in paths]


# ---------------------------------------------------------------------------
# Individual report generators
# ---------------------------------------------------------------------------

def _report_popular_articles(db, out: Path) -> Path:
    """Top 20 most-viewed approved articles."""
    rows = (
        db.query(
            models.Article.article_id,
            models.Article.title,
            models.Category.category_name,
            models.User.name.label("author"),
            models.Article.view_count,
            func.coalesce(func.avg(models.Rating.rating_value), 0).label("avg_rating"),
            func.count(models.Rating.rating_id).label("rating_count"),
        )
        .join(models.Category, models.Article.category_id == models.Category.category_id)
        .join(models.User, models.Article.author_id == models.User.user_id)
        .outerjoin(models.Rating, models.Article.article_id == models.Rating.article_id)
        .filter(models.Article.status == "Approved")
        .group_by(models.Article.article_id)
        .order_by(models.Article.view_count.desc())
        .limit(20)
        .all()
    )

    df = pd.DataFrame(rows, columns=["article_id", "title", "category", "author",
                                      "views", "avg_rating", "rating_count"])
    df["avg_rating"] = df["avg_rating"].round(2)
    path = out / "popular_articles.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ popular_articles.csv (%d rows)", len(df))
    return path


def _report_category_distribution(db, out: Path) -> Path:
    """Article count and total views per category."""
    rows = (
        db.query(
            models.Category.category_id,
            models.Category.category_name,
            func.count(models.Article.article_id).label("article_count"),
            func.coalesce(func.sum(models.Article.view_count), 0).label("total_views"),
        )
        .outerjoin(models.Article, models.Article.category_id == models.Category.category_id)
        .group_by(models.Category.category_id, models.Category.category_name)
        .order_by(func.count(models.Article.article_id).desc())
        .all()
    )

    df = pd.DataFrame(rows, columns=["category_id", "category_name", "article_count", "total_views"])
    path = out / "category_distribution.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ category_distribution.csv (%d rows)", len(df))
    return path


def _report_author_activity(db, out: Path) -> Path:
    """Article count, total views, and avg rating per author."""
    rows = (
        db.query(
            models.User.user_id,
            models.User.name.label("author"),
            models.User.email,
            models.User.department,
            func.count(models.Article.article_id).label("article_count"),
            func.coalesce(func.sum(models.Article.view_count), 0).label("total_views"),
            func.coalesce(func.avg(models.Rating.rating_value), 0).label("avg_rating"),
        )
        .join(models.Article, models.Article.author_id == models.User.user_id)
        .outerjoin(models.Rating, models.Article.article_id == models.Rating.article_id)
        .group_by(models.User.user_id, models.User.name, models.User.email, models.User.department)
        .order_by(func.count(models.Article.article_id).desc())
        .all()
    )

    df = pd.DataFrame(rows, columns=["user_id", "author", "email", "department",
                                      "article_count", "total_views", "avg_rating"])
    df["avg_rating"] = df["avg_rating"].round(2)
    path = out / "author_activity.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ author_activity.csv (%d rows)", len(df))
    return path


def _report_tag_frequency(db, out: Path) -> Path:
    """How often each tag appears across articles (top 30)."""
    rows = (
        db.query(
            models.Tag.tag_id,
            models.Tag.tag_name,
            func.count(models.article_tags.c.article_id).label("usage_count"),
        )
        .join(models.article_tags, models.Tag.tag_id == models.article_tags.c.tag_id)
        .group_by(models.Tag.tag_id, models.Tag.tag_name)
        .order_by(func.count(models.article_tags.c.article_id).desc())
        .limit(30)
        .all()
    )

    df = pd.DataFrame(rows, columns=["tag_id", "tag_name", "usage_count"])
    path = out / "tag_frequency.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ tag_frequency.csv (%d rows)", len(df))
    return path


def _report_status_summary(db, out: Path) -> Path:
    """Article count by status."""
    rows = (
        db.query(
            models.Article.status,
            func.count(models.Article.article_id).label("article_count"),
        )
        .group_by(models.Article.status)
        .order_by(func.count(models.Article.article_id).desc())
        .all()
    )

    df = pd.DataFrame(rows, columns=["status", "article_count"])
    path = out / "status_summary.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ status_summary.csv (%d rows)", len(df))
    return path


def _report_monthly_publication(db, out: Path) -> Path:
    """Articles published per month over the last 12 months."""
    cutoff = datetime.utcnow() - timedelta(days=365)
    rows = (
        db.query(models.Article)
        .filter(
            models.Article.published_at.isnot(None),
            models.Article.published_at >= cutoff,
        )
        .all()
    )

    if not rows:
        df = pd.DataFrame(columns=["year_month", "article_count"])
    else:
        df = pd.DataFrame([{"published_at": r.published_at} for r in rows])
        df["published_at"] = pd.to_datetime(df["published_at"])
        df["year_month"] = df["published_at"].dt.to_period("M").astype(str)
        df = df.groupby("year_month").size().reset_index(name="article_count")
        df = df.sort_values("year_month")

    path = out / "monthly_publication.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ monthly_publication.csv (%d rows)", len(df))
    return path


def _report_search_keywords(db, out: Path) -> Path:
    """Top 30 search keywords from the SearchLog table."""
    rows = (
        db.query(
            models.SearchLog.keyword,
            func.count(models.SearchLog.log_id).label("search_count"),
        )
        .filter(models.SearchLog.keyword.isnot(None))
        .group_by(models.SearchLog.keyword)
        .order_by(func.count(models.SearchLog.log_id).desc())
        .limit(30)
        .all()
    )

    df = pd.DataFrame(rows, columns=["keyword", "search_count"])
    path = out / "search_keywords.csv"
    df.to_csv(path, index=False)
    logger.info("  ✓ search_keywords.csv (%d rows)", len(df))
    return path


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        paths = generate_all_reports()
        print("\n✓ Reports generated:")
        for p in paths:
            print(f"   {p}")
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        sys.exit(1)
