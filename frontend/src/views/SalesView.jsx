import { useCallback, useEffect, useState } from 'react'
import { salesApi } from '../api.js'
import { apiErrorMessage, money } from '../utils.js'
import { ErrorBanner, Loading, SaleRow } from '../components.jsx'

export function SalesView({ refreshKey }) {
  const [sales, setSales] = useState([])
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setSales(await salesApi.list())
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load, refreshKey])

  async function select(id) {
    setError('')
    try {
      setDetail(await salesApi.get(id))
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <section>
      <h2>Ventas</h2>
      <ErrorBanner message={error} />
      {loading ? (
        <Loading />
      ) : (
        <table>
          <thead>
            <tr><th>#</th><th>Fecha</th><th>Total</th><th>Estado</th><th /></tr>
          </thead>
          <tbody>
            {sales.map((s) => (
              <SaleRow key={s.id} sale={s} onSelect={select} />
            ))}
          </tbody>
        </table>
      )}
      {detail ? (
        <div>
          <h3>Venta #{detail.id} — Total {money(detail.total)}</h3>
          <ul>
            {detail.items.map((i, idx) => (
              <li key={idx}>
                Producto {i.producto_id} × {i.cantidad} @ {money(i.precio_unitario)} = {money(i.subtotal)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  )
}
