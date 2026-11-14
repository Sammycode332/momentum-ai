import { useRef, useState } from 'react'
import { api } from '../features/api'
import type { ChatAction, TaskEdit } from './conversation-api'
import { GoalProposalDetails } from './GoalProposalDetails'

const fields = { title: 'Title', status: 'Status', priority: 'Priority', due_date: 'Due date' }
const count = (ids: string[], noun: string) => `${ids.length} ${noun}${ids.length === 1 ? '' : 's'}`

export function TaskEditDetails({ edit }: { edit: TaskEdit }) {
  const format = (value: string | null) => edit.field === 'status' ? value?.replaceAll('_', ' ') : value
  return <dl aria-label={fields[edit.field]}>
    <dt>Current {fields[edit.field].toLowerCase()}</dt><dd>{format(edit.previous) ?? 'None'}</dd>
    <dt>Proposed {fields[edit.field].toLowerCase()}</dt><dd>{format(edit.value)}</dd>
  </dl>
}

export function ChatTaskProposal({ action, onChange }: {
  action: ChatAction
  onChange: (action: ChatAction) => void
}) {
  const busy = useRef(false)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const { proposal, status, result_id: recordId } = action
  const editing = proposal.kind === 'update_task'
  const goal = proposal.roadmap?.goal ?? proposal.goal
  const receipt = proposal.receipt
  const [selected, setSelected] = useState(() => proposal.roadmap?.stages.map((_, index) => index) ?? [])

  async function decide(decision: 'approve' | 'reject') {
    if (busy.current) return
    busy.current = true
    setWorking(true)
    setError('')
    try {
      const path = `actions/${action.id}/${decision}`
      const result = decision === 'approve' && proposal.roadmap
        ? await api<ChatAction>(path, 'POST', { stages: selected })
        : await api<ChatAction>(path, 'POST')
      if (result.id !== action.id || (decision === 'approve'
        ? result.status !== 'applied' || !result.result_id
        : result.status !== 'rejected')) {
        throw new Error('The server did not confirm the action.')
      }
      onChange(result)
    } catch (failure) {
      const message = failure instanceof Error ? failure.message : 'Try again.'
      setError(`Could not confirm the action. ${message}`)
    } finally {
      busy.current = false
      setWorking(false)
    }
  }

  return <section className="feature-card chat-task-proposal" aria-label={proposal.roadmap ? 'Roadmap proposal' : goal ? 'Goal proposal' : 'Task proposal'}>
    <h4>{proposal.title}</h4>
    {goal ? <GoalProposalDetails goal={goal} roadmap={proposal.roadmap} selected={selected} disabled={working}
      toggle={status === 'pending' ? index => setSelected(current => current.includes(index)
        ? current.filter(value => value !== index) : [...current, index]) : undefined} /> :
      editing && proposal.edit ? <TaskEditDetails edit={proposal.edit} /> :
      <p>{proposal.priority} priority · {proposal.due_date ? `Due ${proposal.due_date}` : 'No due date'}</p>}
    {status === 'pending' && <>
      <p>Pending approval.{!editing && !goal && ' Tasks save a date only. Any requested time will be omitted.'}</p>
      <div className="feature-actions">
        <button className="button-primary" disabled={working || (editing && !proposal.edit)}
          onClick={() => void decide('approve')}>{goal ? (proposal.roadmap && selected.length
            ? 'Save goal and selected phases' : 'Approve and create goal')
            : editing ? 'Approve task update' : 'Approve and create task'}</button>
        <button className="button-secondary" disabled={working} onClick={() => void decide('reject')}>Reject proposal</button>
      </div>
    </>}
    {status === 'applied' && recordId && (goal ? <div role="status">
      <p>Goal saved. Find it in Goals.</p>
      {receipt?.project_ids.length ? <p>Saved {count(receipt.project_ids, 'project')}, {count(receipt.milestone_ids, 'milestone')} and {count(receipt.task_ids, 'task')}. Find them in Projects and Tasks.</p> : null}
      {receipt && <details><summary>Saved record IDs</summary><ul>
        <li>Goal {receipt.goal_id}</li>
        {receipt.project_ids.map(id => <li key={id}>Project {id}</li>)}
        {receipt.milestone_ids.map(id => <li key={id}>Milestone {id}</li>)}
        {receipt.task_ids.map(id => <li key={id}>Task {id}</li>)}
      </ul></details>}
    </div> : <p role="status">{editing ? 'Task updated.' : 'Task created.'} Find it in Tasks.</p>)}
    {status === 'rejected' && <p role="status">Proposal rejected.</p>}
    {error && <p role="alert">{error}</p>}
  </section>
}
