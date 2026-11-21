import { useEffect, useState } from 'react'
import type { ReactElement } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { getData } from '../pages/invoices/documentModel'

type NavItem = { to: string; label: string; icon: (props: { className?: string }) => ReactElement }

const icon = (d: string) => ({ className }: { className?: string }) => (
  <svg aria-hidden="true" className={className} width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
)

const icons = {
  home: icon('m3 11 9-8 9 8M5 10v10h5v-6h4v6h5V10'),
  clients: icon('M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0ZM4 21c0-4.4 3.6-7 8-7s8 2.6 8 7'),
  suppliers: icon('M3 7h18M5 7v12h14V7M9 11h6M9 15h3M3 7l2-4h14l2 4'),
  catalogue: icon('m3.5 7 8.5-4 8.5 4-8.5 4-8.5-4Zm0 0v10l8.5 4m0-10v10m0-10 8.5-4v10l-8.5 4'),
  invoices: icon('M7 3h10l2 3v15H5V6l2-3Zm0 7h10M7 14h10M7 18h6'),
  quotes: icon('M8 3h8l3 3v15H5V6l3-3Zm3 7h.01M9 14h6M9 17h6'),
  payments: icon('M3 7h18v12H3V7Zm0 4h18M7 15h3'),
  settings: icon('M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm8-3a7.9 7.9 0 0 0-.2-1.8l2-1.6-2-3.4-2.4 1a8 8 0 0 0-3.1-1.8L14 2h-4l-.3 2.4a8 8 0 0 0-3.1 1.8l-2.4-1-2 3.4 2 1.6A7.9 7.9 0 0 0 4 12c0 .6 0 1.2.2 1.8l-2 1.6 2 3.4 2.4-1a8 8 0 0 0 3.1 1.8L10 22h4l.3-2.4a8 8 0 0 0 3.1-1.8l2.4 1 2-3.4-2-1.6c.1-.6.2-1.2.2-1.8Z'),
  integrations: icon('M9 3v4M15 3v4M4 9h16M6 7h12a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Zm3 7h6'),
  chevronDown: icon('m6 9 6 6 6-6'),
  panelLeft: icon('M4 4h16v16H4zM9 4v16'),
  logout: icon('M15 16l4-4m0 0-4-4m4 4H9m0-9H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h4'),
  sun: icon('M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10ZM12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1'),
  moon: icon('M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z'),
}

type Theme = 'light' | 'dark'

function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    try {
      const stored = localStorage.getItem('docforge-theme')
      if (stored === 'light' || stored === 'dark') return stored
    } catch { /* private window: ignore */ }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('docforge-theme', theme) } catch { /* private window: ignore */ }
  }, [theme])
  return [theme, setTheme] as const
}

type NavEntry = { kind: 'item'; item: NavItem } | { kind: 'group'; label: string; items: NavItem[] }

const navEntries: NavEntry[] = [
  { kind: 'item', item: { to: '/', label: 'Tableau de bord', icon: icons.home } },
  { kind: 'item', item: { to: '/clients', label: 'Clients', icon: icons.clients } },
  { kind: 'item', item: { to: '/suppliers', label: 'Fournisseurs', icon: icons.suppliers } },
  { kind: 'item', item: { to: '/catalogue/products', label: 'Catalogue', icon: icons.catalogue } },
  {
    kind: 'group',
    label: 'Facturation',
    items: [
      { to: '/invoices', label: 'Factures', icon: icons.invoices },
      { to: '/quotes', label: 'Devis', icon: icons.quotes },
      { to: '/payments', label: 'Paiements', icon: icons.payments },
    ],
  },
  {
    kind: 'group',
    label: 'Organisation',
    items: [
      { to: '/settings/company', label: 'Paramètres', icon: icons.settings },
      { to: '/settings/integrations', label: 'Intégrations', icon: icons.integrations },
    ],
  },
]

function usePersistentState(key: string, initial: boolean) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key)
      return stored === null ? initial : stored === '1'
    } catch { return initial }
  })
  useEffect(() => {
    try { localStorage.setItem(key, value ? '1' : '0') } catch { /* private window: ignore */ }
  }, [key, value])
  return [value, setValue] as const
}

function NavRow({ item, collapsed, nested = false }: { item: NavItem; collapsed: boolean; nested?: boolean }) {
  return (
    <NavLink
      to={item.to}
      end={item.to === '/'}
      title={collapsed ? item.label : undefined}
      className={({ isActive }) =>
        `press focus-ring flex items-center gap-3 rounded-lg py-2 text-sm font-medium transition-colors duration-100 ease-out ${
          collapsed ? 'justify-center px-0' : nested ? 'pl-9 pr-3' : 'px-3'
        } ${isActive ? 'bg-accent text-white' : 'text-text-muted hover:bg-surface-muted hover:text-text'}`
      }
    >
      <item.icon className="shrink-0" />
      {!collapsed && <span className="truncate">{item.label}</span>}
    </NavLink>
  )
}

function NavGroup({ label, items, collapsed }: { label: string; items: NavItem[]; collapsed: boolean }) {
  const [open, setOpen] = usePersistentState(`docforge-nav-group-${label}`, true)
  if (collapsed) {
    return <div className="space-y-1">{items.map((item) => <NavRow key={item.to} item={item} collapsed />)}</div>
  }
  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="focus-ring flex w-full items-center justify-between rounded-lg px-3 py-2 text-xs font-semibold uppercase tracking-wide text-text-faint hover:text-text-muted"
      >
        {label}
        <icons.chevronDown className={`transition-transform duration-150 ease-out ${open ? '' : '-rotate-90'}`} />
      </button>
      <div hidden={!open} className="space-y-1">
        {items.map((item) => <NavRow key={item.to} item={item} collapsed={false} nested />)}
      </div>
    </div>
  )
}

export function AppLayout() {
  const { logout } = useAuth()
  const [collapsed, setCollapsed] = usePersistentState('docforge-sidebar-collapsed', false)
  const [theme, setTheme] = useTheme()
  const location = useLocation()
  const enterprise = useQuery({
    queryKey: ['sidebar-enterprise'],
    queryFn: ({ signal }) => getData<{ legal_name: string; trade_name: string | null; slug: string }>('/tenant/me', signal),
    staleTime: 5 * 60_000,
  })
  const name = enterprise.data?.trade_name || enterprise.data?.legal_name || 'DocForge'

  return (
    <div className="flex min-h-svh bg-bg text-text">
      <aside className={`hidden flex-col border-r border-border bg-surface py-4 transition-[width] duration-200 ease-out lg:flex ${collapsed ? 'w-[72px] px-2' : 'w-64 px-3'}`}>
        <div className={`mb-4 flex items-center gap-2 rounded-lg px-2 py-1.5 ${collapsed ? 'justify-center' : ''}`}>
          <span
            className="grid h-8 w-8 shrink-0 place-items-center rounded-md text-sm font-bold text-white"
            style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-secondary))' }}
          >
            {name.slice(0, 1).toUpperCase()}
          </span>
          {!collapsed && (
            <>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold leading-tight">{name}</div>
                <div className="text-xs text-text-faint">DocForge</div>
              </div>
              <button
                type="button"
                onClick={() => setCollapsed(true)}
                aria-pressed={false}
                title="Replier le menu"
                className="press focus-ring shrink-0 rounded-md p-1.5 text-text-faint hover:bg-surface-muted hover:text-text"
              >
                <icons.panelLeft className="shrink-0" />
              </button>
            </>
          )}
        </div>
        {collapsed && (
          <button
            type="button"
            onClick={() => setCollapsed(false)}
            aria-pressed={true}
            title="Déplier le menu"
            className="press focus-ring mb-3 flex w-full items-center justify-center rounded-md py-1.5 text-text-faint hover:bg-surface-muted hover:text-text"
          >
            <icons.panelLeft className="shrink-0" />
          </button>
        )}

        <nav className="flex flex-1 flex-col gap-3 overflow-y-auto">
          {navEntries.map((entry, i) =>
            entry.kind === 'item'
              ? <NavRow key={entry.item.to} item={entry.item} collapsed={collapsed} />
              : <NavGroup key={i} label={entry.label} items={entry.items} collapsed={collapsed} />
          )}
        </nav>

        <div className="mt-3 space-y-1 border-t border-border pt-3">
          <button
            type="button"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title={collapsed ? (theme === 'dark' ? 'Mode clair' : 'Mode sombre') : undefined}
            aria-pressed={theme === 'dark'}
            className={`press focus-ring group flex w-full items-center gap-3 rounded-lg py-2 text-sm font-medium text-text-muted hover:bg-surface-muted hover:text-text ${collapsed ? 'justify-center px-0' : 'px-3'}`}
          >
            {theme === 'dark'
              ? <icons.sun className="shrink-0 transition-colors duration-150 ease-out group-hover:text-accent-secondary" />
              : <icons.moon className="shrink-0 transition-colors duration-150 ease-out group-hover:text-accent-secondary" />}
            {!collapsed && (theme === 'dark' ? 'Mode clair' : 'Mode sombre')}
          </button>
          <button
            type="button"
            onClick={logout}
            title={collapsed ? 'Se déconnecter' : undefined}
            className={`press focus-ring flex w-full items-center gap-3 rounded-lg py-2 text-sm font-medium text-text-muted hover:bg-surface-muted hover:text-text ${collapsed ? 'justify-center px-0' : 'px-3'}`}
          >
            <icons.logout className="shrink-0" />
            {!collapsed && 'Se déconnecter'}
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div key={location.pathname} className="page-transition mx-auto max-w-[1280px] px-6 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
