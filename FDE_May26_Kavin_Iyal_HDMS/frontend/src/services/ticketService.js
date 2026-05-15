/**
 * Service layer wrapping every ticket-related API call.
 *
 * Components import these functions instead of calling axios directly,
 * which keeps API plumbing out of the UI code.
 */
import api from '../api'

export const ticketService = {
  // Retrieve all tickets, optionally filtered
  getAllTickets: async (filters = {}) => {
    const params = new URLSearchParams()
    if (filters.status) params.append('status', filters.status)
    if (filters.category) params.append('category', filters.category)
    if (filters.priority) params.append('priority', filters.priority)
    const queryString = params.toString()
    const url = queryString ? `/tickets?${queryString}` : '/tickets'
    const response = await api.get(url)
    return response.data
  },

  // Retrieve a single ticket by ID
  getTicketById: async (id) => {
    const response = await api.get(`/tickets/${id}`)
    return response.data
  },

  // Create a new ticket
  createTicket: async (ticketData) => {
    const response = await api.post('/tickets', ticketData)
    return response.data
  },

  // Update an existing ticket
  updateTicket: async (id, ticketData) => {
    const response = await api.put(`/tickets/${id}`, ticketData)
    return response.data
  },

  // Delete a ticket
  deleteTicket: async (id) => {
    const response = await api.delete(`/tickets/${id}`)
    return response.data
  },

  // Free-text search with optional filters
  searchTickets: async (searchParams) => {
    const params = new URLSearchParams()
    if (searchParams.keyword) params.append('keyword', searchParams.keyword)
    if (searchParams.status) params.append('status', searchParams.status)
    if (searchParams.category) params.append('category', searchParams.category)
    if (searchParams.priority) params.append('priority', searchParams.priority)
    const response = await api.get(`/search?${params.toString()}`)
    return response.data
  },

  // Dashboard aggregates
  getSummary: async () => {
    const response = await api.get('/tickets/summary')
    return response.data
  },
}

// Shared enum values — keep these in sync with backend/schemas.py
export const CATEGORIES = [
  'VPN Issue',
  'Password Reset',
  'Software Installation',
  'Laptop Issue',
  'Email Access',
  'Network Connectivity',
  'Hardware Request',
]

export const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

export const STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed']
