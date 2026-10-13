import { useCallback, useEffect, useState } from 'react'
import { stockApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { ErrorBanner, Loading, Pager } from '../components.jsx'

export function AuditView() {
  const [rows, setRows] = useState([])
  const [filter, setFilter] = useState('')
  const [applied, setApplied] = useState('')
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const pid = applied.trim() === '' ? null : Number(applied)
      const items = await stockApi.movements({
        producto_id: pid,
        skip: page * PAGE_SIZE,
      })
      if (items.length === 0 && page > 0) {
        setPage((p) => p - 1)
        return
      }
      setHasNext(items.length > PAGE_SIZE)
      setRows(items.slice(0, PAGE_SIZE))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [applied, page])

  useEffect(() => {
    load()
  }, [load])

  function applyFilter(e) {
    e.preventDefault()
    if (filter.trim() !== '' && (!Number.isInteger(Number(filter)) || Number(filter) <= 0)) {
      setError('Filtro inválido (ID de producto entero mayor a 0, o vacío).')
      return
    }
    setApplied(filter.trim())
    setPage(0)
  }

  return (
    <section>
      <h2>Auditoría de inventario</h2>
      <ErrorBanner message={error} />
      <form onSubmit={applyFilter}>
        <label>
          ID de producto (lo ves en la columna # de Productos; vacío = todos)
          <input placeholder="Ej: 3 (vacío = todos)" value={filter}
            onChange={(e) => setFilter(e.target.value)} />
        </label>
        <button type="submit">Filtrar</button>
      </form>
      {loading ? (
        <Loading />
      ) : rows.length === 0 ? (
        <p>Sin movimientos todavía. Registra una venta o ajusta stock y vuelve.</p>
      ) : (
        <>
          <table>
            <thead>
              <tr><th>#</th><th>Producto</th><th>Delta</th><th>Antes → Después</th><th>Motivo</th><th>Actor</th></tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.codigo ?? '—'} {r.nombre ?? ''} (#{r.producto_id})</td>
                  <td>{r.delta > 0 ? `+${r.delta}` : r.delta}</td>
                  <td>{r.cantidad_antes} → {r.cantidad_despues}</td>
                  <td>{r.motivo || '—'}</td>
                  <td>{r.actor_sub} ({r.actor_rol})</td>
                </tr>
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
