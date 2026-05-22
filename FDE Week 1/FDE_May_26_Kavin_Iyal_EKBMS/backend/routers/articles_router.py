"""
Article endpoints — the core of the knowledge base.

Covers CRUD, the approval workflow (Draft → Pending → Approved/Rejected),
search, attachments, comments, ratings, and bookmarks.
"""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from auth import get_current_user, require_roles
from database import get_db

router = APIRouter(prefix="/articles", tags=["Articles"])

# Where uploaded attachments live on disk.
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".xls", ".xlsx", ".png", ".jpg", ".jpeg",
    ".txt", ".md",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _article_to_response(article: models.Article, db: Session) -> dict:
    """Build an ArticleResponse dict including computed aggregates."""
    avg_q = db.query(func.avg(models.Rating.rating_value), func.count(models.Rating.rating_id)) \
              .filter(models.Rating.article_id == article.article_id).first()
    avg_rating = float(avg_q[0]) if avg_q[0] is not None else None
    rating_count = avg_q[1] or 0

    return {
        "article_id": article.article_id,
        "title": article.title,
        "content": article.content,
        "summary": article.summary,
        "category_id": article.category_id,
        "category_name": article.category.category_name if article.category else None,
        "author_id": article.author_id,
        "author_name": article.author.name if article.author else None,
        "reviewer_id": article.reviewer_id,
        "reviewer_name": article.reviewer.name if article.reviewer else None,
        "status": article.status,
        "approval_comments": article.approval_comments,
        "version": article.version,
        "view_count": article.view_count,
        "tags": article.tags,
        "attachments": article.attachments,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "rating_count": rating_count,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
        "published_at": article.published_at,
    }


def _article_to_list_response(article: models.Article, db: Session) -> dict:
    """Light-weight version used in list endpoints."""
    avg_q = db.query(func.avg(models.Rating.rating_value), func.count(models.Rating.rating_id)) \
              .filter(models.Rating.article_id == article.article_id).first()
    avg_rating = float(avg_q[0]) if avg_q[0] is not None else None
    rating_count = avg_q[1] or 0

    return {
        "article_id": article.article_id,
        "title": article.title,
        "summary": article.summary,
        "category_id": article.category_id,
        "category_name": article.category.category_name if article.category else None,
        "author_id": article.author_id,
        "author_name": article.author.name if article.author else None,
        "status": article.status,
        "version": article.version,
        "view_count": article.view_count,
        "tags": article.tags,
        "average_rating": round(avg_rating, 2) if avg_rating else None,
        "rating_count": rating_count,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


def _get_or_create_tags(db: Session, tag_names: List[str]) -> List[models.Tag]:
    """Look up tags by name, creating any that don't exist yet."""
    result = []
    for name in tag_names:
        cleaned = name.strip().lower()
        if not cleaned:
            continue
        tag = db.query(models.Tag).filter(models.Tag.tag_name == cleaned).first()
        if not tag:
            tag = models.Tag(tag_name=cleaned)
            db.add(tag)
            db.flush()
        result.append(tag)
    return result


# ---------------------------------------------------------------------------
# Article CRUD
# ---------------------------------------------------------------------------
@router.get("", response_model=List[schemas.ArticleListResponse])
def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    sort: str = Query("recent", description="recent | popular | rating"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List articles.

    Regular employees see only Approved articles. Authors, Reviewers, and
    Admins can see any status. Filterable by status, category, author.
    """
    query = db.query(models.Article).options(
        joinedload(models.Article.category),
        joinedload(models.Article.author),
        joinedload(models.Article.tags),
    )

    role = current_user.role.role_name
    if role == "Employee":
        # Employees only see approved content (plus their own drafts/etc — none if Employee)
        query = query.filter(models.Article.status == "Approved")
    elif status:
        query = query.filter(models.Article.status == status)

    if category_id:
        query = query.filter(models.Article.category_id == category_id)
    if author_id:
        query = query.filter(models.Article.author_id == author_id)

    if sort == "popular":
        query = query.order_by(desc(models.Article.view_count))
    elif sort == "rating":
        # Sort by average rating subquery
        rating_subq = (
            db.query(
                models.Rating.article_id,
                func.avg(models.Rating.rating_value).label("avg_rating"),
            )
            .group_by(models.Rating.article_id)
            .subquery()
        )
        query = query.outerjoin(rating_subq, models.Article.article_id == rating_subq.c.article_id) \
                     .order_by(desc(rating_subq.c.avg_rating))
    else:
        query = query.order_by(desc(models.Article.updated_at))

    articles = query.offset(skip).limit(limit).all()
    return [_article_to_list_response(a, db) for a in articles]


@router.get("/search", response_model=List[schemas.ArticleListResponse])
def search_articles(
    q: Optional[str] = Query(None, description="Search keyword"),
    category_id: Optional[int] = Query(None),
    tag: Optional[str] = Query(None),
    author_id: Optional[int] = Query(None),
    sort: str = Query("recent"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Full-text search across title, content, summary."""
    query = db.query(models.Article).options(
        joinedload(models.Article.category),
        joinedload(models.Article.author),
        joinedload(models.Article.tags),
    )

    # Permission filter
    if current_user.role.role_name == "Employee":
        query = query.filter(models.Article.status == "Approved")

    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                models.Article.title.ilike(pattern),
                models.Article.content.ilike(pattern),
                models.Article.summary.ilike(pattern),
            )
        )

    if category_id:
        query = query.filter(models.Article.category_id == category_id)

    if author_id:
        query = query.filter(models.Article.author_id == author_id)

    if tag:
        query = query.join(models.Article.tags).filter(models.Tag.tag_name == tag.lower())

    if sort == "popular":
        query = query.order_by(desc(models.Article.view_count))
    else:
        query = query.order_by(desc(models.Article.updated_at))

    articles = query.distinct().all()
    return [_article_to_list_response(a, db) for a in articles]


@router.get("/pending-approvals", response_model=List[schemas.ArticleListResponse])
def list_pending_approvals(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("Reviewer", "Admin")),
):
    """List all articles awaiting review. Reviewer/Admin only."""
    articles = (
        db.query(models.Article)
        .filter(models.Article.status == "Pending Approval")
        .order_by(models.Article.updated_at.asc())
        .all()
    )
    return [_article_to_list_response(a, db) for a in articles]


@router.get("/my-articles", response_model=List[schemas.ArticleListResponse])
def list_my_articles(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Articles authored by the current user (any status)."""
    articles = (
        db.query(models.Article)
        .filter(models.Article.author_id == current_user.user_id)
        .order_by(models.Article.updated_at.desc())
        .all()
    )
    return [_article_to_list_response(a, db) for a in articles]


@router.get("/{article_id}", response_model=schemas.ArticleResponse)
def get_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Fetch a single article. Increments view count for approved articles."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    # Permission check
    role = current_user.role.role_name
    if role == "Employee" and article.status != "Approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Article not accessible")

    # Track views only for approved articles, and don't count the author's own views
    if article.status == "Approved" and article.author_id != current_user.user_id:
        article.view_count += 1
        view = models.ArticleView(article_id=article.article_id, user_id=current_user.user_id)
        db.add(view)
        db.commit()
        db.refresh(article)

    return _article_to_response(article, db)


@router.post(
    "",
    response_model=schemas.ArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_article(
    payload: schemas.ArticleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Author", "Admin")),
):
    """Create a new article in Draft status. Author/Admin only."""
    category = db.query(models.Category).filter(models.Category.category_id == payload.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category does not exist")

    article = models.Article(
        title=payload.title,
        content=payload.content,
        summary=payload.summary,
        category_id=payload.category_id,
        author_id=current_user.user_id,
        status="Draft",
        version=1,
    )

    if payload.tag_names:
        article.tags = _get_or_create_tags(db, payload.tag_names)

    db.add(article)
    db.commit()
    db.refresh(article)
    return _article_to_response(article, db)


@router.put("/{article_id}", response_model=schemas.ArticleResponse)
def update_article(
    article_id: int,
    payload: schemas.ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update an article.

    Authors can update their own articles when they're in Draft or
    Rejected status. Admins can update anything. Editing bumps the version.
    """
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    role = current_user.role.role_name
    is_author = article.author_id == current_user.user_id

    if role != "Admin":
        if not is_author:
            raise HTTPException(status_code=403, detail="You can only edit your own articles")
        if article.status not in ("Draft", "Rejected"):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot edit article in '{article.status}' status. Withdraw it first.",
            )

    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data:
        category = db.query(models.Category).filter(models.Category.category_id == data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=400, detail="Category does not exist")

    tag_names = data.pop("tag_names", None)
    for k, v in data.items():
        setattr(article, k, v)

    if tag_names is not None:
        article.tags = _get_or_create_tags(db, tag_names)

    article.version += 1
    db.commit()
    db.refresh(article)
    return _article_to_response(article, db)


@router.delete("/{article_id}")
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Delete an article.

    Authors can delete their own drafts; Admins can delete any article.
    """
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    role = current_user.role.role_name
    if role != "Admin":
        if article.author_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="You can only delete your own articles")
        if article.status not in ("Draft", "Rejected"):
            raise HTTPException(status_code=400, detail="Only drafts or rejected articles can be deleted")

    # Clean up files on disk
    for att in article.attachments:
        path = os.path.join(UPLOAD_DIR, att.stored_name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    db.delete(article)
    db.commit()
    return {"message": f"Article {article_id} deleted"}


# ---------------------------------------------------------------------------
# Approval workflow
# ---------------------------------------------------------------------------
@router.post("/{article_id}/submit", response_model=schemas.ArticleResponse)
def submit_for_approval(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Submit a Draft article for review."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if article.author_id != current_user.user_id and current_user.role.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Only the author can submit this article")

    if article.status not in ("Draft", "Rejected"):
        raise HTTPException(status_code=400, detail=f"Cannot submit article in '{article.status}' status")

    article.status = "Pending Approval"
    article.approval_comments = None
    db.commit()
    db.refresh(article)
    return _article_to_response(article, db)


@router.post("/{article_id}/review", response_model=schemas.ArticleResponse)
def review_article(
    article_id: int,
    payload: schemas.ArticleStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("Reviewer", "Admin")),
):
    """
    Approve or reject a pending article. Reviewer/Admin only.
    Status must be one of: Approved, Rejected.
    """
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if article.status != "Pending Approval":
        raise HTTPException(status_code=400, detail="Article is not pending approval")

    new_status = payload.status.value
    if new_status not in ("Approved", "Rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'Approved' or 'Rejected'")

    article.status = new_status
    article.reviewer_id = current_user.user_id
    article.approval_comments = payload.approval_comments
    if new_status == "Approved":
        article.published_at = datetime.utcnow()

    db.commit()
    db.refresh(article)
    return _article_to_response(article, db)


@router.post("/{article_id}/archive", response_model=schemas.ArticleResponse)
def archive_article(
    article_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_roles("Admin")),
):
    """Archive an article. Admin only."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    article.status = "Archived"
    db.commit()
    db.refresh(article)
    return _article_to_response(article, db)


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------
@router.post("/{article_id}/attachments", response_model=schemas.AttachmentResponse)
async def upload_attachment(
    article_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Upload a file attachment to an article. Author of the article or Admin."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    if article.author_id != current_user.user_id and current_user.role.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Only the author can attach files")

    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit")

    # Save with UUID-prefixed name to avoid collisions
    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    with open(path, "wb") as f:
        f.write(content)

    attachment = models.Attachment(
        article_id=article.article_id,
        file_name=file.filename,
        stored_name=stored_name,
        file_size=len(content),
        content_type=file.content_type,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """Download an attachment file."""
    att = db.query(models.Attachment).filter(models.Attachment.attachment_id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    path = os.path.join(UPLOAD_DIR, att.stored_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=410, detail="File no longer available on disk")

    return FileResponse(path, filename=att.file_name, media_type=att.content_type or "application/octet-stream")


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete an attachment. Author of the article or Admin."""
    att = db.query(models.Attachment).filter(models.Attachment.attachment_id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    if att.article.author_id != current_user.user_id and current_user.role.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    path = os.path.join(UPLOAD_DIR, att.stored_name)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

    db.delete(att)
    db.commit()
    return {"message": "Attachment deleted"}


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------
@router.get("/{article_id}/comments", response_model=List[schemas.CommentResponse])
def list_comments(
    article_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    """List all comments on an article."""
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.article_id == article_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )
    return [
        {
            "comment_id": c.comment_id,
            "article_id": c.article_id,
            "user_id": c.user_id,
            "user_name": c.user.name if c.user else None,
            "comment_text": c.comment_text,
            "created_at": c.created_at,
        }
        for c in comments
    ]


@router.post(
    "/{article_id}/comments",
    response_model=schemas.CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    article_id: int,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    comment = models.Comment(
        article_id=article_id,
        user_id=current_user.user_id,
        comment_text=payload.comment_text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "comment_id": comment.comment_id,
        "article_id": comment.article_id,
        "user_id": comment.user_id,
        "user_name": current_user.name,
        "comment_text": comment.comment_text,
        "created_at": comment.created_at,
    }


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a comment. Comment owner or Admin."""
    comment = db.query(models.Comment).filter(models.Comment.comment_id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != current_user.user_id and current_user.role.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}


# ---------------------------------------------------------------------------
# Ratings
# ---------------------------------------------------------------------------
@router.post("/{article_id}/rate", response_model=schemas.RatingResponse)
def rate_article(
    article_id: int,
    payload: schemas.RatingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Rate an article 1-5. Updates the rating if the user already rated it."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    existing = (
        db.query(models.Rating)
        .filter(
            models.Rating.article_id == article_id,
            models.Rating.user_id == current_user.user_id,
        )
        .first()
    )

    if existing:
        existing.rating_value = payload.rating_value
        db.commit()
        db.refresh(existing)
        return existing

    rating = models.Rating(
        article_id=article_id,
        user_id=current_user.user_id,
        rating_value=payload.rating_value,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------
@router.post("/{article_id}/bookmark", response_model=schemas.BookmarkResponse)
def bookmark_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Bookmark an article. No-op if already bookmarked."""
    article = db.query(models.Article).filter(models.Article.article_id == article_id).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")

    existing = (
        db.query(models.Bookmark)
        .filter(
            models.Bookmark.article_id == article_id,
            models.Bookmark.user_id == current_user.user_id,
        )
        .first()
    )
    if existing:
        return existing

    bookmark = models.Bookmark(article_id=article_id, user_id=current_user.user_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    return bookmark


@router.delete("/{article_id}/bookmark")
def remove_bookmark(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Remove a bookmark."""
    bookmark = (
        db.query(models.Bookmark)
        .filter(
            models.Bookmark.article_id == article_id,
            models.Bookmark.user_id == current_user.user_id,
        )
        .first()
    )
    if not bookmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark removed"}


@router.get("/bookmarks/mine", response_model=List[schemas.ArticleListResponse])
def my_bookmarks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List articles bookmarked by the current user."""
    bookmarks = (
        db.query(models.Bookmark)
        .filter(models.Bookmark.user_id == current_user.user_id)
        .order_by(models.Bookmark.created_at.desc())
        .all()
    )
    return [_article_to_list_response(b.article, db) for b in bookmarks if b.article]
