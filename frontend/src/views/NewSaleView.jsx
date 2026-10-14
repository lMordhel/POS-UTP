import { useEffect, useRef, useState } from 'react'
import { salesApi, stockApi } from '../api.js'
import { apiErrorMessage, money } from '../utils.js'
import { ErrorBanner, Loading } from '../components.jsx'

const SEARCH_DEBOUNCE_MS = 300

function parseQty(raw) {
  const cantidad = Number(raw)
  if (raw === '' || raw === null || raw === undefined) return { ok: false, cantidad: NaN }
  if (!Number.isInteger(cantidad) || cantidad <= 0) return { ok: false, cantidad }
  return { ok: true, cantidad }
}

export function NewSaleView({ onSold }) {
  const [products, setProducts] = useState([])
  const [lines, setLines] = useState([])
  const [qty, setQty] = useState({})
  const [searchTerm, setSearchTerm] = useState('')
  const [searchQty, setSearchQty] = useState('1')
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const [lineErrors, setLineErrors] = useState({})
  const [ticket, setTicket] = useState(null)
  const requestSeq = useRef(0)
  const knownStock = useRef(new Map())
  const searchInputRef = useRef(null)

  function rememberStock(items) {
    for (const p of items) knownStock.current.set(p.id, p)
  }

  useEffect(() => {
    let cancelled = false
    requestSeq.current += 1
    const seq = requestSeq.current
    setSearching(true)
    const timer = setTimeout(async () => {
      try {
        const items = await stockApi.list(searchTerm.trim())
        if (cancelled || requestSeq.current !== seq) return
        rememberStock(items)
        setProducts(items.filter((p) => p.activo))
        setError((prev) => (prev.startsWith('No se pudo buscar') ? '' : prev))
      } catch (err) {
        if (cancelled || requestSeq.current !== seq) return
        setError(`No se pudo buscar: ${apiErrorMessage(err)}`)
      } finally {
        if (!cancelled && requestSeq.current === seq) {
          setSearching(false)
          setLoading(false)
        }
      }
    }, SEARCH_DEBOUNCE_MS)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [searchTerm])

  function stockOf(productoId) {
    const known = knownStock.current.get(productoId)
    if (known) return known.stock
    const listed = products.find((p) => p.id === productoId)
    return listed ? listed.stock : null
  }

  function productName(productoId, fallback) {
    const known = knownStock.current.get(productoId)
    if (known) return known.nombre
    const listed = products.find((p) => p.id === productoId)
    if (listed) return listed.nombre
    return fallback ?? `Producto ${productoId}`
  }

  function addProduct(product, rawQty) {
    const parsed = parseQty(rawQty ?? 1)
    if (!parsed.ok) {
      setError(`Cantidad inválida para ${product.nombre} (entero mayor a 0).`)
      return false
    }
    const found = lines.find((l) => l.producto_id === product.id)
    const accumulated = (found ? found.cantidad : 0) + parsed.cantidad
    if (Number.isFinite(product.stock) && accumulated > product.stock) {
      setError(`Solo hay ${product.stock} de ${product.nombre} en stock.`)
      return false
    }
    setError('')
    setLines((prev) => {
      const existing = prev.find((l) => l.producto_id === product.id)
      if (existing) {
        return prev.map((l) =>
          l.producto_id === product.id ? { ...l, cantidad: l.cantidad + parsed.cantidad } : l,
        )
      }
      return [...prev, {
        producto_id: product.id,
        nombre: product.nombre,
        precio_unitario: product.precio,
        cantidad: parsed.cantidad,
      }]
    })
    return true
  }

  function addLine(product) {
    addProduct(product, qty[product.id] ?? 1)
  }

  function addFirstResult() {
    if (products.length === 0) {
      setError('Sin resultados para agregar.')
      return
    }
    const first = products[0]
    if (addProduct(first, searchQty)) {
      searchInputRef.current?.focus()
    }
  }

  function removeLine(productoId) {
    setLines((prev) => prev.filter((l) => l.producto_id !== productoId))
    setLineErrors((prev) => {
      const next = { ...prev }
      delete next[productoId]
      return next
    })
    setError('')
  }

  function changeLineQty(productoId, raw) {
    const parsed = parseQty(Number(raw))
    if (!parsed.ok) {
      setLineErrors((prev) => ({
        ...prev,
        [productoId]: 'Cantidad inválida (entero mayor a 0).',
      }))
      return
    }
    const stock = stockOf(productoId)
    if (stock !== null && parsed.cantidad > stock) {
      setLineErrors((prev) => ({
        ...prev,
        [productoId]: `Solo hay ${stock} en stock.`,
      }))
      return
    }
    setLineErrors((prev) => {
      const next = { ...prev }
      delete next[productoId]
      return next
    })
    setLines((prev) => prev.map((l) =>
      l.producto_id === productoId ? { ...l, cantidad: parsed.cantidad } : l,
    ))
  }

  function validateBeforeConfirm() {
    for (const l of lines) {
      if (!Number.isInteger(l.cantidad) || l.cantidad <= 0) {
        return `Cantidad inválida en ${l.nombre} (entero mayor a 0).`
      }
      const stock = stockOf(l.producto_id)
      if (stock !== null && l.cantidad > stock) {
        return `Solo hay ${stock} de ${productName(l.producto_id, l.nombre)} en stock.`
      }
    }
    return ''
  }

  async function confirm() {
    if (lines.length === 0) {
      setError('Agrega al menos una línea.')
      return
    }
    const blocked = validateBeforeConfirm()
    if (blocked) {
      setError(blocked)
      return
    }
    setSending(true)
    setError('')
    try {
      const sale = await salesApi.create(
        lines.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad })),
      )
      const names = new Map(lines.map((l) => [l.producto_id, l.nombre]))
      setTicket({
        sale,
        lines: (sale.items ?? []).map((i) => ({
          ...i,
          nombre: names.get(i.producto_id) ?? productName(i.producto_id),
        })),
      })
      setLines([])
      setLineErrors({})
      const items = await stockApi.list(searchTerm.trim())
      rememberStock(items)
      setProducts(items.filter((p) => p.activo))
      onSold()
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  function newSale() {
    setLines([])
    setLineErrors({})
    setTicket(null)
    setError('')
    setSearchTerm('')
    setSearchQty('1')
    setQty({})
    searchInputRef.current?.focus()
  }

  const estimatedTotal = lines.reduce(
    (sum, l) => sum + Number(l.cantidad) * Number(l.precio_unitario),
    0,
  )

  return (
    <section className="new-sale" aria-labelledby="new-sale-title">
      <h2 id="new-sale-title">Nueva venta</h2>
      <ErrorBanner message={error} />
      {ticket ? (
        <div role="status" aria-live="polite" className="pos-ticket animate-pop">
          <p><strong>Venta #{ticket.sale.id} confirmada — Total: {money(ticket.sale.total)}</strong></p>
          <table className="pos-table pos-ticket-table">
            <caption>Desglose de la venta #{ticket.sale.id}</caption>
            <thead>
              <tr>
                <th scope="col">Producto</th>
                <th scope="col">Cantidad</th>
                <th scope="col">Precio</th>
                <th scope="col">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {ticket.lines.map((i, idx) => (
                <tr key={`${i.producto_id}-${idx}`}>
                  <td>{i.nombre}</td>
                  <td>{i.cantidad}</td>
                  <td>{money(i.precio_unitario)}</td>
                  <td>{money(i.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button type="button" className="pos-btn pos-btn--primary" onClick={newSale}>
            Nueva venta
          </button>
        </div>
      ) : null}
      <div className="pos-search">
        <div className="pos-search-field">
          <label className="pos-label" htmlFor="sale-search">
            Buscar producto por código o nombre
          </label>
          <input
            id="sale-search"
            ref={searchInputRef}
            className="pos-input pos-search-input"
            type="search"
            autoComplete="off"
            placeholder="Ej. leche o 75010… (Enter agrega el primero)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addFirstResult()
              }
            }}
          />
        </div>
        <div className="pos-search-field pos-search-field--qty">
          <label className="pos-label" htmlFor="sale-search-qty">
            Cantidad para Enter
          </label>
          <input
            id="sale-search-qty"
            className="pos-input"
            type="number"
            min="1"
            step="1"
            value={searchQty}
            onChange={(e) => setSearchQty(e.target.value)}
          />
        </div>
      </div>
      {loading || searching ? (
        <Loading label={loading ? 'Cargando catálogo...' : 'Buscando...'} />
      ) : products.length === 0 ? (
        <p role="status" className="pos-empty">Sin resultados para “{searchTerm}”.</p>
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
      {lines.length === 0 ? (
        <p className="pos-empty">Sin líneas. Busca un producto y agrégalo.</p>
      ) : (
        <ul className="pos-lines">
          {lines.map((l) => (
            <li key={l.producto_id} className="pos-line animate-row">
              <span className="pos-line-name">
                {l.nombre} @ {money(l.precio_unitario)} = {money(Number(l.cantidad) * Number(l.precio_unitario))}
              </span>
              <label className="pos-label" htmlFor={`line-qty-${l.producto_id}`}>
                Cantidad de {l.nombre}
              </label>
              <input
                id={`line-qty-${l.producto_id}`}
                className="pos-input"
                type="number"
                min="1"
                step="1"
                value={l.cantidad}
                onChange={(e) => changeLineQty(l.producto_id, e.target.value)}
              />
              <button
                type="button"
                className="pos-btn"
                aria-label={`Quitar ${l.nombre} de la venta`}
                onClick={() => removeLine(l.producto_id)}
              >
                Quitar
              </button>
              {lineErrors[l.producto_id] ? (
                <span role="alert" className="pos-line-error">{lineErrors[l.producto_id]}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
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
