import { money } from './utils.js'

export function ErrorBanner({ message }) {
  if (!message) return null
  return <p role="alert" style={{ color: 'crimson' }}>{message}</p>
}

export function Loading({ label }) {
  return <p>{label ?? 'Cargando...'}</p>
}

export function ProductRow({ product, canDeactivate, onDeactivate, canManage, onEdit, onAdjust }) {
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
      <td>{sale.fecha ? new Date(sale.fecha).toLocaleString() : ''}</td>
      <td>{money(sale.total)}</td>
      <td>{sale.estado}</td>
      <td>
        <button onClick={() => onSelect(sale.id)}>Ver</button>
      </td>
    </tr>
  )
}
