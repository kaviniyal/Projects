"""
Analytics endpoints: dashboard stats, most viewed, top rated, recent uploads.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
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


@router.get("", response_model=schemas.AnalyticsResponse)
def analytics(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    """Return analytics: most viewed, top rated, by category, and recent uploads."""

    # Most viewed (top 5 approved articles by view_count)
    most_viewed_rows = (
        db.query(models.Article)
        .filter(models.Article.status == "Approved")
        .order_by(models.Article.view_count.desc())
        .limit(5)
        .all()
    )
    most_viewed = [
        {"article_id": a.article_id, "title": a.title, "view_count": a.view_count, "average_rating": None}
        for a in most_viewed_rows
    ]

    # Top rated (top 5 by average rating, minimum 1 rating)
    top_rated_rows = (
        db.query(
            models.Article,
            func.avg(models.Rating.rating_value).label("avg_rating"),
        )
        .join(models.Rating, models.Article.article_id == models.Rating.article_id)
        .filter(models.Article.status == "Approved")
        .group_by(models.Article.article_id)
        .order_by(func.avg(models.Rating.rating_value).desc())
        .limit(5)
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

    # Articles per category
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

    # Recent uploads — articles created in the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_uploads = (
        db.query(models.Article)
        .filter(models.Article.created_at >= seven_days_ago)
        .count()
    )

    return {
        "most_viewed": most_viewed,
        "top_rated": top_rated,
        "by_category": by_category,
        "recent_uploads": recent_uploads,
    }
