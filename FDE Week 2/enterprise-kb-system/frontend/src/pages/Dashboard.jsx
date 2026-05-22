import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyticsService, articleService } from '../services/apiService'
import ArticleCard from '../components/ArticleCard'
import { useAuth } from '../context/AuthContext'

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [recentArticles, setRecentArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [statsData, analyticsData, articlesData] = await Promise.all([
          analyticsService.dashboard(),
          analyticsService.full(),
          articleService.list({ limit: 6, sort: 'recent' }),
        ])
        setStats(statsData)
        setAnalytics(analyticsData)
        setRecentArticles(articlesData)
      } catch (err) {
        setError('Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className="loading">Loading dashboard...</div>
  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Welcome back, {user?.name?.split(' ')[0]} 👋</h1>
          <p className="page-subtitle">Here's what's happening in your knowledge base</p>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard label="Total Articles" value={stats.total_articles} icon="📚" color="primary" />
        <StatCard label="Approved" value={stats.approved_articles} icon="✓" color="success" />
        <StatCard label="Pending Approval" value={stats.pending_articles} icon="⏳" color="warning" />
        <StatCard label="Drafts" value={stats.draft_articles} icon="📝" color="info" />
        <StatCard label="Total Users" value={stats.total_users} icon="👥" color="primary" />
        <StatCard label="Total Views" value={stats.total_views} icon="👁" color="info" />
      </div>

      <div className="col-2 mb-4">
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Most Viewed</h2>
            <Link to="/articles?sort=popular" className="text-sm">View all →</Link>
          </div>
          {analytics.most_viewed.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <div className="text-muted">No views yet</div>
            </div>
          ) : (
            <ol style={{ listStyle: 'none' }}>
              {analytics.most_viewed.map((a, i) => (
                <li key={a.article_id} style={{ padding: '0.625rem 0', borderBottom: '1px solid var(--color-gray-100)' }}>
                  <Link to={`/articles/${a.article_id}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span><strong style={{ color: 'var(--color-gray-400)' }}>{i + 1}.</strong> {a.title}</span>
                    <span className="text-xs text-muted">{a.view_count} views</span>
                  </Link>
                </li>
              ))}
            </ol>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="card-title">By Category</h2>
            <Link to="/articles" className="text-sm">View all →</Link>
          </div>
          {analytics.by_category.length === 0 ? (
            <div className="empty-state"><div className="text-muted">No categories yet</div></div>
          ) : (
            <ul style={{ listStyle: 'none' }}>
              {analytics.by_category.map((c) => (
                <li key={c.category_id} style={{ padding: '0.625rem 0', borderBottom: '1px solid var(--color-gray-100)', display: 'flex', justifyContent: 'space-between' }}>
                  <Link to={`/articles?category_id=${c.category_id}`}>{c.category_name}</Link>
                  <span className="text-xs text-muted">{c.article_count} article{c.article_count !== 1 ? 's' : ''}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <div className="page-header">
        <h2 className="page-title" style={{ fontSize: '1.25rem' }}>Recent Articles</h2>
        <Link to="/articles" className="btn btn-secondary btn-sm">View all →</Link>
      </div>

      {recentArticles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📄</div>
          <div className="empty-state-title">No articles yet</div>
          <div className="text-muted">Articles will appear here once authors publish them.</div>
        </div>
      ) : (
        <div className="article-grid">
          {recentArticles.map((a) => <ArticleCard key={a.article_id} article={a} />)}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <div className={`stat-card-icon ${color}`}>{icon}</div>
      </div>
      <div className="stat-card-value">{value}</div>
    </div>
  )
}

export default Dashboard
