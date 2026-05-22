import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { articleService, categoryService } from '../services/apiService'
import ArticleCard from '../components/ArticleCard'
import { useAuth } from '../context/AuthContext'

function ArticleList() {
  const { hasRole } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [articles, setArticles] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  const status = searchParams.get('status') || ''
  const categoryId = searchParams.get('category_id') || ''
  const sort = searchParams.get('sort') || 'recent'

  useEffect(() => {
    categoryService.list().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = {}
    if (status) params.status = status
    if (categoryId) params.category_id = categoryId
    if (sort) params.sort = sort

    articleService
      .list(params)
      .then(setArticles)
      .catch(() => setArticles([]))
      .finally(() => setLoading(false))
  }, [status, categoryId, sort])

  const updateFilter = (key, value) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next)
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Browse Articles</h1>
          <p className="page-subtitle">All approved articles in your knowledge base</p>
        </div>
        {hasRole('Author', 'Admin') && (
          <Link to="/articles/new" className="btn btn-primary">+ New Article</Link>
        )}
      </div>

      <div className="filters-bar">
        <div className="filter-field">
          <label>Category</label>
          <select className="form-select" value={categoryId} onChange={(e) => updateFilter('category_id', e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
          </select>
        </div>

        {hasRole('Author', 'Reviewer', 'Admin') && (
          <div className="filter-field">
            <label>Status</label>
            <select className="form-select" value={status} onChange={(e) => updateFilter('status', e.target.value)}>
              <option value="">All</option>
              <option value="Draft">Draft</option>
              <option value="Pending Approval">Pending</option>
              <option value="Approved">Approved</option>
              <option value="Rejected">Rejected</option>
              <option value="Archived">Archived</option>
            </select>
          </div>
        )}

        <div className="filter-field">
          <label>Sort</label>
          <select className="form-select" value={sort} onChange={(e) => updateFilter('sort', e.target.value)}>
            <option value="recent">Most Recent</option>
            <option value="popular">Most Viewed</option>
            <option value="rating">Top Rated</option>
          </select>
        </div>

        <div className="filter-field"></div>

        <button className="btn btn-secondary btn-sm" onClick={() => setSearchParams({})}>
          Clear
        </button>
      </div>

      {loading ? (
        <div className="loading">Loading articles...</div>
      ) : articles.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📄</div>
          <div className="empty-state-title">No articles found</div>
          <div className="text-muted">Try adjusting your filters</div>
        </div>
      ) : (
        <div className="article-grid">
          {articles.map((a) => <ArticleCard key={a.article_id} article={a} />)}
        </div>
      )}
    </div>
  )
}

export default ArticleList
