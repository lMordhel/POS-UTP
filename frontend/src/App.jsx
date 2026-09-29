import { useState } from 'react'
import { ProductsView } from './views/ProductsView.jsx'
import { NewSaleView } from './views/NewSaleView.jsx'
import { SalesView } from './views/SalesView.jsx'

const TABS = [
  { id: 'sale', label: 'Nueva venta' },
  { id: 'products', label: 'Productos' },
  { id: 'sales', label: 'Ventas' },
]

export function App() {
  const [tab, setTab] = useState('sale')
  const [salesRefresh, setSalesRefresh] = useState(0)

  return (
    <main style={{ fontFamily: 'system-ui', maxWidth: 900, margin: '0 auto', padding: 16 }}>
      <h1>POS-UTP</h1>
      <nav>
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)} disabled={tab === t.id}>
            {t.label}
          </button>
        ))}
      </nav>
      {tab === 'sale' ? (
        <NewSaleView onSold={() => setSalesRefresh((n) => n + 1)} />
      ) : tab === 'products' ? (
        <ProductsView />
      ) : (
        <SalesView refreshKey={salesRefresh} />
      )}
    </main>
  )
}
