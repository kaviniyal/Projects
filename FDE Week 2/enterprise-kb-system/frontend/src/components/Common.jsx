import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Route guard. Redirects to /login if the user isn't authenticated.
 * Optionally restricts access to specific roles.
 */
export function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, hasRole, loading } = useAuth()

  if (loading) return <div className="loading">Loading...</div>

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (roles && !hasRole(...roles)) {
    return (
      <div className="main-content">
        <div className="alert alert-error">
          You don't have permission to access this page.
        </div>
      </div>
    )
  }

  return children
}

/**
 * Generic status / role badge. CSS class is derived from the value.
 */
export function Badge({ value, type = 'status' }) {
  const slug = value.toLowerCase().replace(/\s+/g, '-')
  return <span className={`badge badge-${slug}`}>{value}</span>
}

/**
 * 5-star rating widget.
 *  - readOnly: render just the stars
 *  - onRate(value): when clicked
 */
export function StarRating({ value = 0, count = 0, onRate, readOnly = false }) {
  const rounded = Math.round(value || 0)
  const stars = [1, 2, 3, 4, 5]
  return (
    <span className="flex items-center gap-2">
      <span className="stars">
        {stars.map((s) => (
          <button
            key={s}
            type="button"
            className={`star ${s <= rounded ? 'filled' : ''} ${onRate ? 'interactive' : ''}`}
            onClick={() => onRate && !readOnly && onRate(s)}
            disabled={readOnly || !onRate}
            aria-label={`${s} star${s === 1 ? '' : 's'}`}
          >
            ★
          </button>
        ))}
      </span>
      {count > 0 && (
        <span className="text-xs text-muted">
          {value?.toFixed(1) || '0.0'} ({count})
        </span>
      )}
    </span>
  )
}
