import { useEffect, useState } from 'react'
import { listRecords } from '../records/records-api'
import type { RecordItem } from '../records/records-api'
import { Modal } from './Modal'
import { errorText } from './api'
export function ProjectTasks({ project, onClose }: { project: RecordItem; onClose: () => void }) {
  const [items, setItems] = useState<RecordItem[]>(), [error, setError] = useState(''), [retry, setRetry] = useState(0)
  useEffect(() => { const c = new AbortController(); listRecords('tasks', c.signal).then(rows => { if (!c.signal.aborted) { setItems(rows.filter(row => row.project_id === project.id)); setError('') } }).catch(e => { if (!c.signal.aborted) setError(errorText(e)) }); return () => c.abort() }, [project.id, retry])
  const done = items?.filter(item => item.status === 'completed').length ?? 0
  return <Modal title={`${project.name}: tasks & milestones`} onClose={onClose}>{error ? <p role="alert" className="notice-error">{error} <button className="text-button" onClick={() => setRetry(n => n + 1)}>Retry</button></p> : !items ? <p role="status">Loading project tasks…</p> : <><p>{done} of {items.length} linked tasks completed</p>{items.length > 0 && <progress className="project-progress" max={items.length} value={done} aria-label="Linked task completion" />}<p className="state-copy">Manage these records in Tasks. Completing a task does not automatically complete the project.</p>{['milestone', 'task'].map(kind => <section key={kind}><h3>{kind === 'milestone' ? 'Milestones' : 'Tasks'}</h3>{items.filter(item => (item.kind || 'task') === kind).length === 0 ? <p className="state-copy">None linked yet.</p> : <ul className="project-task-list">{items.filter(item => (item.kind || 'task') === kind).map(item => <li key={item.id}><strong>{item.title}</strong><span className="badge">{item.status?.replaceAll('_', ' ')}</span>{item.due_date && <small>Due {item.due_date}</small>}{item.parent_id && <small>Subtask</small>}</li>)}</ul>}</section>)}</>}</Modal>
}
