import { useState } from 'react'
import { AuthProvider, useAuth } from './auth.jsx'
import { ProductsView } from './views/ProductsView.jsx'
import { NewSaleView } from './views/NewSaleView.jsx'
import { SalesView } from './views/SalesView.jsx'
import { LoginView } from './views/LoginView.jsx'
import { UsersView } from './views/UsersView.jsx'
import { AuditView } from './views/AuditView.jsx'

function Shell() {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState('sale')
  const [salesRefresh, setSalesRefresh] = useState(0)

  if (!user) return <LoginView />

  const isAdmin = user.rol === 'admin'
  const TABS = [
    { id: 'sale', label: 'Nueva venta' },
    { id: 'products', label: 'Productos' },
    { id: 'sales', label: 'Ventas' },
    ...(isAdmin ? [{ id: 'users', label: 'Usuarios' }, { id: 'audit', label: 'Auditoría' }] : []),
  ]
  const active = TABS.some((t) => t.id === tab) ? tab : 'sale'

  return (
    <>
      <p>
        {user.username} ({user.rol}) <button type="button" className="pos-btn" onClick={logout}>Salir</button>
      </p>
      {/* SPEC-FRONT-008 (AC-FRONT08-05): la pestaña activa se marca con
          aria-current y con estilo propio en vez de quedar deshabilitada, que
          le quitaba el foco visible al teclado. */}
      <nav className="pos-tabs" aria-label="Secciones del punto de venta">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            className={active === t.id ? 'pos-btn pos-tab pos-tab--active' : 'pos-btn pos-tab'}
            aria-current={active === t.id ? 'page' : undefined}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      {active === 'sale' ? (
        <NewSaleView onSold={() => setSalesRefresh((n) => n + 1)} />
      ) : active === 'products' ? (
        <ProductsView isAdmin={isAdmin} />
      ) : active === 'users' && isAdmin ? (
        <UsersView />
      ) : active === 'audit' && isAdmin ? (
        <AuditView />
      ) : (
        <SalesView refreshKey={salesRefresh} />
      )}
    </>
  )
}

export function App() {
  return (
    <main style={{ fontFamily: 'system-ui', maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h1>POS-UTP</h1>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </main>
  )
}
