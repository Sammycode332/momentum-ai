import { lazy, Suspense, useState } from 'react'
const Chat = lazy(() => import('../planning/ConversationWorkspace').then(m => ({ default: m.ConversationWorkspace })))
const Practice = lazy(() => import('./PracticePage').then(m => ({ default: m.PracticePage })))
const Actions = lazy(() => import('./ActionsPage').then(m => ({ default: m.ActionsPage })))
type Mode = 'chat' | 'learn' | 'interview' | 'approvals'
const modes: { id: Mode; label: string; description: string }[] = [
  { id: 'chat', label: 'Chat', description: 'Ask anything. Think it through, explore an idea, or make a plan.' },
  { id: 'learn', label: 'Learn', description: 'Go deeper with a guided path, practice questions and saved progress.' },
  { id: 'interview', label: 'Interview', description: 'Rehearse for your role and get feedback on each answer.' },
  { id: 'approvals', label: 'Approvals', description: 'Review proposed changes. Nothing is applied until you approve it.' },
]
export function AssistantHub() {
  const [mode, setMode] = useState<Mode>('chat')
  const [visited, setVisited] = useState<Mode[]>(['chat'])
  return <section className="assistant-hub"><header className="hub-heading"><div><p className="eyebrow">Your thinking partner</p><h1>AI Assistant</h1><p>One assistant. A little structure when you need it.</p></div><span className="hub-label"><span aria-hidden="true">✦</span> Powered by Gemini</span></header>
    <nav className="mode-switch" aria-label="Assistant mode">{modes.map(item => <button key={item.id} aria-pressed={mode === item.id} onClick={() => { setMode(item.id); setVisited(previous => previous.includes(item.id) ? previous : [...previous, item.id]) }}>{item.label}</button>)}</nav>
    <p className="mode-description">{modes.find(item => item.id === mode)?.description}</p>
    {/* Keep visited modes mounted so switching does not discard a draft or interrupt a reply. */}
    {visited.map(item => <div key={item} hidden={mode !== item} className="assistant-mode"><Suspense fallback={<div className="feature-card skeleton" role="status" aria-label="Loading assistant mode"><span /><span /></div>}>{item === 'chat' ? <Chat /> : item === 'approvals' ? <Actions /> : <Practice kind={item === 'learn' ? 'tutor' : 'interview'} embedded />}</Suspense></div>)}
  </section>
}
