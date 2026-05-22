import { useEffect, useState } from 'react'
import { articleService, categoryService, tagService } from '../services/apiService'
import ArticleCard from '../components/ArticleCard'

function SearchPage() {
  const [q, setQ] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [tag, setTag] = useState('')
  const [sort, setSort] = useState('recent')
  const [results, setResults] = useState([])
  const [categories, setCategories] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  useEffect(() => {
    categoryService.list().then(setCategories).catch(() => {})
    tagService.list().then(setTags).catch(() => {})
  }, [])

  const doSearch = async (e) => {
    if (e) e.preventDefault()
    setLoading(true)
    setSearched(true)
    try {
      const params = {}
      if (q) params.q = q
      if (categoryId) params.category_id = categoryId
      if (tag) params.tag = tag
      params.sort = sort
      const data = await articleService.search(params)
      setResults(data)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Search Articles</h1>
          <p className="page-subtitle">Find what you're looking for across the knowledge base</p>
        </div>
      </div>

      <form onSubmit={doSearch} className="card mb-4">
        <div className="form-group">
          <label className="form-label">Search keyword</label>
          <input
            type="text"
            className="form-input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="e.g. VPN setup, password reset, leave policy..."
            autoFocus
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Category</label>
            <select className="form-select" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
              <option value="">All</option>
              {categories.map((c) => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Tag</label>
            <select className="form-select" value={tag} onChange={(e) => setTag(e.target.value)}>
              <option value="">Any</option>
              {tags.map((t) => <option key={t.tag_id} value={t.tag_name}>#{t.tag_name}</option>)}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Sort by</label>
            <select className="form-select" value={sort} onChange={(e) => setSort(e.target.value)}>
              <option value="recent">Most Recent</option>
              <option value="popular">Most Viewed</option>
            </select>
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button type="submit" className="btn btn-primary btn-block">
              🔍 Search
            </button>
          </div>
        </div>
      </form>

      {loading ? (
        <div className="loading">Searching...</div>
      ) : !searched ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-title">Start searching</div>
          <div className="text-muted">Enter a keyword above or filter by category/tag</div>
        </div>
      ) : results.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">😕</div>
          <div className="empty-state-title">No results</div>
          <div className="text-muted">Try different keywords or remove filters</div>
        </div>
      ) : (
        <>
          <div className="text-sm text-muted mb-3">{results.length} result{results.length !== 1 ? 's' : ''}</div>
          <div className="article-grid">
            {results.map((a) => <ArticleCard key={a.article_id} article={a} />)}
          </div>
        </>
      )}
    </div>
  )
}

export default SearchPage
