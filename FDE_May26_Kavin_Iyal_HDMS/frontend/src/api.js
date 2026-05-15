/**
 * Axios instance configured to talk to the FastAPI backend.
 *
 * The base URL can be overridden at build time via VITE_API_URL — useful
 * when deploying the frontend separately from the backend.
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
})

// Centralized error logging so we don't repeat ourselves at each call site.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('API Network Error:', error.message)
    } else {
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api
