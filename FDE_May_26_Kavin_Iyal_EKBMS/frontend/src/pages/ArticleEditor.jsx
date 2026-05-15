import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { articleService, categoryService } from '../services/apiService'

function ArticleEditor() {
  const { id } = useParams()
  const isEdit = !!id
  const navigate = useNavigate()

  const [form, setForm] = useState({
    title: '',
    summary: '',
    content: '',
    category_id: '',
    tag_names: '',
  })
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const cats = await categoryService.list()
        setCategories(cats)
        if (isEdit) {
          const a = await articleService.get(id)
          setForm({
            title: a.title,
            summary: a.summary || '',
            content: a.content,
            category_id: a.category_id,
            tag_names: a.tags.map((t) => t.tag_name).join(', '),
          })
        } else if (cats.length) {
          setForm((f) => ({ ...f, category_id: cats[0].category_id }))
        }
      } catch (err) {
        setError('Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, isEdit])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    try {
      const payload = {
        title: form.title,
        summary: form.summary || null,
        content: form.content,
        category_id: Number(form.category_id),
        tag_names: form.tag_names.split(',').map((t) => t.trim()).filter(Boolean),
      }
      let saved
      if (isEdit) {
        saved = await articleService.update(id, payload)
      } else {
        saved = await articleService.create(payload)
      }
      navigate(`/articles/${saved.article_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">{isEdit ? 'Edit Article' : 'New Article'}</h1>
          <p className="page-subtitle">{isEdit ? 'Update your article' : 'Create a new knowledge article'}</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <form onSubmit={handleSubmit} className="card">
        <div className="form-group">
          <label className="form-label">Title <span className="required">*</span></label>
          <input
            type="text"
            className="form-input"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
            minLength={3}
            placeholder="e.g. How to Connect to the Corporate VPN"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Summary</label>
          <input
            type="text"
            className="form-input"
            value={form.summary}
            onChange={(e) => setForm({ ...form, summary: e.target.value })}
            placeholder="A short one-line summary that appears in lists"
            maxLength={500}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Category <span className="required">*</span></label>
            <select
              className="form-select"
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
              required
            >
              {categories.map((c) => (
                <option key={c.category_id} value={c.category_id}>{c.category_name}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Tags</label>
            <input
              type="text"
              className="form-input"
              value={form.tag_names}
              onChange={(e) => setForm({ ...form, tag_names: e.target.value })}
              placeholder="vpn, networking, remote (comma-separated)"
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Content <span className="required">*</span></label>
          <textarea
            className="form-textarea"
            value={form.content}
            onChange={(e) => setForm({ ...form, content: e.target.value })}
            rows={20}
            required
            minLength={10}
            placeholder="Write the full article content here..."
          />
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate(-1)} className="btn btn-secondary">Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Article')}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ArticleEditor
