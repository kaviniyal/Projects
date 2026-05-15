import { useEffect, useState } from 'react'
import { ticketService } from '../services/ticketService'
import TicketTable from '../components/TicketTable'
import FilterBar from '../components/FilterBar'

/**
 * Search page.
 *
 * Debounces the keyword input by 400 ms so the backend isn't hit on
 * every keystroke. Filter dropdowns trigger an immediate refetch.
 */
function SearchTickets() {
  const [filters, setFilters] = useState({
    keyword: '',
    status: '',
    category: '',
    priority: '',
  })
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)

  // Debounce the keyword so the backend isn't hit on every keystroke.
  useEffect(() => {
    const timer = setTimeout(() => {
      handleSearch()
    }, 400)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters])

  const handleSearch = async () => {
    // Skip the call until the user has typed something or set a filter
    if (
      !filters.keyword &&
      !filters.status &&
      !filters.category &&
      !filters.priority
    ) {
      setTickets([])
      setHasSearched(false)
      return
    }

    setLoading(true)
    setError(null)
    setHasSearched(true)
    try {
      const data = await ticketService.searchTickets(filters)
      setTickets(data)
    } catch (err) {
      console.error('Search error:', err)
      setError('Search failed. Please check that the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(`Are you sure you want to delete ticket #${id}?`)) return
    try {
      await ticketService.deleteTicket(id)
      handleSearch()
    } catch (err) {
      console.error('Delete error:', err)
      setError('Failed to delete ticket.')
    }
  }

  const handleReset = () => {
    setFilters({ keyword: '', status: '', category: '', priority: '' })
    setTickets([])
    setHasSearched(false)
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Search Tickets</h1>
          <p className="page-subtitle">
            Find tickets by keyword, status, category, or priority
          </p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        onReset={handleReset}
        showKeyword={true}
      />

      {loading ? (
        <div className="loading">Searching...</div>
      ) : hasSearched ? (
        <>
          <p style={{ marginBottom: '1rem', color: 'var(--color-gray-500)' }}>
            {tickets.length} result{tickets.length === 1 ? '' : 's'} found
          </p>
          <TicketTable tickets={tickets} onDelete={handleDelete} />
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-title">Start Searching</div>
          <div>Enter a keyword or select a filter to find tickets.</div>
        </div>
      )}
    </div>
  )
}

export default SearchTickets
