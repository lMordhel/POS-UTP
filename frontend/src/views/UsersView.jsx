import { useCallback, useEffect, useState } from 'react'
import { authApi } from '../api.js'
import { PAGE_SIZE, apiErrorMessage } from '../utils.js'
import { Badge, EmptyState, ErrorBanner, Field, Loading, NoticeBanner, Pager, SectionHead } from '../components.jsx'

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
  const [showCreate, setShowCreate] = useState(false)
  const [showLegend, setShowLegend] = useState(false)

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
      setShowCreate(false)
      setNotice(`Usuario ${form.username} creado.`)
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
      setNotice(`${user.username} quedó ${user.activo ? 'desactivado' : 'activado'}.`)
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

  const activos = users.filter((u) => u.activo).length

  return (
    <section>
      <SectionHead
        title="Usuarios"
        description="Quién puede entrar al sistema y qué puede hacer dentro del punto de venta."
      >
        <Badge tone="info">
          {users.length} en esta página · {activos} activos
        </Badge>
        <button
          type="button"
          className="pos-btn"
          aria-expanded={showLegend}
          onClick={() => setShowLegend((v) => !v)}
        >
          {showLegend ? 'Ocultar roles' : '¿Qué hace cada rol?'}
        </button>
        <button
          type="button"
          className="pos-btn pos-btn--primary"
          aria-expanded={showCreate}
          onClick={() => setShowCreate((v) => !v)}
        >
          {showCreate ? 'Cancelar alta' : 'Nuevo usuario'}
        </button>
      </SectionHead>

      <ErrorBanner message={error} />
      <NoticeBanner message={notice} />

      {showLegend ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Roles del sistema</h3>
          <p className="pos-card-desc">
            El backend aplica estos permisos en cada operación: ocultar un botón en la pantalla no es la protección.
          </p>
          <ul className="pos-legend">
            <li className="pos-legend-item">
              <Badge tone="info">admin</Badge>
              <span>
                <strong>Administrador.</strong> Gestiona el catálogo de productos, crea y edita usuarios, ajusta
                existencias y consulta toda la auditoría de inventario.
              </span>
            </li>
            <li className="pos-legend-item">
              <Badge tone="neutral">cajero</Badge>
              <span>
                <strong>Cajero.</strong> Registra ventas y consulta productos, existencias y ventas. No puede crear
                usuarios, editar el catálogo ni ajustar existencias.
              </span>
            </li>
          </ul>
        </div>
      ) : null}

      {showCreate ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Nuevo usuario</h3>
          <p className="pos-card-desc">
            El usuario podrá entrar con estos datos desde la pantalla de inicio de sesión.
          </p>
          <form onSubmit={handleCreate}>
            <div className="pos-fields">
              <Field label="Usuario" id="nuevo-usuario" hint="Con este nombre inicia sesión.">
                <input
                  id="nuevo-usuario"
                  className="pos-input pos-search-input"
                  name="username"
                  value={form.username}
                  autoComplete="off"
                  spellCheck={false}
                  placeholder="Ej: caja1…"
                  onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Contraseña" id="nuevo-password" hint="Mínimo 8 caracteres.">
                <input
                  id="nuevo-password"
                  className="pos-input pos-search-input"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={form.password}
                  placeholder="Mínimo 8 caracteres…"
                  onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  required
                />
              </Field>
              <Field label="Rol" id="nuevo-rol" hint="Define qué puede hacer en el punto de venta.">
                <select
                  id="nuevo-rol"
                  className="pos-select"
                  name="rol"
                  value={form.rol}
                  onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}
                >
                  <option value="cajero">Cajero — registra ventas y consulta</option>
                  <option value="admin">Administrador — gestión completa</option>
                </select>
              </Field>
            </div>
            <div className="pos-form-actions">
              <button type="submit" className="pos-btn pos-btn--primary">
                Crear usuario
              </button>
              <button type="button" className="pos-btn" onClick={() => setShowCreate(false)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {resetting ? (
        <div className="pos-card">
          <h3 className="pos-card-head">Cambiar la clave de {resetting.username}</h3>
          <p className="pos-card-desc">La clave anterior deja de ser válida en el siguiente inicio de sesión.</p>
          <form onSubmit={handleReset}>
            <div className="pos-fields">
              <Field label="Nueva contraseña" id="reset-password" hint="Mínimo 8 caracteres.">
                <input
                  id="reset-password"
                  className="pos-input pos-search-input"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  value={resetting.password}
                  placeholder="Mínimo 8 caracteres…"
                  onChange={(e) => setResetting((s) => ({ ...s, password: e.target.value }))}
                  required
                />
              </Field>
            </div>
            <div className="pos-form-actions">
              <button type="submit" className="pos-btn pos-btn--primary">
                Guardar clave
              </button>
              <button type="button" className="pos-btn" onClick={() => setResetting(null)}>
                Cancelar
              </button>
            </div>
          </form>
        </div>
      ) : null}

      {loading ? (
        <Loading label="Cargando usuarios…" />
      ) : users.length === 0 ? (
        <EmptyState title="Todavía no hay usuarios." hint="Crea el primer usuario para que pueda entrar al sistema." />
      ) : (
        <>
          <table className="pos-table">
            <caption>Usuarios con acceso al punto de venta</caption>
            <thead>
              <tr>
                <th scope="col">Usuario</th>
                <th scope="col">Rol</th>
                <th scope="col">Estado</th>
                <th scope="col" className="actions">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <span className="pos-code" translate="no">{u.username}</span>
                  </td>
                  <td>
                    <Badge tone={u.rol === 'admin' ? 'info' : 'neutral'} title={u.rol === 'admin' ? 'Administrador: gestión completa' : 'Cajero: registra ventas y consulta'}>
                      {u.rol}
                    </Badge>
                  </td>
                  <td>
                    {u.activo ? (
                      <Badge tone="ok" title="Puede iniciar sesión">Activo</Badge>
                    ) : (
                      <Badge tone="danger" title="No puede iniciar sesión">Desactivado</Badge>
                    )}
                  </td>
                  <td className="actions">
                    <button type="button" className="pos-btn" onClick={() => startReset(u)}>
                      Cambiar clave
                    </button>
                    <button
                      type="button"
                      className={u.activo ? 'pos-btn pos-btn--ghost pos-btn--danger' : 'pos-btn pos-btn--ghost'}
                      onClick={() => handleToggle(u)}
                    >
                      {u.activo ? 'Desactivar' : 'Activar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pager
            page={page}
            hasNext={hasNext}
            count={users.length}
            unit="usuarios"
            onPrev={() => setPage((p) => Math.max(0, p - 1))}
            onNext={() => setPage((p) => p + 1)}
          />
        </>
      )}
    </section>
  )
}
