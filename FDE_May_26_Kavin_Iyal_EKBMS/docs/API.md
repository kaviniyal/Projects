# API Reference

Base URL: `http://localhost:8000`

All endpoints (except `/auth/register` and `/auth/login`) require an `Authorization: Bearer <token>` header.

Interactive docs at `/docs` (Swagger UI) and `/redoc`.

---

## Authentication

### POST /auth/register
Create a new user account.

**Body:**
```json
{
  "name": "Alice Smith",
  "email": "alice@example.com",
  "password": "securepass123",
  "department": "Engineering",
  "role": "Author"
}
```
Roles: `Admin`, `Author`, `Reviewer`, `Employee`.

**Returns:** 201 with user object.

### POST /auth/login
**Body:** `{ "email": "...", "password": "..." }`

**Returns:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": { "user_id": 1, "name": "...", "role_name": "Admin", ... }
}
```

### GET /auth/me
Returns the currently authenticated user.

### POST /auth/reset-password
**Body:** `{ "email": "...", "new_password": "..." }`

---

## Users (Admin)

### GET /users
List all users. **Admin only.**

### GET /users/{id}
Get one user. Self or Admin.

### PUT /users/{id}
**Body:**
```json
{ "name": "...", "department": "...", "role": "Author", "is_active": true }
```
All fields optional. **Admin only.**

### DELETE /users/{id}
**Admin only.** Cannot delete yourself.

### GET /users/roles/all
List all roles.

---

## Categories

### GET /categories
List all categories.

### POST /categories
**Admin only.**
```json
{ "category_name": "Networking", "description": "Network docs", "parent_id": 2 }
```

### PUT /categories/{id}
**Admin only.**

### DELETE /categories/{id}
**Admin only.** Fails if articles still use this category.

---

## Tags

### GET /tags
List all tags.

Tags are auto-created when articles include `tag_names`.

---

## Articles

### GET /articles
Query parameters:
- `status` — filter by status
- `category_id` — filter by category
- `author_id` — filter by author
- `sort` — `recent` (default) | `popular` | `rating`
- `skip` / `limit` — pagination

Employees see only `Approved`. Other roles see everything (filter by status).

### GET /articles/search
- `q` — keyword (matches title/content/summary)
- `category_id`
- `tag` — tag name
- `author_id`
- `sort`

### GET /articles/my-articles
Articles authored by the current user (any status).

### GET /articles/pending-approvals
Articles awaiting review. **Reviewer/Admin only.**

### GET /articles/{id}
Increments view count for Approved articles (excluding the author's own views).

### POST /articles
**Author/Admin only.**
```json
{
  "title": "How to Connect to VPN",
  "content": "Step-by-step instructions...",
  "summary": "VPN connection guide",
  "category_id": 2,
  "tag_names": ["vpn", "remote", "networking"]
}
```
Returns the new article in `Draft` status.

### PUT /articles/{id}
Update an article. Authors can edit own articles in `Draft` or `Rejected`. Admins can edit anything. Bumps `version`.

### DELETE /articles/{id}
Authors delete own drafts; Admins delete anything.

### POST /articles/{id}/submit
Submit a `Draft` or `Rejected` article for approval. Author only.

### POST /articles/{id}/review
**Reviewer/Admin only.**
```json
{ "status": "Approved", "approval_comments": "Looks great!" }
```
Status must be `Approved` or `Rejected`. Approving sets `published_at`.

### POST /articles/{id}/archive
**Admin only.** Sets status to `Archived`.

---

## Attachments

### POST /articles/{id}/attachments
Multipart upload. Field name: `file`. Max 10MB. Allowed extensions: `.pdf .doc .docx .ppt .pptx .xls .xlsx .png .jpg .jpeg .txt .md`.

Author of the article or Admin only.

### GET /articles/attachments/{id}/download
Returns the file with original filename.

### DELETE /articles/attachments/{id}
Author of the parent article or Admin only.

---

## Comments

### GET /articles/{id}/comments
List comments on an article.

### POST /articles/{id}/comments
```json
{ "comment_text": "Great article, thanks!" }
```

### DELETE /articles/comments/{id}
Comment owner or Admin.

---

## Ratings

### POST /articles/{id}/rate
```json
{ "rating_value": 5 }
```
1–5 stars. Updates the user's existing rating if they've rated before.

---

## Bookmarks

### POST /articles/{id}/bookmark
No-op if already bookmarked.

### DELETE /articles/{id}/bookmark

### GET /articles/bookmarks/mine
Current user's bookmarked articles.

---

## Analytics

### GET /analytics/dashboard
```json
{
  "total_articles": 47,
  "approved_articles": 30,
  "pending_articles": 5,
  "draft_articles": 8,
  "rejected_articles": 2,
  "archived_articles": 2,
  "total_users": 12,
  "total_categories": 8,
  "total_views": 1247
}
```

### GET /analytics
```json
{
  "most_viewed":   [{ "article_id": 3, "title": "...", "view_count": 152 }],
  "top_rated":     [{ "article_id": 7, "title": "...", "average_rating": 4.8 }],
  "by_category":   [{ "category_id": 2, "category_name": "IT Support", "article_count": 12 }],
  "recent_uploads": 6
}
```

---

## Error responses

| Status | Meaning |
|--------|---------|
| 400 | Bad request (business logic error) |
| 401 | Missing or invalid auth token |
| 403 | Authenticated but lacks permission |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate email) |
| 422 | Validation failed (Pydantic) |
| 500 | Server error |

Error body:
```json
{ "detail": "Human-readable message" }
```
