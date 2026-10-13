import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { authApi, setAuthStore } from './api.js'

const KEY = 'pos-utp-session'

function loadSession() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data?.access_token || !data?.refresh_token) return null
    return data
  } catch {
    return null
  }
}

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadSession)

  const save = useCallback((data) => {
    setSession(data)
    if (data) localStorage.setItem(KEY, JSON.stringify(data))
    else localStorage.removeItem(KEY)
  }, [])

  const login = useCallback(
    async (username, password) => {
      const tokens = await authApi.login(username, password)
      // El rol viene en el payload del JWT (sin verificar firma: la API manda).
      // Base64url -> base64 con padding: atob no acepta '-'/'_' ni falta de '='.
      const raw = tokens.access_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
      const padded = raw + '='.repeat((4 - (raw.length % 4)) % 4)
      const payload = JSON.parse(atob(padded))
      const data = { ...tokens, username, rol: payload.rol }
      save(data)
      return data
    },
    [save],
  )

  const logout = useCallback(() => save(null), [save])

  // Puente api.js -> contexto: renueva una vez y reintenta; si falla, sale.
  setAuthStore({
    getAccess: () => loadSession()?.access_token ?? null,
    getRefresh: () => loadSession()?.refresh_token ?? null,
    setTokens: (tokens) => {
      const current = loadSession()
      if (!current) return
      save({ ...current, ...tokens })
    },
    onUnauthorized: () => save(null),
  })

  const value = useMemo(
    () => ({ session, user: session ? { username: session.username, rol: session.rol } : null, login, logout }),
    [session, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth fuera de AuthProvider')
  return ctx
}
