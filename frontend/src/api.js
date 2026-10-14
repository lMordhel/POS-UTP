import { PAGE_SIZE } from './utils.js'

const STOCK = import.meta.env.VITE_STOCK_URL ?? 'http://localhost:8002'
const SALES = import.meta.env.VITE_SALES_URL ?? 'http://localhost:8001'

// Puente con AuthContext (SPEC-FRONT-002): tokens + salida por 401 definitivo.
const store = {
  getAccess: () => null,
  getRefresh: () => null,
  setTokens: () => {},
  onUnauthorized: () => {},
}

export function setAuthStore(next) {
  Object.assign(store, next)
}

async function raw(base, path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers ?? {}) }
  const access = store.getAccess()
  if (access) headers.Authorization = `Bearer ${access}`
  const res = await fetch(`${base}/api/v1${path}`, { ...options, headers })
  return res
}

function toError(res, detail) {
  const err = new Error(detail || `HTTP ${res.status}`)
  err.status = res.status
  throw err
}

async function request(base, path, options = {}, retried = false) {
  let res = await raw(base, path, options)
  if (res.status === 401 && !retried) {
    // Renueva una vez con el refresh y reintenta (FR-03).
    const refresh = store.getRefresh()
    if (refresh) {
      const rr = await fetch(`${SALES}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      })
      if (rr.ok) {
        const pair = await rr.json()
        store.setTokens({ access_token: pair.access_token, refresh_token: pair.refresh_token })
        res = await raw(base, path, options)
        if (res.ok) return res.json()
      }
    }
    store.onUnauthorized()
  }
  if (!res.ok) {
    const detail = await res.text()
    toError(res, detail)
  }
  return res.json()
}

export const authApi = {
  login: async (username, password) => {
    const res = await fetch(`${SALES}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) toError(res, await res.text())
    return res.json()
  },
  users: {
    list: ({ skip = 0, limit = PAGE_SIZE + 1 } = {}) =>
      request(SALES, `/users?skip=${skip}&limit=${limit}`),
    create: (body) => request(SALES, '/users', { method: 'POST', body: JSON.stringify(body) }),
    update: (id, body) =>
      request(SALES, `/users/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  },
}

export const stockApi = {
  list: (q = '', { skip = 0, limit = PAGE_SIZE + 1 } = {}) => {
    const params = new URLSearchParams()
    if (q) params.set('q', q)
    params.set('skip', String(skip))
    params.set('limit', String(limit))
    return request(STOCK, `/products?${params}`)
  },
  create: (body) => request(STOCK, '/products', { method: 'POST', body: JSON.stringify(body) }),
  update: (id, body) => request(STOCK, `/products/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  adjust: (id, delta, motivo) =>
    request(STOCK, `/products/${id}/stock`, {
      method: 'PATCH',
      body: JSON.stringify(motivo ? { delta, motivo } : { delta }),
    }),
  deactivate: (id) => request(STOCK, `/products/${id}`, { method: 'DELETE' }),
  movements: ({ producto_id = null, skip = 0, limit = PAGE_SIZE + 1 } = {}) => {
    const params = new URLSearchParams()
    if (producto_id) params.set('producto_id', String(producto_id))
    params.set('skip', String(skip))
    params.set('limit', String(limit))
    return request(STOCK, `/stock/movements?${params}`)
  },
}

export const salesApi = {
  create: (items, { cliente, monto_recibido } = {}) => {
    const body = { items }
    if (cliente !== undefined && cliente !== null && cliente !== '') body.cliente = cliente
    if (monto_recibido !== undefined && monto_recibido !== null && monto_recibido !== '') {
      body.monto_recibido = monto_recibido
    }
    return request(SALES, '/sales', { method: 'POST', body: JSON.stringify(body) })
  },
  list: ({ skip = 0, limit = PAGE_SIZE + 1 } = {}) =>
    request(SALES, `/sales?skip=${skip}&limit=${limit}`),
  get: (id) => request(SALES, `/sales/${id}`),
}
