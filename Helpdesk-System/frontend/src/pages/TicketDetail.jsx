import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ticketService, STATUSES, PRIORITIES, CATEGORIES } from '../services/ticketService'
import { StatusBadge, PriorityBadge } from '../components/Badge'

/**
 * Ticket detail / edit page.
 *
 * Two modes are toggled by the `editMode` flag:
 *   - read-only view of the ticket
 *   - inline edit form
 */
function TicketDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editMode, setEditMode] = useState(false)
  const [editData, setEditData] = useState({})
  const [saving, setSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState(null)

  useEffect(() => {
    loadTicket()
  }, [id])

  const loadTicket = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await ticketService.getTicketById(id)
      setTicket(data)
      setEditData({
        employee_name: data.employee_name,
        department: data.department,
        issue_category: data.issue_category,
        description: data.description,
        priority: data.priority,
        status: data.status,
        resolution_notes: data.resolution_notes || '',
      })
    } catch (err) {
      console.error('Load ticket error:', err)
      if (err.response?.status === 404) {
        setError(`Ticket #${id} not found.`)
      } else {
        setError('Failed to load ticket details.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleEditChange = (e) => {
    const { name, value } = e.target
    setEditData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const updated = await ticketService.updateTicket(id, editData)
      setTicket(updated)
      setEditMode(false)
      setSuccessMessage('Ticket updated successfully.')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      console.error('Update error:', err)
      setError(err.response?.data?.detail || 'Failed to update ticket.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete ticket #${id}?`)) return
    try {
      await ticketService.deleteTicket(id)
      navigate('/tickets')
    } catch (err) {
      console.error('Delete error:', err)
      setError('Failed to delete ticket.')
    }
  }

  if (loading) return <div className="loading">Loading ticket details...</div>

  if (error && !ticket) {
    return (
      <div>
        <div className="alert alert-error">{error}</div>
        <Link to="/tickets" className="btn btn-secondary">← Back to Tickets</Link>
      </div>
    )
  }

  if (!ticket) return null

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Ticket #{ticket.ticket_id}</h1>
          <p className="page-subtitle">Created on {formatDate(ticket.created_at)}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Link to="/tickets" className="btn btn-secondary">← Back</Link>
          {!editMode && (
            <>
              <button onClick={() => setEditMode(true)} className="btn btn-primary">
                Edit
              </button>
              <button onClick={handleDelete} className="btn btn-danger">Delete</button>
            </>
          )}
        </div>
      </div>

      {successMessage && <div className="alert alert-success">{successMessage}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      {editMode ? (
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '1.5rem' }}>Edit Ticket</h3>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Employee Name</label>
              <input
                type="text"
                name="employee_name"
                className="form-input"
                value={editData.employee_name}
                onChange={handleEditChange}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Department</label>
              <input
                type="text"
                name="department"
                className="form-input"
                value={editData.department}
                onChange={handleEditChange}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Category</label>
              <select
                name="issue_category"
                className="form-select"
                value={editData.issue_category}
                onChange={handleEditChange}
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Priority</label>
              <select
                name="priority"
                className="form-select"
                value={editData.priority}
                onChange={handleEditChange}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Status</label>
            <select
              name="status"
              className="form-select"
              value={editData.status}
              onChange={handleEditChange}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              name="description"
              className="form-textarea"
              value={editData.description}
              onChange={handleEditChange}
              rows={4}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Resolution Notes</label>
            <textarea
              name="resolution_notes"
              className="form-textarea"
              value={editData.resolution_notes}
              onChange={handleEditChange}
              placeholder="Add resolution notes when working on or closing the ticket..."
              rows={4}
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setEditMode(false)
                loadTicket()
              }}
              disabled={saving}
            >
              Cancel
            </button>
            <button onClick={handleSave} className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      ) : (
        <div className="detail-grid">
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem' }}>Issue Description</h3>
            <div className="description-box">{ticket.description}</div>

            {ticket.resolution_notes && (
              <>
                <h3 className="card-title" style={{ marginTop: '1.5rem', marginBottom: '1rem' }}>
                  Resolution Notes
                </h3>
                <div className="description-box">{ticket.resolution_notes}</div>
              </>
            )}
          </div>

          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '1rem' }}>Ticket Information</h3>

            <div className="detail-row">
              <span className="detail-label">Status</span>
              <span className="detail-value"><StatusBadge status={ticket.status} /></span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Priority</span>
              <span className="detail-value"><PriorityBadge priority={ticket.priority} /></span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Category</span>
              <span className="detail-value">{ticket.issue_category}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Employee</span>
              <span className="detail-value">{ticket.employee_name}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Department</span>
              <span className="detail-value">{ticket.department}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Created</span>
              <span className="detail-value" style={{ fontSize: '0.8125rem' }}>
                {formatDate(ticket.created_at)}
              </span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Last Updated</span>
              <span className="detail-value" style={{ fontSize: '0.8125rem' }}>
                {formatDate(ticket.updated_at)}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TicketDetail
