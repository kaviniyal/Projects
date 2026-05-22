/**
 * AuthContext — global authentication state.
 *
 * Stores the current user and token in React state + localStorage. Exposes
 * login, register, logout, and role-checking helpers.
 */
import { createContext, useContext, useEffect, useState } from 'react'
import api from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // Restore session from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('kb_user')
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser))
      } catch {
        localStorage.removeItem('kb_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password })
    const { access_token, user: userData } = res.data
    localStorage.setItem('kb_token', access_token)
    localStorage.setItem('kb_user', JSON.stringify(userData))
    setUser(userData)
    return userData
  }

  const register = async (data) => {
    await api.post('/auth/register', data)
    // After registration, log them in immediately
    return login(data.email, data.password)
  }

  const logout = () => {
    localStorage.removeItem('kb_token')
    localStorage.removeItem('kb_user')
    setUser(null)
  }

  const hasRole = (...roles) => {
    return user && roles.includes(user.role_name)
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    hasRole,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
