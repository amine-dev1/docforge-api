import { createContext, useContext, useState, type ReactNode } from 'react'
import { api, setAccessToken } from '../lib/api'

interface AuthState {
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (payload: {
    company_name: string
    first_name: string
    last_name: string
    email: string
    password: string
  }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

function storeTokens(access: string, refresh: string) {
  setAccessToken(access)
  localStorage.setItem('refresh_token', refresh)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem('refresh_token'))

  async function login(username: string, password: string) {
    const form = new URLSearchParams({ username, password })
    const { data } = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    storeTokens(data.access_token, data.refresh_token)
    setIsAuthenticated(true)
  }

  async function register(payload: {
    company_name: string
    first_name: string
    last_name: string
    email: string
    password: string
  }) {
    const { data } = await api.post('/auth/register', payload)
    storeTokens(data.access_token, data.refresh_token)
    setIsAuthenticated(true)
  }

  function logout() {
    setAccessToken(null)
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout }}>{children}</AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
