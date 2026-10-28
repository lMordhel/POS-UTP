/**
 * S4: un rechazo de negocio no puede cerrar la sesión del cajero.
 *
 * `request()` reintenta una vez tras refrescar el par. Antes del fix, cualquier
 * respuesta no-2xx del reintento llamaba `onUnauthorized()`: un 409 por stock
 * insuficiente expulsaba al usuario y le borraba el carrito en el flujo más
 * crítico de la app. Sólo un 401 definitivo cierra sesión.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { salesApi, setAuthStore } from './api.js'

function json(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetchSequence(steps) {
  const calls = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, options = {}) => {
      calls.push({ url: String(url), method: options.method ?? 'GET' })
      const step = steps.shift()
      if (!step) throw new Error(`fetch inesperado: ${url}`)
      return step()
    }),
  )
  return calls
}

let onUnauthorized

beforeEach(() => {
  onUnauthorized = vi.fn()
  setAuthStore({
    getAccess: () => 'access-vencido',
    getRefresh: () => 'refresh-vigente',
    setTokens: vi.fn(),
    onUnauthorized,
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('reintento tras refrescar el par', () => {
  it('no cierra sesión cuando el reintento falla por falta de stock (409)', async () => {
    const calls = mockFetchSequence([
      () => json(401, { detail: 'credenciales inválidas' }),
      () => json(200, { access_token: 'access-nuevo', refresh_token: 'refresh-nuevo' }),
      () =>
        json(409, {
          detail: 'stock insuficiente producto=2: disponible=0, solicitado=1',
        }),
    ])

    await expect(
      salesApi.create([{ producto_id: 2, cantidad: 1 }]),
    ).rejects.toMatchObject({ status: 409 })

    expect(onUnauthorized).not.toHaveBeenCalled()
    expect(calls).toHaveLength(3)
    expect(calls[1].url).toContain('/api/v1/auth/refresh')
  })

  it('devuelve el dato cuando el reintento sale bien', async () => {
    mockFetchSequence([
      () => json(401, { detail: 'credenciales inválidas' }),
      () => json(200, { access_token: 'access-nuevo', refresh_token: 'refresh-nuevo' }),
      () => json(200, [{ id: 1, total: '10.50' }]),
    ])

    await expect(salesApi.list()).resolves.toEqual([{ id: 1, total: '10.50' }])
    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('cierra sesión cuando el reintento vuelve a dar 401', async () => {
    mockFetchSequence([
      () => json(401, { detail: 'credenciales inválidas' }),
      () => json(200, { access_token: 'access-nuevo', refresh_token: 'refresh-nuevo' }),
      () => json(401, { detail: 'credenciales inválidas' }),
    ])

    await expect(salesApi.list()).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('cierra sesión cuando el refresh ya no sirve', async () => {
    mockFetchSequence([
      () => json(401, { detail: 'credenciales inválidas' }),
      () => json(401, { detail: 'refresh reutilizado: familia revocada' }),
    ])

    await expect(salesApi.list()).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })
})
