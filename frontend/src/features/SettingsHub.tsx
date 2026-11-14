import { lazy, Suspense, useState } from 'react'
import { OnboardingPreferences } from '../onboarding/OnboardingPreferences'
const Memory = lazy(() => import('./MemoryPage').then(m => ({ default: m.MemoryPage })))
const AccountData = lazy(() => import('./AccountData').then(m => ({ default: m.AccountData })))
export function SettingsHub() {
  const [view, setView] = useState<'profile' | 'memory' | 'data'>('profile')
  return <section><div className="page-heading"><div><p className="eyebrow">Make Momentum yours</p><h1>Settings</h1><p className="page-subtitle">Your preferences and the context your assistant can use.</p></div></div><nav className="mode-switch compact-switch" aria-label="Settings section"><button aria-pressed={view === 'profile'} onClick={() => setView('profile')}>Profile & preferences</button><button aria-pressed={view === 'memory'} onClick={() => setView('memory')}>AI memory & privacy</button><button aria-pressed={view === 'data'} onClick={() => setView('data')}>Data & support</button></nav>{view === 'profile' ? <OnboardingPreferences><div /></OnboardingPreferences> : <Suspense fallback={<p role="status">Loading settings…</p>}>{view === 'memory' ? <Memory /> : <AccountData />}</Suspense>}</section>
}
