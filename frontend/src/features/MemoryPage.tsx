import { useEffect, useState } from 'react'
import { api, errorText } from './api'
type Memory = { id: string; content: string; status: 'pending' | 'approved' }

export function MemoryPage() {
  const [items,setItems] = useState<Memory[]>([]), [enabled,setEnabled] = useState(true)
  const [draft,setDraft] = useState(''), [edit,setEdit] = useState<string|null>(null)
  const [busy,setBusy] = useState(false), [ready,setReady] = useState(false), [error,setError] = useState('')
  const [refresh,setRefresh] = useState(0)
  useEffect(() => {
    const c = new AbortController()
    Promise.all([api<Memory[]>('memory','GET',undefined,c.signal),api<{personalization:boolean}>('memory/preferences','GET',undefined,c.signal)])
      .then(([rows,p]) => { setItems(rows); setEnabled(p.personalization); setReady(true) })
      .catch(e => { if(!c.signal.aborted) setError(errorText(e)) })
    return () => c.abort()
  },[refresh])
  async function change(action:()=>Promise<void>) { setBusy(true);setError('');try {await action()}catch(e){setError(errorText(e))}finally{setBusy(false)} }
  return <section className="feature-page">
    <header className="page-heading"><div><p className="eyebrow">You decide what stays</p><h1>Personal memory</h1><p className="page-subtitle">A few useful details. Always reviewed by you.</p></div></header>
    {error && <div className="notice-error" role="alert">{error} <button className="text-button" onClick={()=>{setError('');setRefresh(v=>v+1)}}>Reload memory</button></div>}
    {!ready ? <p role="status">Loading memory…</p> : <>
      <div className="feature-card"><label className="toggle-label"><input type="checkbox" checked={enabled} disabled={busy} onChange={e=>{const value=e.target.checked;void change(async()=>{await api('memory/preferences','PUT',{personalization:value});setEnabled(value)})}}/>Use personalization in conversations</label><p className="state-copy">When disabled, chat uses your messages without adding workspace records or approved memories. Explicit structured planning still uses your records.</p></div>
      <form className="feature-card feature-form" onSubmit={e=>{e.preventDefault();void change(async()=>{
        const saved=await api<Memory>(edit?`memory/${edit}`:'memory',edit?'PUT':'POST',{content:draft})
        setItems(rows=>edit?rows.map(row=>row.id===saved.id?saved:row):[saved,...rows]);setDraft('');setEdit(null)
      })}}><h2>{edit?'Correct a memory':'Propose a memory'}</h2><label>What should Momentum remember?<textarea className="field" required maxLength={500} value={draft} onChange={e=>setDraft(e.target.value)} placeholder="I prefer short explanations with practical examples."/></label><p className="state-copy">Avoid passwords, account numbers and unnecessary sensitive details. New or corrected memories stay pending until you approve them.</p><div className="feature-actions"><button className="button-primary" disabled={busy||!draft.trim()}>{busy?'Saving…':'Save for review'}</button>{edit&&<button type="button" className="button-secondary" onClick={()=>{setEdit(null);setDraft('')}}>Cancel edit</button>}</div></form>
      <div className="feature-grid">{items.map(item=><article className="feature-card" key={item.id}><span className="badge">{item.status==='approved'?'Approved':'Awaiting your approval'}</span><p className="memory-content">{item.content}</p><div className="feature-actions">{item.status==='pending'&&<button className="button-primary" disabled={busy} onClick={()=>void change(async()=>{const saved=await api<Memory>(`memory/${item.id}/approve`,'POST');setItems(rows=>rows.map(r=>r.id===saved.id?saved:r))})}>Approve memory</button>}<button className="text-button" disabled={busy} onClick={()=>{setEdit(item.id);setDraft(item.content)}}>Correct</button><button className="text-button" disabled={busy} onClick={()=>{if(window.confirm('Delete this memory permanently?'))void change(async()=>{await api(`memory/${item.id}`,'DELETE');setItems(rows=>rows.filter(r=>r.id!==item.id))})}}>Delete</button></div></article>)}</div>
      {!items.length&&<div className="empty-state"><h2>Nothing remembered yet</h2><p>Conversation history and workspace records are separate. Chat is never silently saved as approved memory.</p></div>}
    </>}
  </section>
}
