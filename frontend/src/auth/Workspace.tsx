import { lazy, Suspense, useEffect, useState } from 'react'
import { Dashboard } from '../dashboard/Dashboard'
import { Goals } from '../goals/Goals'
import { RecordsPage } from '../records/RecordsPage'
import type { Domain } from '../records/records-api'
import { authClient } from './auth-client'
import { disablePush } from '../features/push-client'
import { NavIcon } from '../features/NavIcon'
import '../features/features.css'
const AssistantHub = lazy(() => import('../features/AssistantHub').then(m => ({ default: m.AssistantHub })))
const RemindersPage = lazy(() => import('../features/RemindersPage').then(m => ({ default: m.RemindersPage })))
const SettingsHub = lazy(() => import('../features/SettingsHub').then(m => ({ default: m.SettingsHub })))
const OpportunitiesHub = lazy(() => import('../features/OpportunitiesHub').then(m => ({ default: m.OpportunitiesHub })))
type Page = 'home' | Domain | 'goals' | 'settings' | 'assistant' | 'notifications'
type WorkspaceProps = { email: string; name?: string; onSignedOut: () => Promise<void> }
const nav: { id: Page; label: string; group?: string }[] = [
  { id: 'home', label: 'Overview', group: 'Your day' },
  { id: 'assistant', label: 'AI Assistant' },
  { id: 'tasks', label: 'Tasks', group: 'Workspace' },
  { id: 'projects', label: 'Projects' },
  { id: 'goals', label: 'Goals' },
  { id: 'learning', label: 'Learning' },
  { id: 'academics', label: 'Academics' },
  { id: 'opportunities', label: 'Opportunities' },
  { id: 'notifications', label: 'Notifications', group: 'Personal' },
  { id: 'settings', label: 'Settings' },
]

export function Workspace({ email, name, onSignedOut }: WorkspaceProps) {
  const [openCreate, setOpenCreate] = useState(false)
  const [page, setPage] = useState<Page>(() => new URLSearchParams(location.search).has('chat') ? 'assistant' : new URLSearchParams(location.search).get('view') === 'notifications' ? 'notifications' : 'home'); const [sidebarOpen, setSidebarOpen] = useState(false); const [menuOpen, setMenuOpen] = useState(false); const [isSigningOut, setIsSigningOut] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (localStorage.getItem('momentum-theme') as 'light' | 'dark') || (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem('momentum-theme', theme) }, [theme])
  const [signOutError, setSignOutError] = useState('')
  async function signOut() {
    if (isSigningOut) return
    setIsSigningOut(true)
    setSignOutError('')
    try {
      try { await disablePush() } catch { /* Sign-out must remain available if push cleanup fails. */ }
      const result = await authClient.signOut()
      if (result.error) throw new Error('Sign-out failed')
      await onSignedOut()
    } catch {
      setSignOutError('Could not sign out. Please try again.')
    } finally { setIsSigningOut(false) }
  }
  function go(next: Page, create = false) {
    if (next !== 'assistant') {
      const url = new URL(location.href)
      url.searchParams.delete('chat')
      history.replaceState(history.state, '', url)
    }
    setOpenCreate(create)
    setPage(next)
    setSidebarOpen(false)
  }
  const current = nav.find((item) => item.id === page)?.label ?? 'Home'
  return <div className="app-shell"><aside className={`sidebar ${sidebarOpen ? 'sidebar-open' : ''}`} aria-label="Primary navigation"><div className="brand"><span className="brand-mark">M</span><span>Momentum</span><button className="mobile-close" aria-label="Close navigation" onClick={() => setSidebarOpen(false)}>×</button></div><nav>{nav.map((item) => <div key={item.id}>{item.group && <p className="nav-group">{item.group}</p>}<button aria-current={page === item.id ? 'page' : undefined} className={page === item.id ? 'nav-active' : ''} onClick={() => go(item.id)}><NavIcon name={item.id} />{item.label}</button></div>)}</nav><div className="sidebar-footer"><span className="status-dot" /> Your personal workspace</div></aside>{sidebarOpen && <button className="scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
    <main className="app-main"><header className="topbar"><button className="menu-button" aria-label="Open navigation" onClick={() => setSidebarOpen(true)}>☰</button><div><p className="eyebrow">Workspace</p><strong>{current}</strong></div><div className="topbar-actions"><button className="icon-button" aria-label="Toggle color theme" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? '☀' : '◐'}</button><button className="sr-only" disabled={isSigningOut} onClick={() => void signOut()}>{isSigningOut ? 'Signing out…' : 'Sign out'}</button><div className="account"><button className="account-button" onClick={() => setMenuOpen(!menuOpen)} aria-expanded={menuOpen}><span>{email.slice(0, 1).toUpperCase()}</span><i>{email}</i></button>{menuOpen && <div className="account-menu"><button onClick={() => go('settings')}>Settings</button><button onClick={() => void signOut()} disabled={isSigningOut}>{isSigningOut ? 'Signing out…' : 'Sign out'}</button></div>}</div></div></header><div className={`page-content ${page === 'assistant' ? 'assistant-content' : ''}`}>{signOutError && <p role="alert" className="notice-error">{signOutError}</p>}{page === 'home' ? <Dashboard name={name} onNavigate={go} onCreate={domain => go(domain, true)} /> : page === 'goals' ? <Goals /> : page === 'settings' ? <Suspense fallback={<p role="status">Loading settings…</p>}><SettingsHub /></Suspense> : page === 'assistant' ? <Suspense fallback={<p role="status">Loading assistant…</p>}><AssistantHub /></Suspense> : page === 'notifications' ? <Suspense fallback={<p role="status">Loading notifications…</p>}><RemindersPage /></Suspense> : page === 'opportunities' ? <Suspense fallback={<p role="status">Loading opportunities…</p>}><OpportunitiesHub openCreate={openCreate} /></Suspense> : <RecordsPage key={page} domain={page} openCreate={openCreate} />}</div></main></div>
}
