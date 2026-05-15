"""
SQLAlchemy ORM models for the Enterprise Knowledge Base Management System.

Models map to the entities described in the requirements document:
Users, Roles, Articles, Categories, Tags, Attachments, Comments,
Ratings, Bookmarks, and ArticleViews (for analytics).
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# Association table for many-to-many between articles and tags
# ---------------------------------------------------------------------------
article_tags = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.article_id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.tag_id"), primary_key=True),
)


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------
class Role(Base):
    """Roles for RBAC: Admin, Author, Reviewer, Employee."""

    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(Base):
    """Application user — author, reviewer, admin, or regular employee."""

    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="users")
    articles = relationship("Article", back_populates="author", foreign_keys="Article.author_id")
    comments = relationship("Comment", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class Category(Base):
    """
    Hierarchical category. `parent_id` lets a category nest under another
    (e.g. "IT Support" → "Networking" → "VPN").
    """

    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category_name = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.category_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    parent = relationship("Category", remote_side=[category_id], backref="children")
    articles = relationship("Article", back_populates="category")


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------
class Tag(Base):
    """Free-form tag attached to articles (many-to-many)."""

    __tablename__ = "tags"

    tag_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tag_name = Column(String(50), unique=True, nullable=False, index=True)

    articles = relationship("Article", secondary=article_tags, back_populates="tags")


# ---------------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------------
class Article(Base):
    """Core knowledge article with approval workflow and versioning."""

    __tablename__ = "articles"

    article_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(String(500), nullable=True)

    category_id = Column(Integer, ForeignKey("categories.category_id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    # Statuses: Draft, Pending Approval, Approved, Rejected, Archived
    status = Column(String(30), default="Draft", nullable=False, index=True)
    approval_comments = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    view_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    author = relationship("User", back_populates="articles", foreign_keys=[author_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")
    attachments = relationship("Attachment", back_populates="article", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="article", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="article", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", back_populates="article", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Attachment
# ---------------------------------------------------------------------------
class Attachment(Base):
    """Uploaded file linked to an article (PDF, DOC, image, etc.)."""

    __tablename__ = "attachments"

    attachment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.article_id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False)  # UUID-prefixed name on disk
    file_size = Column(Integer, nullable=False)  # bytes
    content_type = Column(String(100), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("Article", back_populates="attachments")


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------
class Comment(Base):
    """User comments on an article."""

    __tablename__ = "comments"

    comment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.article_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("Article", back_populates="comments")
    user = relationship("User", back_populates="comments")


# ---------------------------------------------------------------------------
# Rating
# ---------------------------------------------------------------------------
class Rating(Base):
    """1-5 star rating from a user on an article. One rating per user/article."""

    __tablename__ = "ratings"

    rating_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.article_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    rating_value = Column(Integer, nullable=False)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("Article", back_populates="ratings")
    user = relationship("User", back_populates="ratings")


# ---------------------------------------------------------------------------
# Bookmark
# ---------------------------------------------------------------------------
class Bookmark(Base):
    """User bookmarks (favorites). One bookmark per user/article."""

    __tablename__ = "bookmarks"

    bookmark_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.article_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("Article", back_populates="bookmarks")
    user = relationship("User", back_populates="bookmarks")


# ---------------------------------------------------------------------------
# ArticleView (analytics)
# ---------------------------------------------------------------------------
class ArticleView(Base):
    """Records each article view for analytics."""

    __tablename__ = "article_views"

    view_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.article_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
