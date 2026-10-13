import { useCallback, useEffect, useState } from 'react'
import { authApi } from '../api.js'
import { apiErrorMessage } from '../utils.js'
import { ErrorBanner, Loading } from '../components.jsx'

const EMPTY_FORM = { username: '', password: '', rol: 'cajero' }

export function UsersView() {
  const [users, setUsers] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setUsers(await authApi.users.list())
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
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
    try {
      await authApi.users.update(user.id, { activo: !user.activo })
      await load()
    } catch (err) {
      setError(apiErrorMessage(err))
    }
  }

  return (
    <section>
      <h2>Usuarios</h2>
      <ErrorBanner message={error} />
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
      {loading ? (
        <Loading />
      ) : (
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
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
