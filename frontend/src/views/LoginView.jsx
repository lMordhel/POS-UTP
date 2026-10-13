import { useState } from 'react'
import { useAuth } from '../auth.jsx'
import { apiErrorMessage } from '../utils.js'
import { ErrorBanner } from '../components.jsx'

export function LoginView() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [sending, setSending] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Usuario y contraseña son obligatorios.')
      return
    }
    setSending(true)
    setError('')
    try {
      await login(username.trim(), password)
    } catch (err) {
      setError(apiErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  return (
    <section>
      <h2>Iniciar sesión</h2>
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit}>
        <input placeholder="Usuario" value={username} autoComplete="username"
          onChange={(e) => setUsername(e.target.value)} required />
        <input placeholder="Contraseña" type="password" value={password} autoComplete="current-password"
          onChange={(e) => setPassword(e.target.value)} required />
        <button type="submit" disabled={sending}>{sending ? 'Entrando...' : 'Entrar'}</button>
      </form>
    </section>
  )
}
