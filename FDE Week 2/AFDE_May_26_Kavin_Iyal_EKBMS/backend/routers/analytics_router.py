"""
Analytics Router — Phase 2
============================
Dashboard stats, most viewed, top rated, category trends, search keyword
analysis, author activity reports, and monthly publication timeline.

Endpoints
---------
GET /analytics/dashboard        — High-level counts (Phase 1 compat.)
GET /analytics                  — Full Phase 2 analytics payload.
GET /analytics/category-trends  — Views + article counts per category.
GET /analytics/search-keywords  — Top search keywords from SearchLog.
GET /analytics/author-activity  — Per-author productivity metrics.
GET /analytics/monthly-publish  — Monthly publication trend (12 months).
GET /analytics/top-tags         — Most-used tags.
GET /analytics/etl-summary      — Latest ETL job status summary.
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ---------------------------------------------------------------------------
# Phase 1-compatible dashboard endpoint
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Return high-level counts for the dashboard."""
    total = db.query(models.Article).count()
    approved = db.query(models.Article).filter(models.Article.status == "Approved").count()
    pending = db.query(models.Article).filter(models.Article.status == "Pending Approval").count()
    draft = db.query(models.Article).filter(models.Article.status == "Draft").count()
    rejected = db.query(models.Article).filter(models.Article.status == "Rejected").count()
    archived = db.query(models.Article).filter(models.Article.status == "Archived").count()
    users = db.query(models.User).count()
    categories = db.query(models.Category).count()
    views = db.query(models.ArticleView).count()

    return {
        "total_articles": total,
        "approved_articles": approved,
        "pending_articles": pending,
        "draft_articles": draft,
        "rejected_articles": rejected,
        "archived_articles": archived,
        "total_users": users,
        "total_categories": categories,
        "total_views": views,
    }


# ---------------------------------------------------------------------------
# Phase 2 full analytics payload
# ---------------------------------------------------------------------------

@router.get("", response_model=schemas.ExtendedAnalyticsResponse)
def analytics(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Return the full Phase 2 analytics payload."""

    # --- Most viewed (top 10 approved) ---
    most_viewed_rows = (
        db.query(models.Article)
        .filter(models.Article.status == "Approved")
        .order_by(models.Article.view_count.desc())
        .limit(10)
        .all()
    )
    most_viewed = [
        {"article_id": a.article_id, "title": a.title, "view_count": a.view_count, "average_rating": None}
        for a in most_viewed_rows
    ]

    # --- Top rated (top 10, min 1 rating) ---
    top_rated_rows = (
        db.query(
            models.Article,
            func.avg(models.Rating.rating_value).label("avg_rating"),
        )
        .join(models.Rating, models.Article.article_id == models.Rating.article_id)
        .filter(models.Article.status == "Approved")
        .group_by(models.Article.article_id)
        .order_by(func.avg(models.Rating.rating_value).desc())
        .limit(10)
        .all()
    )
    top_rated = [
        {
            "article_id": a.article_id,
            "title": a.title,
            "view_count": a.view_count,
            "average_rating": round(float(avg), 2) if avg else None,
        }
        for a, avg in top_rated_rows
    ]

    # --- By category (article counts) ---
    by_category_rows = (
        db.query(
            models.Category.category_id,
            models.Category.category_name,
            func.count(models.Article.article_id).label("article_count"),
        )
        .outerjoin(models.Article, models.Article.category_id == models.Category.category_id)
        .group_by(models.Category.category_id, models.Category.category_name)
        .order_by(func.count(models.Article.article_id).desc())
        .all()
    )
    by_category = [
        {"category_id": cid, "category_name": cname, "article_count": count}
        for cid, cname, count in by_category_rows
    ]

    # --- Recent uploads ---
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = (
        db.query(models.Article)
        .filter(models.Article.created_at >= seven_days_ago)
        .count()
    )

    # --- Category trends (views + articles) ---
    category_trends = _get_category_trends(db)

    # --- Monthly publication ---
    monthly_publication = _get_monthly_publication(db)

    # --- Top tags ---
    top_tags = _get_top_tags(db)

    # --- Search keywords ---
    search_keywords = _get_search_keywords(db)

    # --- Author activity ---
    author_activity = _get_author_activity(db)

    return {
        "most_viewed": most_viewed,
        "top_rated": top_rated,
        "by_category": by_category,
        "recent_uploads": recent_uploads,
        "category_trends": category_trends,
        "monthly_publication": monthly_publication,
        "top_tags": top_tags,
        "search_keywords": search_keywords,
        "author_activity": author_activity,
    }


# ---------------------------------------------------------------------------
# Dedicated analytics endpoints
# ---------------------------------------------------------------------------

@router.get("/category-trends", response_model=List[schemas.CategoryTrendPoint])
def category_trends(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Article counts and view totals per category."""
    return _get_category_trends(db)


@router.get("/search-keywords", response_model=List[schemas.SearchKeywordStat])
def search_keywords(
    limit: int = 30,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Top search keywords from the search log."""
    return _get_search_keywords(db, limit=limit)


@router.get("/author-activity", response_model=List[schemas.AuthorActivityStat])
def author_activity(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Per-author article count, views, and average rating."""
    return _get_author_activity(db)


@router.get("/monthly-publish", response_model=List[schemas.MonthlyPublicationPoint])
def monthly_publication(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Articles published per month over the last 12 months."""
    return _get_monthly_publication(db)


@router.get("/top-tags", response_model=List[schemas.TagUsageStat])
def top_tags(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Most frequently used tags."""
    return _get_top_tags(db, limit=limit)


@router.get("/etl-summary")
def etl_summary(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Return a summary of the most recent ETL job."""
    latest = (
        db.query(models.ETLJob)
        .order_by(models.ETLJob.created_at.desc())
        .first()
    )
    if not latest:
        return {"status": "never_run", "last_run": None}

    return {
        "job_id": latest.job_id,
        "status": latest.status,
        "started_at": latest.started_at,
        "finished_at": latest.finished_at,
        "rows_inserted": latest.rows_inserted,
        "rows_updated": latest.rows_updated,
        "rows_errored": latest.rows_errored,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_category_trends(db) -> list:
    rows = (
        db.query(
            models.Category.category_id,
            models.Category.category_name,
            func.count(models.Article.article_id).label("article_count"),
            func.coalesce(func.sum(models.Article.view_count), 0).label("total_views"),
        )
        .outerjoin(models.Article, models.Article.category_id == models.Category.category_id)
        .group_by(models.Category.category_id, models.Category.category_name)
        .order_by(func.coalesce(func.sum(models.Article.view_count), 0).desc())
        .all()
    )
    result = []
    for cid, cname, article_count, total_views in rows:
        avg_views = round(total_views / article_count, 1) if article_count > 0 else 0.0
        result.append({
            "category_id": cid,
            "category_name": cname,
            "article_count": article_count,
            "total_views": total_views,
            "avg_views_per_article": avg_views,
        })
    return result


def _get_monthly_publication(db) -> list:
    cutoff = datetime.utcnow() - timedelta(days=365)
    rows = (
        db.query(models.Article)
        .filter(
            models.Article.published_at.isnot(None),
            models.Article.published_at >= cutoff,
        )
        .order_by(models.Article.published_at)
        .all()
    )

    monthly: dict = {}
    for row in rows:
        key = row.published_at.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + 1

    return [{"year_month": k, "article_count": v} for k, v in sorted(monthly.items())]


def _get_top_tags(db, limit: int = 20) -> list:
    rows = (
        db.query(
            models.Tag.tag_name,
            func.count(models.article_tags.c.article_id).label("usage_count"),
        )
        .join(models.article_tags, models.Tag.tag_id == models.article_tags.c.tag_id)
        .group_by(models.Tag.tag_name)
        .order_by(func.count(models.article_tags.c.article_id).desc())
        .limit(limit)
        .all()
    )
    return [{"tag_name": tag_name, "usage_count": cnt} for tag_name, cnt in rows]


def _get_search_keywords(db, limit: int = 30) -> list:
    rows = (
        db.query(
            models.SearchLog.keyword,
            func.count(models.SearchLog.log_id).label("search_count"),
        )
        .filter(models.SearchLog.keyword.isnot(None))
        .group_by(models.SearchLog.keyword)
        .order_by(func.count(models.SearchLog.log_id).desc())
        .limit(limit)
        .all()
    )
    return [{"keyword": kw, "search_count": cnt} for kw, cnt in rows]


def _get_author_activity(db) -> list:
    rows = (
        db.query(
            models.User.user_id,
            models.User.name.label("author_name"),
            models.User.department,
            func.count(models.Article.article_id).label("article_count"),
            func.coalesce(func.sum(models.Article.view_count), 0).label("total_views"),
            func.avg(models.Rating.rating_value).label("avg_rating"),
        )
        .join(models.Article, models.Article.author_id == models.User.user_id)
        .outerjoin(models.Rating, models.Article.article_id == models.Rating.article_id)
        .group_by(models.User.user_id, models.User.name, models.User.department)
        .order_by(func.count(models.Article.article_id).desc())
        .limit(20)
        .all()
    )
    return [
        {
            "user_id": uid,
            "author_name": name,
            "department": dept,
            "article_count": cnt,
            "total_views": views,
            "avg_rating": round(float(avg), 2) if avg else None,
        }
        for uid, name, dept, cnt, views, avg in rows
    ]
