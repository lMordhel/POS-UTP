import { useCallback, useEffect, useState } from 'react'
import { stockApi } from '../api.js'
import { apiErrorMessage } from '../utils.js'
import { ErrorBanner, Loading, ProductRow } from '../components.jsx'

const EMPTY_FORM = { codigo: '', nombre: '', precio: '', cantidad_inicial: '' }

export function ProductsView() {
  const [products, setProducts] = useState([])
  const [q, setQ] = useState('')
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setProducts(await stockApi.list(q))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [q])

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

  return (
    <section>
      <h2>Productos</h2>
      <ErrorBanner message={error} />
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
      <input placeholder="Buscar..." value={q} onChange={(e) => setQ(e.target.value)} />
      {loading ? (
        <Loading />
      ) : (
        <table>
          <thead>
            <tr><th>Código</th><th>Nombre</th><th>Precio</th><th>Stock</th><th>Activo</th><th /></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <ProductRow key={p.id} product={p} onDeactivate={handleDeactivate} />
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
