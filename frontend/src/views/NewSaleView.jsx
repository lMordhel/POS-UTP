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
      return [...prev, { producto_id: product.id, nombre: product.nombre, cantidad }]
    })
  }

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
    <section>
      <h2>Nueva venta</h2>
      <ErrorBanner message={error} />
      {ticket ? (
        <p>Venta #{ticket.id} confirmada — Total: {money(ticket.total)}</p>
      ) : null}
      {loading ? (
        <Loading />
      ) : (
        <table>
          <thead>
            <tr><th>Producto</th><th>Precio</th><th>Stock</th><th>Cant.</th><th /></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.nombre}</td>
                <td>{money(p.precio)}</td>
                <td>{p.stock}</td>
                <td>
                  <input type="number" min="1" step="1" defaultValue={1}
                    onChange={(e) => setQty((m) => ({ ...m, [p.id]: e.target.value }))} />
                </td>
                <td><button onClick={() => addLine(p)}>Agregar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h3>Líneas ({lines.length})</h3>
      <ul>
        {lines.map((l) => (
          <li key={l.producto_id}>{l.nombre} × {l.cantidad}</li>
        ))}
      </ul>
      <button onClick={confirm} disabled={sending || lines.length === 0}>
        {sending ? 'Confirmando...' : 'Confirmar venta'}
      </button>
    </section>
  )
}
