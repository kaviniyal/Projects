import { useEffect, useState } from 'react'
import { userService } from '../services/apiService'
import { Badge } from '../components/Common'
import { useAuth } from '../context/AuthContext'

function UserManagement() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = () => {
    userService
      .list()
      .then(setUsers)
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleRoleChange = async (userId, newRole) => {
    try {
      await userService.update(userId, { role: newRole })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  const handleToggleActive = async (u) => {
    try {
      await userService.update(u.user_id, { is_active: !u.is_active })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  const handleDelete = async (u) => {
    if (!confirm(`Delete user "${u.name}"?`)) return
    try {
      await userService.remove(u.user_id)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed')
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">Manage users and roles</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div className="table-wrapper">
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Email</th><th>Department</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.user_id}>
                    <td className="table-id">#{u.user_id}</td>
                    <td><strong>{u.name}</strong>{u.user_id === currentUser?.user_id && <span className="text-xs text-muted"> (you)</span>}</td>
                    <td className="text-sm">{u.email}</td>
                    <td className="text-sm">{u.department || '—'}</td>
                    <td>
                      <select
                        className="form-select"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.8125rem' }}
                        value={u.role_name}
                        onChange={(e) => handleRoleChange(u.user_id, e.target.value)}
                        disabled={u.user_id === currentUser?.user_id}
                      >
                        <option value="Admin">Admin</option>
                        <option value="Author">Author</option>
                        <option value="Reviewer">Reviewer</option>
                        <option value="Employee">Employee</option>
                      </select>
                    </td>
                    <td>
                      {u.is_active ? <Badge value="Approved" /> : <Badge value="Archived" />}
                    </td>
                    <td className="text-sm">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="flex gap-1">
                        {u.user_id !== currentUser?.user_id && (
                          <>
                            <button onClick={() => handleToggleActive(u)} className="btn btn-secondary btn-sm">
                              {u.is_active ? 'Disable' : 'Enable'}
                            </button>
                            <button onClick={() => handleDelete(u)} className="btn btn-danger btn-sm">Delete</button>
                          </>
                        )}
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

export default UserManagement
