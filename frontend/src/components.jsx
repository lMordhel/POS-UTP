import { money } from './utils.js'

export function ErrorBanner({ message }) {
  if (!message) return null
  return <p role="alert" className="pos-error">{message}</p>
}

export function Loading({ label }) {
  return <p role="status" aria-live="polite" aria-busy="true" className="pos-loading">{label ?? 'Cargando...'}</p>
}

export function ProductRow({ product, canDeactivate, onDeactivate, canManage, onEdit, onAdjust, onReactivate }) {
  return (
    <tr>
      <td>{product.codigo}</td>
      <td>{product.nombre}</td>
      <td>{money(product.precio)}</td>
      <td>{product.stock}</td>
      <td>{product.activo ? 'Sí' : 'No'}</td>
      <td>
        {product.activo && canDeactivate ? (
          <button onClick={() => onDeactivate(product.id)}>Desactivar</button>
        ) : null}
        {!product.activo && canManage ? (
          <button onClick={() => onReactivate(product.id)}>Reactivar</button>
        ) : null}
        {product.activo && canManage ? (
          <>
            <button onClick={() => onEdit(product)}>Editar</button>
            <button onClick={() => onAdjust(product)}>Ajustar</button>
          </>
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
      <td>{money(sale.total)}</td>
      <td>{sale.estado}</td>
      <td>
        <button className="pos-btn" onClick={() => onSelect(sale.id)}>Ver</button>
      </td>
    </tr>
  )
}

export function Pager({ page, hasNext, onPrev, onNext }) {
  return (
    <div>
      <button onClick={onPrev} disabled={page === 0}>Anterior</button>
      <span>Página {page + 1}</span>
      <button onClick={onNext} disabled={!hasNext}>Siguiente</button>
    </div>
  )
}
