import { lazy, Suspense, useState } from 'react'
import { RecordsPage } from '../records/RecordsPage'
const Discovery = lazy(() => import('./DiscoveryPage').then(m => ({ default: m.DiscoveryPage })))
export function OpportunitiesHub({ openCreate }: { openCreate: boolean }) {
  const [view, setView] = useState<'saved' | 'discover'>('saved')
  return <section><nav className="mode-switch compact-switch" aria-label="Opportunity view"><button aria-pressed={view === 'saved'} onClick={() => setView('saved')}>Saved opportunities</button><button aria-pressed={view === 'discover'} onClick={() => setView('discover')}>Discover opportunities</button></nav>{view === 'saved' ? <RecordsPage domain="opportunities" openCreate={openCreate} /> : <Suspense fallback={<p role="status">Loading discovery…</p>}><Discovery /></Suspense>}</section>
}
