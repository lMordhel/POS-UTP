import { useCallback, useEffect, useState } from 'react'
import { stockApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { ErrorBanner, Loading, Pager, ProductRow } from '../components.jsx'

const EMPTY_FORM = { codigo: '', nombre: '', precio: '', cantidad_inicial: '' }

export function ProductsView({ isAdmin }) {
  const [products, setProducts] = useState([])
  const [q, setQ] = useState('')
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(null)
  const [adjusting, setAdjusting] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const items = await stockApi.list(q, { skip: page * PAGE_SIZE })
      if (items.length === 0 && page > 0) {
        setPage((p) => p - 1)
        return
      }
      setHasNext(items.length > PAGE_SIZE)
      setProducts(items.slice(0, PAGE_SIZE))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [q, page])

  useEffect(() => {
    load()
  }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    try {
      await stockApi.create({
        codigo: form.codigo,
        nombre: form.nombre,
        precio: form.precio,
        cantidad_inicial: form.cantidad_inicial === '' ? 0 : Number(form.cantidad_inicial),
      })
      setForm(EMPTY_FORM)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  async function handleDeactivate(id) {
    setError('')
    try {
      await stockApi.deactivate(id)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  function startEdit(product) {
    setAdjusting(null)
    setError('')
    setEditing({ id: product.id, nombre: product.nombre, precio: product.precio, descripcion: product.descripcion ?? '' })
  }

  async function handleUpdate(e) {
    e.preventDefault()
    setError('')
    try {
      await stockApi.update(editing.id, {
        nombre: editing.nombre,
        precio: editing.precio,
        descripcion: editing.descripcion,
      })
      setEditing(null)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  function startAdjust(product) {
    setEditing(null)
    setError('')
    setAdjusting({ id: product.id, nombre: product.nombre, stock: product.stock, delta: '', motivo: '' })
  }

  async function handleAdjust(e) {
    e.preventDefault()
    const delta = Number(adjusting.delta)
    if (!Number.isInteger(delta) || delta === 0) {
      setError('Delta inválido (entero distinto de 0).')
      return
    }
    setError('')
    try {
      await stockApi.adjust(adjusting.id, delta, adjusting.motivo.trim() || undefined)
      setAdjusting(null)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <section>
      <h2>Productos</h2>
      <ErrorBanner message={error} />
      {isAdmin ? (
        <form onSubmit={handleCreate}>
          <input placeholder="Código" value={form.codigo}
            onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value }))} required />
          <input placeholder="Nombre" value={form.nombre}
            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
          <input placeholder="Precio" type="number" step="0.01" min="0.01" value={form.precio}
            onChange={(e) => setForm((f) => ({ ...f, precio: e.target.value }))} required />
          <input placeholder="Stock inicial" type="number" min="0" step="1" value={form.cantidad_inicial}
            onChange={(e) => setForm((f) => ({ ...f, cantidad_inicial: e.target.value }))} />
          <button type="submit">Crear</button>
        </form>
      ) : null}
      {isAdmin && editing ? (
        <form onSubmit={handleUpdate}>
          <h3>Editando {editing.nombre} (#{editing.id})</h3>
          <label>
            Nombre
            <input value={editing.nombre}
              onChange={(e) => setEditing((s) => ({ ...s, nombre: e.target.value }))} required />
          </label>
          <label>
            Precio
            <input type="number" step="0.01" min="0.01" value={editing.precio}
              onChange={(e) => setEditing((s) => ({ ...s, precio: e.target.value }))} required />
          </label>
          <label>
            Descripción
            <input value={editing.descripcion}
              onChange={(e) => setEditing((s) => ({ ...s, descripcion: e.target.value }))} />
          </label>
          <button type="submit">Guardar cambios</button>
          <button type="button" onClick={() => setEditing(null)}>Cancelar</button>
        </form>
      ) : null}
      {isAdmin && adjusting ? (
        <form onSubmit={handleAdjust}>
          <h3>Ajustar stock de {adjusting.nombre}</h3>
          <p>
            Stock actual: <strong>{adjusting.stock}</strong> — el ajuste lo suma o lo resta.
          </p>
          <label>
            Cantidad (usa número negativo para restar)
            <input type="number" step="1" placeholder="Ej: 5 para sumar, -3 para restar"
              value={adjusting.delta}
              onChange={(e) => setAdjusting((s) => ({ ...s, delta: e.target.value }))} required />
          </label>
          <label>
            Motivo del ajuste (opcional)
            <input placeholder="Ej: conteo físico, merma, devolución de cliente..."
              value={adjusting.motivo}
              onChange={(e) => setAdjusting((s) => ({ ...s, motivo: e.target.value }))} />
          </label>
          <button type="submit">Aplicar ajuste</button>
          <button type="button" onClick={() => setAdjusting(null)}>Cancelar</button>
        </form>
      ) : null}
      <input placeholder="Buscar..." value={q}
        onChange={(e) => { setQ(e.target.value); setPage(0) }} />
      {loading ? (
        <Loading />
      ) : (
        <>
          <table>
            <thead>
              <tr><th>Código</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Activo</th><th /></tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <ProductRow key={p.id} product={p} canDeactivate={isAdmin}
                  onDeactivate={handleDeactivate} canManage={isAdmin}
                  onEdit={startEdit} onAdjust={startAdjust} />
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
