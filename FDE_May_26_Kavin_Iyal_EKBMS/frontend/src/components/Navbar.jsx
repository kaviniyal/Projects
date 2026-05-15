import { NavLink, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * Top navigation bar. Different links visible based on user role.
 */
function Navbar() {
  const { user, logout, hasRole } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const initials = (user?.name || '?')
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <div className="navbar-brand-icon">KB</div>
          <div>
            <div className="navbar-title">Knowledge Base</div>
            <div className="navbar-subtitle">Enterprise Edition</div>
          </div>
        </Link>

        <div className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/articles" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Browse
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Search
          </NavLink>
          <NavLink to="/bookmarks" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Bookmarks
          </NavLink>

          {hasRole('Author', 'Admin') && (
            <NavLink to="/my-articles" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
              My Articles
            </NavLink>
          )}

          {hasRole('Reviewer', 'Admin') && (
            <NavLink to="/approvals" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
              Approvals
            </NavLink>
          )}

          {hasRole('Admin') && (
            <>
              <NavLink to="/categories" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
                Categories
              </NavLink>
              <NavLink to="/users" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
                Users
              </NavLink>
            </>
          )}
        </div>

        <div className="navbar-user">
          <div className="user-avatar">{initials}</div>
          <div className="user-info">
            <div className="user-name">{user?.name}</div>
            <div className="user-role">{user?.role_name}</div>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary btn-sm">
            Logout
          </button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
