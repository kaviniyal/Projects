import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { articleService } from '../services/apiService'
import { Badge } from '../components/Common'

function ApprovalQueue() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    articleService
      .pendingApprovals()
      .then(setArticles)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Approval Queue</h1>
          <p className="page-subtitle">Articles waiting for review</p>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✨</div>
          <div className="empty-state-title">Nothing to review</div>
          <div className="text-muted">All caught up! No articles are pending approval.</div>
        </div>
      ) : (
        <div className="table-wrapper">
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Category</th>
                  <th>Submitted</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {articles.map((a) => (
                  <tr key={a.article_id}>
                    <td className="table-id">#{a.article_id}</td>
                    <td>
                      <Link to={`/articles/${a.article_id}`}><strong>{a.title}</strong></Link>
                      <div className="text-xs text-muted">v{a.version}</div>
                    </td>
                    <td>{a.author_name}</td>
                    <td><Badge value={a.category_name} type="role" /></td>
                    <td className="text-sm">{new Date(a.updated_at).toLocaleString()}</td>
                    <td>
                      <Link to={`/articles/${a.article_id}`} className="btn btn-primary btn-sm">
                        Review →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default ApprovalQueue
