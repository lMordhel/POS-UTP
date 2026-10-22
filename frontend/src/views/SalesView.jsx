import { useCallback, useEffect, useRef, useState } from 'react'
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
  const detailRef = useRef(null)

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

  // SPEC-FRONT-008 (AC-FRONT08-03): al abrir el detalle el foco va al panel,
  // que se muestra encima de la tabla; antes el detalle aparecía debajo de
  // 20 filas y el clic en "Ver" parecía no hacer nada.
  useEffect(() => {
    if (detail) detailRef.current?.focus()
  }, [detail])

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
      {detail ? (
        <div
          className="pos-ticket pos-detail"
          role="region"
          aria-label={`Detalle de la venta ${detail.id}`}
          ref={detailRef}
          tabIndex={-1}
        >
          <div className="pos-detail-head">
            <h3>Venta #{detail.id} — Total {money(detail.total)}</h3>
            <button type="button" className="pos-btn" onClick={() => setDetail(null)}>Cerrar</button>
          </div>
          <table className="pos-table pos-ticket-table">
            <thead>
              <tr>
                <th scope="col">Producto</th>
                <th scope="col">Cantidad</th>
                <th scope="col">Precio</th>
                <th scope="col">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {detail.items.map((i, idx) => (
                <tr key={idx}>
                  <td>Producto {i.producto_id}</td>
                  <td>{i.cantidad}</td>
                  <td>{money(i.precio_unitario)}</td>
                  <td>{money(i.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
      {loading ? (
        <Loading />
      ) : (
        <>
          <table className="pos-table">
            <caption>Ventas registradas, de la más reciente a la más antigua</caption>
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Fecha</th>
                <th scope="col" className="num">Total</th>
                <th scope="col">Estado</th>
                <th scope="col" className="actions" />
              </tr>
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
    </section>
  )
}
