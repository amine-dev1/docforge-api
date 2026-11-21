import axios from 'axios'

export const api = axios.create({
  baseURL: '/api/v1',
})

let accessToken: string | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Concurrent 401s must share a single refresh call: the backend rotates refresh
// tokens, so a second independent refresh would invalidate the one the first
// request just received and use, causing an infinite 401 loop.
let refreshPromise: Promise<string> | null = null

function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) throw new Error('No refresh token')
      const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
      setAccessToken(data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      return data.access_token as string
    })().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      try {
        const token = await refreshAccessToken()
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      } catch {
        setAccessToken(null)
        localStorage.removeItem('refresh_token')
      }
    }
    return Promise.reject(error)
  },
)
