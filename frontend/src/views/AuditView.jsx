import { useCallback, useEffect, useMemo, useState } from 'react'
import { authApi, stockApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { Badge, EmptyState, ErrorBanner, Loading, Pager, SectionHead, SummaryStrip } from '../components.jsx'

const ROL_LABEL = { admin: 'Administrador', cajero: 'Cajero' }

/** "venta:19" -> "Venta #19"; un motivo libre se muestra tal cual. */
function humanizeMotivo(motivo) {
  if (!motivo) return 'Ajuste manual'
  const venta = /^venta:(\d+)$/.exec(motivo)
  if (venta) return `Venta #${venta[1]}`
  return motivo
}

/** El actor puede ser un usuario (id numérico) o la credencial del servicio. */
function humanizeActor(actorSub, actorRol, usuariosPorId) {
  if (!actorSub) return 'Sistema'
  if (actorSub === 'svc-sales') return 'Servicio de ventas'
  const usuario = usuariosPorId[actorSub]
  if (usuario) {
    const rol = ROL_LABEL[usuario.rol] ?? usuario.rol
    return usuario.username === usuario.rol ? rol : `${usuario.username} · ${rol}`
  }
  return `Usuario #${actorSub} · ${ROL_LABEL[actorRol] ?? actorRol}`
}

export function AuditView() {
  const [rows, setRows] = useState([])
  const [products, setProducts] = useState([])
  const [usuariosPorId, setUsuariosPorId] = useState({})
  const [applied, setApplied] = useState('')
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function loadCatalog() {
      try {
        const items = await stockApi.list('', { limit: 100 })
        if (!cancelled) setProducts(items)
      } catch {
        // El filtro sigue usable por ID si el catálogo falla.
      }
    }
    async function loadUsers() {
      try {
        const items = await authApi.users.list({ limit: 100 })
        if (!cancelled) setUsuariosPorId(Object.fromEntries(items.map((u) => [String(u.id), u])))
      } catch {
        // Si no se pueden leer los usuarios, el actor se muestra con su id.
      }
    }
    loadCatalog()
    loadUsers()
    return () => {
      cancelled = true
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const items = await stockApi.movements({
        producto_id: applied === '' ? null : Number(applied),
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

  const resumen = useMemo(() => {
    let sumados = 0
    let restados = 0
    for (const r of rows) {
      if (r.delta > 0) sumados += r.delta
      else restados += Math.abs(r.delta)
    }
    return { sumados, restados, neto: sumados - restados }
  }, [rows])

  const productoFiltro = products.find((p) => String(p.id) === applied)

  return (
    <section>
      <SectionHead
        title="Auditoría de inventario"
        description="Cada cambio de existencias queda registrado con su fecha, su motivo y quién lo hizo. Los más recientes aparecen primero."
      >
        <Badge tone="info">{rows.length} movimientos en esta página</Badge>
      </SectionHead>

      <ErrorBanner message={error} />

      <div className="pos-toolbar">
        <div className="pos-field">
          <label className="pos-field-label" htmlFor="filtro-producto">
            Filtrar por producto
          </label>
          <select
            id="filtro-producto"
            className="pos-select"
            name="producto_id"
            value={applied}
            onChange={(e) => { setApplied(e.target.value); setPage(0) }}
          >
            <option value="">Todos los productos</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.codigo} — {p.nombre}
              </option>
            ))}
          </select>
          <span className="pos-field-hint">
            {productoFiltro
              ? `Mostrando solo los movimientos de ${productoFiltro.nombre}.`
              : 'Sin filtro: se muestran los movimientos de todo el catálogo.'}
          </span>
        </div>
        {applied !== '' ? (
          <button type="button" className="pos-btn" onClick={() => { setApplied(''); setPage(0) }}>
            Quitar filtro
          </button>
        ) : null}
      </div>

      {loading ? (
        <Loading label="Cargando movimientos…" />
      ) : rows.length === 0 ? (
        <EmptyState
          title="Sin movimientos que mostrar."
          hint="Registra una venta o ajusta el stock de un producto y el cambio aparecerá aquí."
        />
      ) : (
        <>
          <SummaryStrip
            items={[
              { label: 'Movimientos', value: rows.length },
              { label: 'Unidades sumadas', value: `+${resumen.sumados}`, tone: 'up' },
              { label: 'Unidades restadas', value: `−${resumen.restados}`, tone: 'down' },
              { label: 'Saldo neto en la página', value: resumen.neto > 0 ? `+${resumen.neto}` : `${resumen.neto}` },
            ]}
          />

          <table className="pos-table">
            <caption>Movimientos de existencias, del más reciente al más antiguo</caption>
            <thead>
              <tr>
                <th scope="col">Fecha</th>
                <th scope="col">Producto</th>
                <th scope="col" className="num">Cambio</th>
                <th scope="col" className="num">Antes → Después</th>
                <th scope="col">Motivo</th>
                <th scope="col">Actor</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    {r.created_at
                      ? new Date(r.created_at).toLocaleString('es-PE', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: false,
                        })
                      : '—'}
                  </td>
                  <td>
                    {r.nombre ?? `Producto #${r.producto_id}`}
                    <span className="pos-sub">
                      <span className="pos-code" translate="no">{r.codigo ?? `#${r.producto_id}`}</span>
                    </span>
                  </td>
                  <td className="num">
                    {r.delta > 0 ? (
                      <Badge tone="ok">+{r.delta}</Badge>
                    ) : (
                      <Badge tone="danger">{r.delta}</Badge>
                    )}
                  </td>
                  <td className="num">
                    {r.cantidad_antes} → {r.cantidad_despues}
                  </td>
                  <td>{humanizeMotivo(r.motivo)}</td>
                  <td>{humanizeActor(r.actor_sub, r.actor_rol, usuariosPorId)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager
            page={page}
            hasNext={hasNext}
            count={rows.length}
            unit="movimientos"
            onPrev={() => setPage((p) => Math.max(0, p - 1))}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </section>
  )
}
