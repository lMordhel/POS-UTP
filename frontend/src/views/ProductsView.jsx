import { useCallback, useEffect, useState } from 'react'
import { stockApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { Badge, EmptyState, ErrorBanner, Field, Loading, NoticeBanner, Pager, ProductRow, SectionHead } from '../components.jsx'

const EMPTY_FORM = { codigo: '', nombre: '', precio: '', cantidad_inicial: '' }

export function ProductsView({ isAdmin }) {
  const [products, setProducts] = useState([])
  const [q, setQ] = useState('')
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editing, setEditing] = useState(null)
  const [adjusting, setAdjusting] = useState(null)
  const [showCreate, setShowCreate] = useState(false)

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
    setNotice('')
    try {
      const created = await stockApi.create({
        codigo: form.codigo,
        nombre: form.nombre,
        precio: form.precio,
        cantidad_inicial: form.cantidad_inicial === '' ? 0 : Number(form.cantidad_inicial),
      })
      setForm(EMPTY_FORM)
      setShowCreate(false)
      // El catálogo se ordena por id ascendente, así que el producto nuevo
      // quedaría en la última página: se filtra por su código para que el
      // usuario vea de inmediato lo que acaba de crear.
      setQ(created.codigo ?? '')
      setPage(0)
      setNotice(`Producto ${created.codigo ?? created.nombre} creado.`)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  async function handleDeactivate(id) {
    const target = products.find((p) => p.id === id)
    const name = target ? target.nombre : `#${id}`
    if (!window.confirm(`¿Desactivar ${name}? No se podrá vender hasta reactivarlo.`)) return
    setError('')
    setNotice('')
    try {
      await stockApi.deactivate(id)
      setNotice(`${name} ya no se puede vender.`)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  async function handleReactivate(id) {
    setError('')
    setNotice('')
    try {
      await stockApi.update(id, { activo: true })
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  function startEdit(product) {
    setAdjusting(null)
    setError('')
    setNotice('')
    setEditing({ id: product.id, nombre: product.nombre, precio: product.precio, descripcion: product.descripcion ?? '' })
  }

  async function handleUpdate(e) {
    e.preventDefault()
    setError('')
    setNotice('')
    try {
      await stockApi.update(editing.id, {
        nombre: editing.nombre,
        precio: editing.precio,
        descripcion: editing.descripcion,
      })
      setEditing(null)
      setNotice('Producto actualizado.')
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  function startAdjust(product) {
    setEditing(null)
    setError('')
    setNotice('')
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
    setNotice('')
    try {
      await stockApi.adjust(adjusting.id, delta, adjusting.motivo.trim() || undefined)
      setAdjusting(null)
      setNotice('Ajuste de stock aplicado y auditado.')
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  const sinStock = products.filter((p) => p.stock === 0).length
  const inactivos = products.filter((p) => !p.activo).length

  return (
    <section>
      <SectionHead
        title="Productos"
        description="Catálogo que el punto de venta puede ofrecer. Un producto inactivo no se puede vender."
      >
        <Badge tone="info">
          {products.length} en esta página
          {sinStock > 0 ? ` · ${sinStock} sin stock` : ''}
          {inactivos > 0 ? ` · ${inactivos} inactivos` : ''}
        </Badge>
        {isAdmin ? (
          <button
            type="button"
            className="pos-btn pos-btn--primary"
            aria-expanded={showCreate}
            onClick={() => setShowCreate((v) => !v)}
          >
            {showCreate ? 'Cancelar alta' : 'Nuevo producto'}
          </button>
        ) : null}
      </SectionHead>

      <ErrorBanner message={error} />
      <NoticeBanner message={notice} />

      <div className="pos-toolbar">
        <div className="pos-toolbar-search">
          <label className="pos-field-label" htmlFor="buscar-producto">
            Buscar producto
          </label>
          <input
            id="buscar-producto"
            className="pos-input pos-search-input"
            type="search"
            placeholder="Por nombre o código, ej: pan…"
            name="q"
            autoComplete="off"
            spellCheck={false}
            value={q}
            onChange={(e) => { setQ(e.target.value); setPage(0) }}
          />
          <span className="pos-field-hint">La búsqueda se hace en el servidor sobre todo el catálogo.</span>
        </div>
      </div>

      {isAdmin && showCreate ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Nuevo producto</h3>
          <p className="pos-card-desc">
            El código es el identificador que se usa al vender y no se puede repetir.
          </p>
          <form onSubmit={handleCreate}>
            <div className="pos-fields">
              <Field label="Código" id="nuevo-codigo" hint="Identificador único, ej: DEMO-001…">
                <input
                  id="nuevo-codigo"
                  className="pos-input pos-search-input"
                  name="codigo"
                  value={form.codigo}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="Ej: DEMO-001…"
                  onChange={(e) => setForm((f) => ({ ...f, codigo: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Nombre" id="nuevo-nombre" hint="Cómo se muestra en el punto de venta.">
                <input
                  id="nuevo-nombre"
                  className="pos-input pos-search-input"
                  name="nombre"
                  value={form.nombre}
                  placeholder="Ej: Café molido 500 g…"
                  onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Precio de venta" id="nuevo-precio" hint="En soles, con dos decimales.">
                <input
                  id="nuevo-precio"
                  className="pos-input pos-search-input"
                  name="precio"
                  type="number"
                  step="0.01"
                  min="0.01"
                  inputMode="decimal"
                  value={form.precio}
                  placeholder="Ej: 25.90…"
                  onChange={(e) => setForm((f) => ({ ...f, precio: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Stock inicial" id="nuevo-stock" hint="Unidades que entran al inventario. Puedes dejarlo en 0.">
                <input
                  id="nuevo-stock"
                  className="pos-input pos-search-input"
                  name="cantidad_inicial"
                  type="number"
                  min="0"
                  step="1"
                  inputMode="numeric"
                  value={form.cantidad_inicial}
                  placeholder="Ej: 0…"
                  onChange={(e) => setForm((f) => ({ ...f, cantidad_inicial: e.target.value }))}
                />
              </Field>
            </div>
            <div className="pos-form-actions">
              <button type="submit" className="pos-btn pos-btn--primary">
                Crear producto
              </button>
              <button type="button" className="pos-btn" onClick={() => setShowCreate(false)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {isAdmin && editing ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Editando {editing.nombre}</h3>
          <p className="pos-card-desc">Los cambios no modifican las existencias; para eso usa «Ajustar stock».</p>
          <form onSubmit={handleUpdate}>
            <div className="pos-fields">
              <Field label="Nombre" id="editar-nombre">
                <input
                  id="editar-nombre"
                  className="pos-input pos-search-input"
                  name="nombre"
                  value={editing.nombre}
                  onChange={(e) => setEditing((s) => ({ ...s, nombre: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Precio de venta" id="editar-precio">
                <input
                  id="editar-precio"
                  className="pos-input pos-search-input"
                  name="precio"
                  type="number"
                  step="0.01"
                  min="0.01"
                  inputMode="decimal"
                  value={editing.precio}
                  onChange={(e) => setEditing((s) => ({ ...s, precio: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Descripción" id="editar-descripcion" hint="Opcional. Aparece debajo del nombre.">
                <input
                  id="editar-descripcion"
                  className="pos-input pos-search-input"
                  name="descripcion"
                  value={editing.descripcion}
                  placeholder="Ej: 500 g, molido fino…"
                  onChange={(e) => setEditing((s) => ({ ...s, descripcion: e.target.value }))}
                />
              </Field>
            </div>
            <div className="pos-form-actions">
              <button type="submit" className="pos-btn pos-btn--primary">
                Guardar cambios
              </button>
              <button type="button" className="pos-btn" onClick={() => setEditing(null)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {isAdmin && adjusting ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Ajustar stock de {adjusting.nombre}</h3>
          <p className="pos-card-desc">
            Stock actual: <strong>{adjusting.stock}</strong>. El ajuste lo suma o lo resta y queda auditado con tu
            usuario y el motivo que indiques.
          </p>
          <form onSubmit={handleAdjust}>
            <div className="pos-fields">
              <Field label="Cantidad" id="ajuste-cantidad" hint="Usa un número negativo para restar.">
                <input
                  id="ajuste-cantidad"
                  className="pos-input pos-search-input"
                  name="delta"
                  type="number"
                  step="1"
                  inputMode="numeric"
                  placeholder="Ej: 5 suma, −3 resta…"
                  value={adjusting.delta}
                  onChange={(e) => setAdjusting((s) => ({ ...s, delta: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Motivo del ajuste" id="ajuste-motivo" hint="Opcional, pero ayuda a explicar el cambio.">
                <input
                  id="ajuste-motivo"
                  className="pos-input pos-search-input"
                  name="motivo"
                  placeholder="Ej: conteo físico, merma…"
                  value={adjusting.motivo}
                  onChange={(e) => setAdjusting((s) => ({ ...s, motivo: e.target.value }))}
                />
              </Field>
            </div>
            <div className="pos-form-actions">
              <button type="submit" className="pos-btn pos-btn--primary">
                Aplicar ajuste
              </button>
              <button type="button" className="pos-btn" onClick={() => setAdjusting(null)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {loading ? (
        <Loading label="Cargando catálogo…" />
      ) : products.length === 0 ? (
        <EmptyState
          title={q ? `Ningún producto coincide con «${q}».` : 'Todavía no hay productos.'}
          hint={q ? 'Prueba con otra parte del nombre o del código.' : 'Crea el primer producto para empezar a vender.'}
        />
      ) : (
        <>
          <table className="pos-table">
            <caption>Catálogo de productos</caption>
            <thead>
              <tr>
                <th scope="col">Código</th>
                <th scope="col">Producto</th>
                <th scope="col" className="num">Precio</th>
                <th scope="col" className="num">Stock</th>
                <th scope="col">Estado</th>
                <th scope="col" className="actions">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <ProductRow
                  key={p.id}
                  product={p}
                  canDeactivate={isAdmin}
                  onDeactivate={handleDeactivate}
                  canManage={isAdmin}
                  onEdit={startEdit}
                  onAdjust={startAdjust}
                  onReactivate={handleReactivate}
                />
              ))}
            </tbody>
          </table>
          <Pager
            page={page}
            hasNext={hasNext}
            count={products.length}
            unit="productos"
            onPrev={() => setPage((p) => Math.max(0, p - 1))}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </section>
  )
}
