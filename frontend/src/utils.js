export const PAGE_SIZE = 20

const moneyFormatter = new Intl.NumberFormat('es-PE', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  useGrouping: false,
})

export function money(value) {
  const n = Number(value)
  return Number.isFinite(n) ? moneyFormatter.format(n) : String(value)
}

export function apiErrorMessage(err) {
  if (err.status === 401) return 'Sesión vencida o credenciales inválidas. Entra de nuevo.'
  if (err.status === 403) return 'Sin permiso para esta operación.'
  if (err.status === 409) return 'Stock insuficiente para uno o más productos.'
  if (err.status === 404) return 'Producto, venta o usuario no encontrado.'
  if (err.status === 422) return 'Datos inválidos. Revisa cantidades y campos.'
  if (err.status === 429) return 'Demasiados intentos. Reintenta en un momento.'
  if (err.status === 502) return 'Servicio no disponible. Intenta de nuevo.'
  return 'Error de red o del servidor. Intenta de nuevo.'
}
