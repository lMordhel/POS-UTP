import { useEffect, useState } from 'react'
import { salesApi, stockApi } from '../api.js'
import { apiErrorMessage, money } from '../utils.js'
import { ErrorBanner, Loading } from '../components.jsx'

export function NewSaleView({ onSold }) {
  const [products, setProducts] = useState([])
  const [lines, setLines] = useState([])
  const [qty, setQty] = useState({})
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [ticket, setTicket] = useState(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        // async-parallel: catálogo en una sola llamada (sin waterfalls)
        const [items] = await Promise.all([stockApi.list('')])
        if (!cancelled) setProducts(items.filter((p) => p.activo))
      } catch (err) {
        if (!cancelled) setError(apiErrorMessage(err))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  function addLine(product) {
    const cantidad = Number(qty[product.id] ?? 1)
    if (!Number.isInteger(cantidad) || cantidad <= 0) {
      setError('Cantidad inválida (entero mayor a 0).')
      return
    }
    setError('')
    setLines((prev) => {
      const found = prev.find((l) => l.producto_id === product.id)
      if (found) {
        return prev.map((l) =>
          l.producto_id === product.id ? { ...l, cantidad: l.cantidad + cantidad } : l,
        )
      }
      return [...prev, {
        producto_id: product.id,
        nombre: product.nombre,
        precio_unitario: product.precio,
        cantidad,
      }]
    })
  }

  const estimatedTotal = lines.reduce(
    (sum, l) => sum + Number(l.cantidad) * Number(l.precio_unitario),
    0,
  )

  async function confirm() {
    if (lines.length === 0) {
      setError('Agrega al menos una línea.')
      return
    }
    setSending(true)
    setError('')
    try {
      const sale = await salesApi.create(
        lines.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad })),
      )
      setTicket(sale)
      setLines([])
      const [items] = await Promise.all([stockApi.list('')])
      setProducts(items.filter((p) => p.activo))
      onSold()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="new-sale" aria-labelledby="new-sale-title">
      <h2 id="new-sale-title">Nueva venta</h2>
      <ErrorBanner message={error} />
      {ticket ? (
        <p role="status" aria-live="polite" className="pos-ticket animate-pop">
          Venta #{ticket.id} confirmada — Total: {money(ticket.total)}
        </p>
      ) : null}
      {loading ? (
        <Loading />
      ) : (
        <table className="pos-table">
          <caption>Catálogo disponible para agregar a la venta</caption>
          <thead>
            <tr>
              <th scope="col">Producto</th>
              <th scope="col">Precio</th>
              <th scope="col">Stock</th>
              <th scope="col">Cantidad</th>
              <th scope="col"><span className="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="animate-row">
                <td>{p.nombre}</td>
                <td>{money(p.precio)}</td>
                <td>{p.stock}</td>
                <td>
                  <label className="pos-label" htmlFor={`qty-${p.id}`}>
                    Cantidad de {p.nombre}
                  </label>
                  <input id={`qty-${p.id}`} className="pos-input" type="number" min="1" step="1" defaultValue={1}
                    onChange={(e) => setQty((m) => ({ ...m, [p.id]: e.target.value }))} />
                </td>
                <td>
                  <button type="button" className="pos-btn" aria-label={`Agregar ${p.nombre} a la venta`} onClick={() => addLine(p)}>
                    Agregar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h3>Líneas ({lines.length})</h3>
      <ul>
        {lines.map((l) => (
          <li key={l.producto_id}>
            {l.nombre} × {l.cantidad} @ {money(l.precio_unitario)} = {money(Number(l.cantidad) * Number(l.precio_unitario))}
          </li>
        ))}
      </ul>
      {lines.length > 0 ? (
        <p role="status" aria-live="polite" className="pos-estimate">
          Total estimado: <strong>{money(estimatedTotal)}</strong>{' '}
          (lo confirma el servidor al vender)
        </p>
      ) : null}
      <button type="button" className="pos-btn pos-btn--primary" onClick={confirm} disabled={sending || lines.length === 0}>
        {sending ? 'Confirmando...' : 'Confirmar venta'}
      </button>
    </section>
  )
}
