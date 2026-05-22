import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    department: '',
    role: 'Employee',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="auth-logo-icon">KB</div>
        </div>
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Join your team's knowledge base</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name <span className="required">*</span></label>
            <input type="text" name="name" className="form-input" value={form.name} onChange={handleChange} required minLength={2} />
          </div>

          <div className="form-group">
            <label className="form-label">Email <span className="required">*</span></label>
            <input type="email" name="email" className="form-input" value={form.email} onChange={handleChange} required />
          </div>

          <div className="form-group">
            <label className="form-label">Password <span className="required">*</span></label>
            <input type="password" name="password" className="form-input" value={form.password} onChange={handleChange} required minLength={6} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Department</label>
              <input type="text" name="department" className="form-input" value={form.department} onChange={handleChange} placeholder="e.g. Engineering" />
            </div>
            <div className="form-group">
              <label className="form-label">Role</label>
              <select name="role" className="form-select" value={form.role} onChange={handleChange}>
                <option value="Employee">Employee</option>
                <option value="Author">Author</option>
                <option value="Reviewer">Reviewer</option>
                <option value="Admin">Admin</option>
              </select>
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={loading}>
            {loading ? 'Creating account...' : 'Create account'}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  )
}

export default Register
