import { money } from './utils.js'

export function ErrorBanner({ message }) {
  if (!message) return null
  return <p role="alert" className="pos-error">{message}</p>
}

export function NoticeBanner({ message }) {
  if (!message) return null
  return <p role="status" className="pos-notice">{message}</p>
}

export function Loading({ label }) {
  return <p role="status" aria-live="polite" aria-busy="true" className="pos-loading">{label ?? 'Cargando…'}</p>
}

/** Encabezado de sección: título, qué es esta vista y acciones a la derecha. */
export function SectionHead({ title, description, children }) {
  return (
    <header className="pos-section">
      <div>
        <h2 className="pos-section-title">{title}</h2>
        {description ? <p className="pos-section-desc">{description}</p> : null}
      </div>
      {children ? <div className="pos-form-actions">{children}</div> : null}
    </header>
  )
}

/** Campo de formulario con etiqueta visible y pista opcional. */
export function Field({ label, hint, id, children }) {
  return (
    <div className="pos-field">
      <label className="pos-field-label" htmlFor={id}>
        {label}
      </label>
      {children}
      {hint ? <span className="pos-field-hint">{hint}</span> : null}
    </div>
  )
}

/** Etiqueta de estado (activo, sin stock, admin…). */
export function Badge({ tone = 'neutral', children, title }) {
  return (
    <span className={`pos-badge pos-badge--${tone}`} title={title}>
      {children}
    </span>
  )
}

/** Tira de cifras de resumen. */
export function SummaryStrip({ items }) {
  return (
    <div className="pos-summary">
      {items.map((it) => (
        <div className="pos-summary-item" key={it.label}>
          <span className={`pos-summary-value${it.tone ? ` pos-summary-value--${it.tone}` : ''}`}>
            {it.value}
          </span>
          <span className="pos-summary-label">{it.label}</span>
        </div>
      ))}
    </div>
  )
}

/** Estado vacío con título y pista. */
export function EmptyState({ title, hint }) {
  return (
    <div className="pos-empty-box">
      <p className="pos-empty-title">{title}</p>
      {hint ? <p className="pos-empty-hint">{hint}</p> : null}
    </div>
  )
}

export function ProductRow({ product, canDeactivate, onDeactivate, canManage, onEdit, onAdjust, onReactivate }) {
  const sinStock = product.stock === 0
  const pocoStock = !sinStock && product.stock <= 5
  return (
    <tr>
      <td>
        <span className="pos-code" translate="no">{product.codigo}</span>
      </td>
      <td>
        {product.nombre}
        {product.descripcion ? <span className="pos-sub">{product.descripcion}</span> : null}
      </td>
      <td className="num">{money(product.precio)}</td>
      <td className="num">
        {sinStock ? (
          <Badge tone="danger" title="No hay existencias de este producto">Sin stock</Badge>
        ) : pocoStock ? (
          <Badge tone="warn" title="Existencias bajas">{product.stock}</Badge>
        ) : (
          product.stock
        )}
      </td>
      <td>
        {product.activo ? (
          <Badge tone="ok">Activo</Badge>
        ) : (
          <Badge tone="neutral" title="No se puede vender hasta reactivarlo">Inactivo</Badge>
        )}
      </td>
      <td className="actions">
        {product.activo && canManage ? (
          <>
            <button type="button" className="pos-btn" onClick={() => onEdit(product)}>
              Editar
            </button>
            <button type="button" className="pos-btn" onClick={() => onAdjust(product)}>
              Ajustar stock
            </button>
          </>
        ) : null}
        {product.activo && canDeactivate ? (
          <button type="button" className="pos-btn pos-btn--ghost pos-btn--danger" onClick={() => onDeactivate(product.id)}>
            Desactivar
          </button>
        ) : null}
        {!product.activo && canManage ? (
          <button type="button" className="pos-btn pos-btn--ghost" onClick={() => onReactivate(product.id)}>
            Reactivar
          </button>
        ) : null}
      </td>
    </tr>
  )
}

export function SaleRow({ sale, onSelect }) {
  return (
    <tr>
      <td>{sale.id}</td>
      {/* SPEC-FRONT-008 (AC-FRONT08-02): fecha en es-PE y en 24 horas; sin
          locale el navegador usa en-US y muestra "9/28/2026, 9:15:07 PM". */}
      <td>
        {sale.fecha
          ? new Date(sale.fecha).toLocaleString('es-PE', {
              day: '2-digit',
              month: '2-digit',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
              hour12: false,
            })
          : ''}
      </td>
      <td className="num">{money(sale.total)}</td>
      <td>{sale.estado}</td>
      <td className="actions">
        <button type="button" className="pos-btn" onClick={() => onSelect(sale.id)}>Ver detalle</button>
      </td>
    </tr>
  )
}

export function Pager({ page, hasNext, onPrev, onNext, count, unit = 'elementos' }) {
  return (
    <div className="pos-pager">
      <span className="pos-pager-count">
        {count !== undefined ? `${count} ${unit} en esta página · ` : ''}Página {page + 1}
      </span>
      <div className="pos-pager-controls">
        <button type="button" className="pos-btn" onClick={onPrev} disabled={page === 0}>
          Anterior
        </button>
        <button type="button" className="pos-btn" onClick={onNext} disabled={!hasNext}>
          Siguiente
        </button>
      </div>
    </div>
  )
}
