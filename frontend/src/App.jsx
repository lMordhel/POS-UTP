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
        {user.username} ({user.rol}) <button onClick={logout}>Salir</button>
      </p>
      <nav>
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)} disabled={active === t.id}>
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
