export function money(value) {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(2) : String(value)
}

export function apiErrorMessage(err) {
  if (err.status === 409) return 'Stock insuficiente para uno o más productos.'
  if (err.status === 404) return 'Producto o venta no encontrada.'
  if (err.status === 422) return 'Datos inválidos. Revisa cantidades y campos.'
  if (err.status === 502) return 'Servicio de stock no disponible. Intenta de nuevo.'
  return 'Error de red o del servidor. Intenta de nuevo.'
}
