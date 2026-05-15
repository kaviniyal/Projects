import { Link } from 'react-router-dom'
import { StatusBadge, PriorityBadge } from './Badge'

/**
 * Reusable table for displaying a list of tickets.
 *
 * Shown by both the Listing page and the Search page.
 */
function TicketTable({ tickets, onDelete }) {
  if (!tickets || tickets.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">📋</div>
        <div className="empty-state-title">No tickets found</div>
        <div>Try adjusting your filters or create a new ticket.</div>
      </div>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div className="table-wrapper">
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Employee</th>
              <th>Department</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.ticket_id}>
                <td className="table-id">#{ticket.ticket_id}</td>
                <td>{ticket.employee_name}</td>
                <td>{ticket.department}</td>
                <td>{ticket.issue_category}</td>
                <td><PriorityBadge priority={ticket.priority} /></td>
                <td><StatusBadge status={ticket.status} /></td>
                <td>{formatDate(ticket.created_at)}</td>
                <td>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/tickets/${ticket.ticket_id}`} className="btn btn-secondary btn-sm">
                      View
                    </Link>
                    {onDelete && (
                      <button
                        onClick={() => onDelete(ticket.ticket_id)}
                        className="btn btn-danger btn-sm"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default TicketTable
