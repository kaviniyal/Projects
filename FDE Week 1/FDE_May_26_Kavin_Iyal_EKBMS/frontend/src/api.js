/**
 * Axios instance for the Knowledge Base API.
 *
 * The request interceptor automatically attaches the bearer token from
 * localStorage to outgoing requests. The response interceptor logs errors
 * centrally and redirects to /login on 401.
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

// Attach token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('kb_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Centralized error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      if (error.response.status === 401) {
        // Auth expired or invalid; force re-login
        localStorage.removeItem('kb_token')
        localStorage.removeItem('kb_user')
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
      console.error('API error:', error.response.status, error.response.data)
    } else {
      console.error('Network error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api
