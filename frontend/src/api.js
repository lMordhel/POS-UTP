const STOCK = import.meta.env.VITE_STOCK_URL ?? 'http://localhost:8002'
const SALES = import.meta.env.VITE_SALES_URL ?? 'http://localhost:8001'

async function request(base, path, options = {}) {
  const res = await fetch(`${base}/api/v1${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.text()
    const err = new Error(detail || `HTTP ${res.status}`)
    err.status = res.status
    throw err
  }
  return res.json()
}

export const stockApi = {
  list: (q = '') => request(STOCK, `/products${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  create: (body) => request(STOCK, '/products', { method: 'POST', body: JSON.stringify(body) }),
  deactivate: (id) => request(STOCK, `/products/${id}`, { method: 'DELETE' }),
}

export const salesApi = {
  create: (items) => request(SALES, '/sales', { method: 'POST', body: JSON.stringify({ items }) }),
  list: () => request(SALES, '/sales'),
  get: (id) => request(SALES, `/sales/${id}`),
}
