import { NavLink, Link } from 'react-router-dom'

/**
 * Top navigation bar shown on every page.
 *
 * Uses react-router's NavLink so the active route is automatically
 * highlighted.
 */
function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <div className="navbar-brand-icon">H</div>
          <div>
            <div className="navbar-title">Helpdesk System</div>
            <div className="navbar-subtitle">Ticket Management</div>
          </div>
        </Link>

        <div className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Dashboard
          </NavLink>
          <NavLink to="/tickets" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            All Tickets
          </NavLink>
          <NavLink to="/tickets/new" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Create Ticket
          </NavLink>
          <NavLink to="/search" className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}>
            Search
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => 'nav-link nav-link--analytics' + (isActive ? ' active' : '')}>
            📊 Analytics
          </NavLink>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
