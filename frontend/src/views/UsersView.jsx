import { useCallback, useEffect, useState } from 'react'
import { authApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { ErrorBanner, Loading, Pager } from '../components.jsx'

const EMPTY_FORM = { username: '', password: '', rol: 'cajero' }

export function UsersView() {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [page, setPage] = useState(0)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [resetting, setResetting] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const items = await authApi.users.list({ skip: page * PAGE_SIZE })
      if (items.length === 0 && page > 0) {
        setPage((p) => p - 1)
        return
      }
      setHasNext(items.length > PAGE_SIZE)
      setUsers(items.slice(0, PAGE_SIZE))
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => {
    load()
  }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    setNotice('')
    try {
      await authApi.users.create(form)
      setForm(EMPTY_FORM)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  async function handleToggle(user) {
    setError('')
    setNotice('')
    try {
      await authApi.users.update(user.id, { activo: !user.activo })
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  function startReset(user) {
    setError('')
    setNotice('')
    setResetting({ id: user.id, username: user.username, password: '' })
  }

  async function handleReset(e) {
    e.preventDefault()
    if (!resetting.password || resetting.password.length < 8) {
      setError('La nueva clave debe tener al menos 8 caracteres.')
      return
    }
    setError('')
    setNotice('')
    try {
      await authApi.users.update(resetting.id, { password: resetting.password })
      setResetting(null)
      setNotice(`Clave de ${resetting.username} actualizada.`)
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <section>
      <h2>Usuarios</h2>
      <ErrorBanner message={error} />
      {notice ? <p style={{ color: 'green' }}>{notice}</p> : null}
      <form onSubmit={handleCreate}>
        <input placeholder="Usuario" value={form.username}
          onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))} required />
        <input placeholder="Contraseña (mín. 8)" type="password" value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} required />
        <select value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}>
          <option value="cajero">cajero</option>
          <option value="admin">admin</option>
        </select>
        <button type="submit">Crear</button>
      </form>
      {resetting ? (
        <form onSubmit={handleReset}>
          <h3>Cambiar clave de {resetting.username}</h3>
          <label>
            Nueva contraseña (mín. 8 caracteres)
            <input type="password" value={resetting.password}
              onChange={(e) => setResetting((s) => ({ ...s, password: e.target.value }))} required />
          </label>
          <button type="submit">Guardar clave</button>
          <button type="button" onClick={() => setResetting(null)}>Cancelar</button>
        </form>
      ) : null}
      {loading ? (
        <Loading />
      ) : (
        <>
          <table>
            <thead>
              <tr><th>Usuario</th><th>Rol</th><th>Activo</th><th /></tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.rol}</td>
                  <td>{u.activo ? 'Sí' : 'No'}</td>
                  <td>
                    <button onClick={() => handleToggle(u)}>
                      {u.activo ? 'Desactivar' : 'Activar'}
                    </button>
                    <button onClick={() => startReset(u)}>Cambiar clave</button>
                  </td>
                </tr>
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
