import { useCallback, useEffect, useState } from 'react'
import { salesApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage, money } from '../utils.js'
import { ErrorBanner, Loading, Pager, SaleRow } from '../components.jsx'

export function SalesView({ refreshKey }) {
  const [sales, setSales] = useState([])
  const [detail, setDetail] = useState(null)
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const items = await salesApi.list({ skip: page * PAGE_SIZE })
      if (items.length === 0 && page > 0) {
        setPage((p) => p - 1)
        return
      }
      setHasNext(items.length > PAGE_SIZE)
      setSales(items.slice(0, PAGE_SIZE))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page])

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
        <>
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
          <Pager page={page} hasNext={hasNext}
            onPrev={() => setPage((p) => Math.max(0, p - 1))}
            onNext={() => setPage((p) => p + 1)} />
        </>
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
