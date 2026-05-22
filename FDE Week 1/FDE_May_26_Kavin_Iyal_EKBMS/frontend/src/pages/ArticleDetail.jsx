import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { articleService } from '../services/apiService'
import { Badge, StarRating } from '../components/Common'
import { useAuth } from '../context/AuthContext'

function ArticleDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user, hasRole } = useAuth()

  const [article, setArticle] = useState(null)
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [bookmarked, setBookmarked] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [reviewComment, setReviewComment] = useState('')

  const load = async () => {
    try {
      const [a, c, bookmarks] = await Promise.all([
        articleService.get(id),
        articleService.listComments(id),
        articleService.myBookmarks().catch(() => []),
      ])
      setArticle(a)
      setComments(c)
      setBookmarked(bookmarks.some((b) => b.article_id === Number(id)))
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load article')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [id])

  const isAuthor = article && user && article.author_id === user.user_id
  const canEdit = article && (hasRole('Admin') || (isAuthor && ['Draft', 'Rejected'].includes(article.status)))
  const canSubmit = article && isAuthor && ['Draft', 'Rejected'].includes(article.status)
  const canReview = article && hasRole('Reviewer', 'Admin') && article.status === 'Pending Approval'
  const canArchive = article && hasRole('Admin') && article.status !== 'Archived'

  const handleRate = async (value) => {
    try {
      await articleService.rate(id, value)
      await load()
    } catch {}
  }

  const handleBookmark = async () => {
    try {
      if (bookmarked) {
        await articleService.unbookmark(id)
        setBookmarked(false)
      } else {
        await articleService.bookmark(id)
        setBookmarked(true)
      }
    } catch {}
  }

  const handleAddComment = async (e) => {
    e.preventDefault()
    if (!newComment.trim()) return
    try {
      await articleService.addComment(id, newComment)
      setNewComment('')
      await load()
    } catch {}
  }

  const handleDeleteComment = async (commentId) => {
    if (!confirm('Delete this comment?')) return
    try {
      await articleService.deleteComment(commentId)
      await load()
    } catch {}
  }

  const handleSubmitForApproval = async () => {
    if (!confirm('Submit this article for approval?')) return
    try {
      await articleService.submit(id)
      setSuccess('Submitted for approval')
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  const handleReview = async (status) => {
    try {
      await articleService.review(id, status, reviewComment)
      setSuccess(`Article ${status.toLowerCase()}`)
      setReviewComment('')
      await load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  const handleArchive = async () => {
    if (!confirm('Archive this article?')) return
    try {
      await articleService.archive(id)
      await load()
    } catch {}
  }

  const handleDelete = async () => {
    if (!confirm('Delete this article permanently?')) return
    try {
      await articleService.remove(id)
      navigate('/articles')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    try {
      await articleService.uploadAttachment(id, file)
      await load()
      e.target.value = ''
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    }
  }

  const handleDeleteAttachment = async (attachmentId) => {
    if (!confirm('Delete this attachment?')) return
    try {
      await articleService.deleteAttachment(attachmentId)
      await load()
    } catch {}
  }

  const fileIconFor = (name) => {
    const ext = name.split('.').pop()?.toLowerCase()
    if (['pdf'].includes(ext)) return '📕'
    if (['doc', 'docx'].includes(ext)) return '📘'
    if (['xls', 'xlsx'].includes(ext)) return '📗'
    if (['ppt', 'pptx'].includes(ext)) return '📙'
    if (['png', 'jpg', 'jpeg'].includes(ext)) return '🖼️'
    return '📄'
  }

  const formatBytes = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1024 / 1024).toFixed(2) + ' MB'
  }

  if (loading) return <div className="loading">Loading article...</div>
  if (error && !article) return <div className="alert alert-error">{error}</div>
  if (!article) return null

  return (
    <div>
      <Link to="/articles" className="text-sm mb-3" style={{ display: 'inline-block' }}>← Back to articles</Link>

      {error && <div className="alert alert-error mt-2">{error}</div>}
      {success && <div className="alert alert-success mt-2">{success}</div>}

      <div className="article-detail-header">
        <div className="flex items-center gap-2 mb-2" style={{ flexWrap: 'wrap' }}>
          <Badge value={article.status} />
          <span className="text-xs text-muted">v{article.version}</span>
          {article.tags?.map((t) => <span key={t.tag_id} className="tag">#{t.tag_name}</span>)}
        </div>

        <h1 className="article-detail-title">{article.title}</h1>

        {article.summary && (
          <p className="text-muted mb-2" style={{ fontSize: '1rem' }}>{article.summary}</p>
        )}

        <div className="article-detail-meta">
          <span className="article-meta-item">📁 {article.category_name}</span>
          <span className="article-meta-item">✍️ {article.author_name}</span>
          <span className="article-meta-item">👁 {article.view_count} views</span>
          <span className="article-meta-item">📅 {new Date(article.updated_at).toLocaleDateString()}</span>
        </div>

        {article.approval_comments && article.status === 'Rejected' && (
          <div className="alert alert-warning mt-2">
            <strong>Review notes:</strong> {article.approval_comments}
          </div>
        )}

        <div className="article-actions">
          <button onClick={handleBookmark} className={`btn ${bookmarked ? 'btn-warning' : 'btn-secondary'} btn-sm`}>
            {bookmarked ? '★ Bookmarked' : '☆ Bookmark'}
          </button>

          {canEdit && (
            <Link to={`/articles/${id}/edit`} className="btn btn-secondary btn-sm">✎ Edit</Link>
          )}

          {canSubmit && (
            <button onClick={handleSubmitForApproval} className="btn btn-primary btn-sm">
              Submit for Approval
            </button>
          )}

          {canArchive && (
            <button onClick={handleArchive} className="btn btn-secondary btn-sm">Archive</button>
          )}

          {(isAuthor || hasRole('Admin')) && (
            <button onClick={handleDelete} className="btn btn-danger btn-sm">Delete</button>
          )}
        </div>
      </div>

      {canReview && (
        <div className="card mb-4" style={{ borderColor: 'var(--color-warning)', borderLeft: '4px solid var(--color-warning)' }}>
          <h3 className="card-title mb-2">Review this article</h3>
          <textarea
            className="form-textarea"
            placeholder="Comments for the author (optional for approval, recommended for rejection)..."
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
            rows={3}
          />
          <div className="flex gap-2 mt-2">
            <button onClick={() => handleReview('Approved')} className="btn btn-success">✓ Approve</button>
            <button onClick={() => handleReview('Rejected')} className="btn btn-danger">✗ Reject</button>
          </div>
        </div>
      )}

      <div className="col-2-narrow">
        <div>
          <div className="article-content mb-4">{article.content}</div>

          <div className="card mb-4">
            <h3 className="card-title mb-2">💬 Comments ({comments.length})</h3>
            <form onSubmit={handleAddComment} className="mb-4">
              <textarea
                className="form-textarea"
                placeholder="Share your thoughts..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                rows={3}
              />
              <button type="submit" className="btn btn-primary btn-sm mt-2" disabled={!newComment.trim()}>
                Post Comment
              </button>
            </form>

            {comments.length === 0 ? (
              <div className="text-muted text-sm">No comments yet. Be the first!</div>
            ) : (
              comments.map((c) => (
                <div key={c.comment_id} className="comment">
                  <div className="comment-header">
                    <span className="comment-author">{c.user_name}</span>
                    <span className="comment-date">{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                  <div className="comment-text">{c.comment_text}</div>
                  {(c.user_id === user?.user_id || hasRole('Admin')) && (
                    <button
                      onClick={() => handleDeleteComment(c.comment_id)}
                      className="btn btn-sm"
                      style={{ background: 'transparent', color: 'var(--color-danger)', padding: '0.25rem 0', marginTop: '0.5rem' }}
                    >
                      Delete
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div>
          <div className="card mb-4">
            <h3 className="card-title mb-2">⭐ Rating</h3>
            <StarRating value={article.average_rating} count={article.rating_count} readOnly />
            <div className="mt-2 text-sm text-muted">Your rating:</div>
            <StarRating onRate={handleRate} />
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">📎 Attachments ({article.attachments.length})</h3>
            </div>

            {(isAuthor || hasRole('Admin')) && (
              <div className="mb-3">
                <label className="btn btn-secondary btn-sm" style={{ cursor: 'pointer' }}>
                  + Upload file
                  <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
                <div className="text-xs text-muted mt-1">Max 10MB. PDF, DOC, XLS, PPT, PNG, JPG.</div>
              </div>
            )}

            {article.attachments.length === 0 ? (
              <div className="text-muted text-sm">No attachments</div>
            ) : (
              article.attachments.map((a) => (
                <div key={a.attachment_id} className="attachment-item">
                  <div className="attachment-info">
                    <div className="attachment-icon">{fileIconFor(a.file_name)}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="attachment-name">{a.file_name}</div>
                      <div className="attachment-size">{formatBytes(a.file_size)}</div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <a href={articleService.downloadAttachmentUrl(a.attachment_id) + `?token=${localStorage.getItem('kb_token')}`}
                       onClick={async (e) => {
                         e.preventDefault()
                         // Use fetch with auth header for download
                         const res = await fetch(articleService.downloadAttachmentUrl(a.attachment_id), {
                           headers: { Authorization: `Bearer ${localStorage.getItem('kb_token')}` }
                         })
                         const blob = await res.blob()
                         const url = URL.createObjectURL(blob)
                         const link = document.createElement('a')
                         link.href = url
                         link.download = a.file_name
                         link.click()
                         URL.revokeObjectURL(url)
                       }}
                       className="btn btn-secondary btn-sm">⬇</a>
                    {(isAuthor || hasRole('Admin')) && (
                      <button onClick={() => handleDeleteAttachment(a.attachment_id)} className="btn btn-danger btn-sm">×</button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ArticleDetail
