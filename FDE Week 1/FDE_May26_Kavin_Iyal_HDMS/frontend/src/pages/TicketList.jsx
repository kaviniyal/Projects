import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ticketService } from '../services/ticketService'
import TicketTable from '../components/TicketTable'
import FilterBar from '../components/FilterBar'

/**
 * Ticket listing page.
 *
 * Loads tickets whenever the filter object changes. A fresh request to
 * the backend is used (rather than client-side filtering) so the same
 * filters can be passed straight through as query parameters.
 */
function TicketList() {
  const [tickets, setTickets] = useState([])
  const [filters, setFilters] = useState({ status: '', category: '', priority: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  useEffect(() => {
    loadTickets()
  }, [filters])

  const loadTickets = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await ticketService.getAllTickets(filters)
      setTickets(data)
    } catch (err) {
      console.error('Load tickets error:', err)
      setError('Failed to load tickets. Please check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    // Browser `confirm` is the most lightweight option for Phase 1.
    if (!window.confirm(`Are you sure you want to delete ticket #${id}?`)) return
    try {
      await ticketService.deleteTicket(id)
      setSuccessMessage(`Ticket #${id} deleted successfully.`)
      setTimeout(() => setSuccessMessage(null), 3000)
      loadTickets()
    } catch (err) {
      console.error('Delete error:', err)
      setError('Failed to delete ticket.')
    }
  }

  const handleReset = () => {
    setFilters({ status: '', category: '', priority: '' })
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">All Tickets</h1>
          <p className="page-subtitle">
            {loading ? 'Loading...' : `${tickets.length} ticket${tickets.length === 1 ? '' : 's'} found`}
          </p>
        </div>
        <Link to="/tickets/new" className="btn btn-primary">+ New Ticket</Link>
      </div>

      {successMessage && <div className="alert alert-success">{successMessage}</div>}
      {error && <div className="alert alert-error">{error}</div>}

      <FilterBar filters={filters} onFilterChange={setFilters} onReset={handleReset} />

      {loading ? (
        <div className="loading">Loading tickets...</div>
      ) : (
        <TicketTable tickets={tickets} onDelete={handleDelete} />
      )}
    </div>
  )
}

export default TicketList
