import { useEffect, useState } from 'react'
import { categoryService } from '../services/apiService'

function CategoryManagement() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState({ category_name: '', description: '', parent_id: '' })
  const [error, setError] = useState('')

  const load = () => {
    categoryService
      .list()
      .then(setCategories)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const openCreate = () => {
    setEditing(null)
    setForm({ category_name: '', description: '', parent_id: '' })
    setShowForm(true)
    setError('')
  }

  const openEdit = (c) => {
    setEditing(c)
    setForm({
      category_name: c.category_name,
      description: c.description || '',
      parent_id: c.parent_id || '',
    })
    setShowForm(true)
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const payload = {
        category_name: form.category_name,
        description: form.description || null,
        parent_id: form.parent_id ? Number(form.parent_id) : null,
      }
      if (editing) {
        await categoryService.update(editing.category_id, payload)
      } else {
        await categoryService.create(payload)
      }
      setShowForm(false)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    }
  }

  const handleDelete = async (c) => {
    if (!confirm(`Delete "${c.category_name}"?`)) return
    try {
      await categoryService.remove(c.category_id)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Delete failed')
    }
  }

  const categoryName = (id) => categories.find((c) => c.category_id === id)?.category_name

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Category Management</h1>
          <p className="page-subtitle">Organize knowledge into categories</p>
        </div>
        <button onClick={openCreate} className="btn btn-primary">+ New Category</button>
      </div>

      {showForm && (
        <div className="card mb-4">
          <h3 className="card-title mb-3">{editing ? 'Edit Category' : 'New Category'}</h3>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Name <span className="required">*</span></label>
              <input type="text" className="form-input" value={form.category_name}
                     onChange={(e) => setForm({ ...form, category_name: e.target.value })} required />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <input type="text" className="form-input" value={form.description}
                     onChange={(e) => setForm({ ...form, description: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Parent Category (optional)</label>
              <select className="form-select" value={form.parent_id}
                      onChange={(e) => setForm({ ...form, parent_id: e.target.value })}>
                <option value="">None (top-level)</option>
                {categories.filter((c) => !editing || c.category_id !== editing.category_id).map((c) => (
                  <option key={c.category_id} value={c.category_id}>{c.category_name}</option>
                ))}
              </select>
            </div>
            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">{editing ? 'Save' : 'Create'}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div className="table-wrapper">
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Description</th><th>Parent</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {categories.map((c) => (
                  <tr key={c.category_id}>
                    <td className="table-id">#{c.category_id}</td>
                    <td><strong>{c.category_name}</strong></td>
                    <td className="text-sm text-muted">{c.description || '—'}</td>
                    <td className="text-sm">{c.parent_id ? categoryName(c.parent_id) : '—'}</td>
                    <td>
                      <div className="flex gap-1">
                        <button onClick={() => openEdit(c)} className="btn btn-secondary btn-sm">Edit</button>
                        <button onClick={() => handleDelete(c)} className="btn btn-danger btn-sm">Delete</button>
                      </div>
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

export default CategoryManagement
