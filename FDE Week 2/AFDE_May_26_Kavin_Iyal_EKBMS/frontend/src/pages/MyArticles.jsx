import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { articleService } from '../services/apiService'
import ArticleCard from '../components/ArticleCard'

function MyArticles() {
  const [articles, setArticles] = useState([])
  const [tab, setTab] = useState('All')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    articleService
      .myArticles()
      .then(setArticles)
      .finally(() => setLoading(false))
  }, [])

  const tabs = ['All', 'Draft', 'Pending Approval', 'Approved', 'Rejected', 'Archived']
  const filtered = tab === 'All' ? articles : articles.filter((a) => a.status === tab)

  const counts = articles.reduce((acc, a) => {
    acc[a.status] = (acc[a.status] || 0) + 1
    return acc
  }, {})

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">My Articles</h1>
          <p className="page-subtitle">All articles you've authored</p>
        </div>
        <Link to="/articles/new" className="btn btn-primary">+ New Article</Link>
      </div>

      <div className="tabs">
        {tabs.map((t) => (
          <button key={t} className={`tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
            {t} {t !== 'All' && counts[t] ? <span className="text-xs">({counts[t]})</span> : ''}
            {t === 'All' && <span className="text-xs"> ({articles.length})</span>}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✍️</div>
          <div className="empty-state-title">No articles in this view</div>
          <div className="text-muted mb-3">Start writing and share your knowledge</div>
          <Link to="/articles/new" className="btn btn-primary">+ New Article</Link>
        </div>
      ) : (
        <div className="article-grid">
          {filtered.map((a) => <ArticleCard key={a.article_id} article={a} />)}
        </div>
      )}
    </div>
  )
}

export default MyArticles
