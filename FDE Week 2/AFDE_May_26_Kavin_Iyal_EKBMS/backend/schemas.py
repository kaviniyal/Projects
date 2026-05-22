"""
Pydantic schemas for request validation and response serialization.

Separated into per-entity sections for clarity. Schemas are versioned
into Create / Update / Response variants to keep the API contract explicit.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class RoleEnum(str, Enum):
    ADMIN = "Admin"
    AUTHOR = "Author"
    REVIEWER = "Reviewer"
    EMPLOYEE = "Employee"


class ArticleStatusEnum(str, Enum):
    DRAFT = "Draft"
    PENDING = "Pending Approval"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    ARCHIVED = "Archived"


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)
    department: Optional[str] = Field(None, max_length=100)
    role: RoleEnum = RoleEnum.EMPLOYEE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class PasswordReset(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, max_length=72)


# ---------------------------------------------------------------------------
# Role schema
# ---------------------------------------------------------------------------
class RoleResponse(BaseModel):
    role_id: int
    role_name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------
class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    department: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None  # populated from joined role
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    role: Optional[RoleEnum] = None
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Category schemas
# ---------------------------------------------------------------------------
class CategoryCreate(BaseModel):
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None


class CategoryUpdate(BaseModel):
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Tag schemas
# ---------------------------------------------------------------------------
class TagCreate(BaseModel):
    tag_name: str = Field(..., min_length=1, max_length=50)


class TagResponse(BaseModel):
    tag_id: int
    tag_name: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Article schemas
# ---------------------------------------------------------------------------
class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=10)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: int
    tag_names: List[str] = Field(default_factory=list)  # creates tags on the fly


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    content: Optional[str] = Field(None, min_length=10)
    summary: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    tag_names: Optional[List[str]] = None


class ArticleStatusUpdate(BaseModel):
    status: ArticleStatusEnum
    approval_comments: Optional[str] = None


class AttachmentResponse(BaseModel):
    attachment_id: int
    file_name: str
    file_size: int
    content_type: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    article_id: int
    title: str
    content: str
    summary: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    reviewer_id: Optional[int] = None
    reviewer_name: Optional[str] = None
    status: ArticleStatusEnum
    approval_comments: Optional[str] = None
    version: int
    view_count: int
    tags: List[TagResponse] = []
    attachments: List[AttachmentResponse] = []
    average_rating: Optional[float] = None
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Lightweight version of ArticleResponse used in lists/feeds."""

    article_id: int
    title: str
    summary: Optional[str] = None
    category_id: int
    category_name: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    status: ArticleStatusEnum
    version: int
    view_count: int
    tags: List[TagResponse] = []
    average_rating: Optional[float] = None
    rating_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Comment schemas
# ---------------------------------------------------------------------------
class CommentCreate(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    comment_id: int
    article_id: int
    user_id: int
    user_name: Optional[str] = None
    comment_text: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Rating schemas
# ---------------------------------------------------------------------------
class RatingCreate(BaseModel):
    rating_value: int = Field(..., ge=1, le=5)


class RatingResponse(BaseModel):
    rating_id: int
    article_id: int
    user_id: int
    rating_value: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Bookmark schema
# ---------------------------------------------------------------------------
class BookmarkResponse(BaseModel):
    bookmark_id: int
    article_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class DashboardStats(BaseModel):
    total_articles: int
    approved_articles: int
    pending_articles: int
    draft_articles: int
    rejected_articles: int
    archived_articles: int
    total_users: int
    total_categories: int
    total_views: int


class PopularArticle(BaseModel):
    article_id: int
    title: str
    view_count: int
    average_rating: Optional[float] = None


class CategoryStat(BaseModel):
    category_id: int
    category_name: str
    article_count: int


class AnalyticsResponse(BaseModel):
    most_viewed: List[PopularArticle]
    top_rated: List[PopularArticle]
    by_category: List[CategoryStat]
    recent_uploads: int


# ---------------------------------------------------------------------------
# Phase 2 — ETL & Extended Analytics schemas
# ---------------------------------------------------------------------------

class ETLJobResponse(BaseModel):
    job_id: int
    status: str
    datasets_dir: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    rows_extracted: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_skipped: int = 0
    rows_errored: int = 0
    triggered_by: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ETLRunResponse(BaseModel):
    """Returned immediately when a pipeline run is queued/started."""
    job_id: int
    status: str
    message: str


class SearchKeywordStat(BaseModel):
    keyword: str
    search_count: int


class AuthorActivityStat(BaseModel):
    user_id: int
    author_name: str
    department: Optional[str] = None
    article_count: int
    total_views: int
    avg_rating: Optional[float] = None


class CategoryTrendPoint(BaseModel):
    category_id: int
    category_name: str
    article_count: int
    total_views: int
    avg_views_per_article: float


class MonthlyPublicationPoint(BaseModel):
    year_month: str
    article_count: int


class TagUsageStat(BaseModel):
    tag_name: str
    usage_count: int


class ExtendedAnalyticsResponse(BaseModel):
    """Full Phase 2 analytics payload."""
    most_viewed: List[PopularArticle]
    top_rated: List[PopularArticle]
    by_category: List[CategoryStat]
    recent_uploads: int
    # Phase 2 additions
    category_trends: List[CategoryTrendPoint]
    monthly_publication: List[MonthlyPublicationPoint]
    top_tags: List[TagUsageStat]
    search_keywords: List[SearchKeywordStat]
    author_activity: List[AuthorActivityStat]


# Forward-reference resolution for TokenResponse → UserResponse
TokenResponse.model_rebuild()
