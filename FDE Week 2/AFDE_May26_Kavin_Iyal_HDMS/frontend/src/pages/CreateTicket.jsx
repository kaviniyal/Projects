import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ticketService,
  CATEGORIES,
  PRIORITIES,
} from '../services/ticketService'

/**
 * Create-ticket page.
 *
 * Performs client-side validation before POSTing to the backend so the
 * user gets immediate feedback on obvious mistakes.
 */
function CreateTicket() {
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    employee_name: '',
    department: '',
    issue_category: '',
    description: '',
    priority: 'Medium',
  })

  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    // Clear the field-level error as soon as the user starts fixing it.
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: null }))
    }
  }

  const validate = () => {
    const newErrors = {}

    if (!formData.employee_name.trim()) {
      newErrors.employee_name = 'Employee name is required'
    } else if (formData.employee_name.trim().length < 2) {
      newErrors.employee_name = 'Employee name must be at least 2 characters'
    }

    if (!formData.department.trim()) {
      newErrors.department = 'Department is required'
    }

    if (!formData.issue_category) {
      newErrors.issue_category = 'Please select an issue category'
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    } else if (formData.description.trim().length < 5) {
      newErrors.description = 'Description must be at least 5 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setServerError(null)

    if (!validate()) return

    setSubmitting(true)
    try {
      const ticket = await ticketService.createTicket(formData)
      navigate(`/tickets/${ticket.ticket_id}`)
    } catch (err) {
      console.error('Create ticket error:', err)
      setServerError(
        err.response?.data?.detail ||
          'Failed to create ticket. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Create New Ticket</h1>
          <p className="page-subtitle">Submit a new support request</p>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 800 }}>
        {serverError && <div className="alert alert-error">{serverError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                Employee Name<span className="required">*</span>
              </label>
              <input
                type="text"
                name="employee_name"
                className={`form-input ${errors.employee_name ? 'error' : ''}`}
                value={formData.employee_name}
                onChange={handleChange}
                placeholder="e.g., John Doe"
              />
              {errors.employee_name && (
                <div className="form-error">{errors.employee_name}</div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Department<span className="required">*</span>
              </label>
              <input
                type="text"
                name="department"
                className={`form-input ${errors.department ? 'error' : ''}`}
                value={formData.department}
                onChange={handleChange}
                placeholder="e.g., Engineering"
              />
              {errors.department && (
                <div className="form-error">{errors.department}</div>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">
                Issue Category<span className="required">*</span>
              </label>
              <select
                name="issue_category"
                className={`form-select ${errors.issue_category ? 'error' : ''}`}
                value={formData.issue_category}
                onChange={handleChange}
              >
                <option value="">Select a category...</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              {errors.issue_category && (
                <div className="form-error">{errors.issue_category}</div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Priority<span className="required">*</span>
              </label>
              <select
                name="priority"
                className="form-select"
                value={formData.priority}
                onChange={handleChange}
              >
                {PRIORITIES.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">
              Description<span className="required">*</span>
            </label>
            <textarea
              name="description"
              className={`form-textarea ${errors.description ? 'error' : ''}`}
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the issue in detail..."
              rows={5}
            />
            {errors.description && (
              <div className="form-error">{errors.description}</div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate('/tickets')}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CreateTicket
