import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ticketService } from '../services/ticketService'
import { StatusBadge, PriorityBadge } from '../components/Badge'

/**
 * Dashboard / home page.
 *
 * Shows aggregate ticket counts and the five most recent tickets.
 * Loads summary + recent tickets in parallel on mount.
 */
function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [recentTickets, setRecentTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Two independent calls — issue them in parallel.
      const [summaryData, ticketsData] = await Promise.all([
        ticketService.getSummary(),
        ticketService.getAllTickets(),
      ])
      setSummary(summaryData)
      setRecentTickets(ticketsData.slice(0, 5))
    } catch (err) {
      console.error('Dashboard load error:', err)
      setError('Failed to load dashboard data. Please check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading dashboard...</div>
  if (error) return <div className="alert alert-error">{error}</div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of your helpdesk tickets</p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary">+ New Ticket</Link>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Total Tickets"
          value={summary?.total_tickets || 0}
          icon="📋"
          color="primary"
        />
        <StatCard
          label="Open"
          value={summary?.open_tickets || 0}
          icon="🔵"
          color="info"
        />
        <StatCard
          label="In Progress"
          value={summary?.in_progress_tickets || 0}
          icon="⚡"
          color="warning"
        />
        <StatCard
          label="Resolved"
          value={summary?.resolved_tickets || 0}
          icon="✓"
          color="success"
        />
        <StatCard
          label="Closed"
          value={summary?.closed_tickets || 0}
          icon="🔒"
          color="primary"
        />
        <StatCard
          label="Critical / High"
          value={(summary?.critical_priority || 0) + (summary?.high_priority || 0)}
          icon="🔥"
          color="danger"
        />
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title">Recent Tickets</div>
          <Link to="/tickets" className="btn btn-secondary btn-sm">View All</Link>
        </div>

        {recentTickets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <div className="empty-state-title">No tickets yet</div>
            <div>Create your first ticket to get started.</div>
          </div>
        ) : (
          <div>
            {recentTickets.map((ticket) => (
              <Link
                key={ticket.ticket_id}
                to={`/tickets/${ticket.ticket_id}`}
                className="recent-ticket-item"
              >
                <div className="table-id">#{ticket.ticket_id}</div>
                <div className="recent-ticket-info">
                  <div className="recent-ticket-title">
                    {ticket.issue_category} — {ticket.employee_name}
                  </div>
                  <div className="recent-ticket-meta">
                    {ticket.department} · {new Date(ticket.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <PriorityBadge priority={ticket.priority} />
                  <StatusBadge status={ticket.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, icon, color }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <div className="stat-card-label">{label}</div>
        <div className={`stat-card-icon ${color}`}>{icon}</div>
      </div>
      <div className="stat-card-value">{value}</div>
    </div>
  )
}

export default Dashboard
