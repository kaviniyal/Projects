import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { articleService } from '../services/apiService'
import ArticleCard from '../components/ArticleCard'

function Bookmarks() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    articleService
      .myBookmarks()
      .then(setArticles)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">★ Bookmarks</h1>
          <p className="page-subtitle">Articles you've saved for quick access</p>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⭐</div>
          <div className="empty-state-title">No bookmarks yet</div>
          <div className="text-muted mb-3">Bookmark articles to quickly come back to them later.</div>
          <Link to="/articles" className="btn btn-primary">Browse articles</Link>
        </div>
      ) : (
        <div className="article-grid">
          {articles.map((a) => <ArticleCard key={a.article_id} article={a} />)}
        </div>
      )}
    </div>
  )
}

export default Bookmarks
