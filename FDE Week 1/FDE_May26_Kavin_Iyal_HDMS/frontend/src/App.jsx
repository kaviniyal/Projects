import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CreateTicket from './pages/CreateTicket'
import TicketList from './pages/TicketList'
import TicketDetail from './pages/TicketDetail'
import SearchTickets from './pages/SearchTickets'

/**
 * Application root.
 *
 * Mounts the navbar and registers every route. The catch-all redirects
 * unknown URLs to the dashboard.
 */
function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tickets" element={<TicketList />} />
          <Route path="/tickets/new" element={<CreateTicket />} />
          <Route path="/tickets/:id" element={<TicketDetail />} />
          <Route path="/search" element={<SearchTickets />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
