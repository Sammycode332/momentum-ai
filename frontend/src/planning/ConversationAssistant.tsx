import { useEffect, useRef, useState } from 'react'
import type { FormEvent, KeyboardEvent } from 'react'
import { PlanningAssistant } from './PlanningAssistant'
import { AssistantMarkdown } from './AssistantMarkdown'
import { loadMessages, sendTurn } from './conversation-api'
import type { SavedMessage } from './conversation-api'
import './conversation.css'
import { MessageTools } from '../features/MessageTools'
import { ChatTaskProposal } from './ChatTaskProposal'

const prompts = [
  { title: 'Learn', detail: 'Work through a concept', prompt: 'Help me learn something new. Ask what subject I want to study and what I already know.' },
  { title: 'Opportunities', detail: 'Plan your search', prompt: 'Help me find places to look for relevant opportunities and show me how to verify a listing.' },
  { title: 'Interview Prep', detail: 'Practice an interview question', prompt: 'Help me prepare for an interview. First ask about my target role and experience level.' },
  { title: 'Plan My Day', detail: 'Prioritize your saved work', prompt: 'Which of my tasks should I prioritize today, and why?' },
]

export function ConversationAssistant({ chatId, initialMessages = [], onStart }: {
  chatId: string | null
  initialMessages?: SavedMessage[]
  onStart?: (title: string, signal: AbortSignal) => Promise<string>
}) {
  const [view, setView] = useState<'chat' | 'plan'>('chat')
  const [turns, setTurns] = useState(initialMessages)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef<AbortController | null>(null)
  const conversationId = useRef(chatId)
  const unanswered = turns.at(-1)?.role === 'user'
  const transcript = useRef<HTMLDivElement>(null)
  const composer = useRef<HTMLTextAreaElement>(null)
  useEffect(() => () => pending.current?.abort(), [])
  useEffect(() => {
    if (view === 'chat' && transcript.current) transcript.current.scrollTop = transcript.current.scrollHeight
  }, [turns, busy, error, view])

  async function request(turn: SavedMessage) {
    if (pending.current) return
    const controller = new AbortController()
    pending.current = controller
    setError('')
    setBusy(true)
    try {
      let id = conversationId.current
      if (!id && onStart) {
        id = await onStart(Array.from(turn.content).slice(0, 80).join(''), controller.signal)
        conversationId.current = id
      }
      if (!id) throw new Error('Start a conversation first.')
      const reply = await sendTurn(id, turn, controller.signal)
      if (!controller.signal.aborted) setTurns(current => [...current, reply])
    } catch (failure) {
      if (!controller.signal.aborted) {
        setError(failure instanceof Error ? failure.message : 'Try again.')
        // If another tab advanced the conversation, reconcile from the saved history.
        if (conversationId.current) {
          const rows = await loadMessages(conversationId.current, controller.signal).catch(() => null)
          if (rows && !controller.signal.aborted && rows.length &&
            (rows.at(-1)?.role === 'user' || rows.some(row => row.turn_id === turn.turn_id))) {
            setTurns(rows)
            if (rows.at(-1)?.role === 'assistant') setError('')
          }
        }
      }
    } finally {
      pending.current = null
      if (!controller.signal.aborted) setBusy(false)
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const content = draft.trim()
    if (!content || unanswered || pending.current) return
    const turn: SavedMessage = { turn_id: crypto.randomUUID(), role: 'user', content, position: (turns.at(-1)?.position ?? 0) + 1 }
    setTurns([...turns, turn])
    setDraft('')
    void request(turn)
  }

  function composerKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      event.currentTarget.form?.requestSubmit()
    }
  }

  return (
    <section className="conversation" aria-label="AI Assistant">
      <header className="conversation-header">
        <div className="planning-heading">
          <span className="planning-icon" aria-hidden="true">✦</span>
          <div><h1>AI Assistant</h1><p>Work through questions and decide what to do next.</p></div>
        </div>
        <button className="button-secondary" onClick={() => setView(view === 'chat' ? 'plan' : 'chat')}>
          {view === 'chat' ? 'Structured planner' : 'Back to chat'}
        </button>
      </header>
      {view === 'plan' ? <PlanningAssistant embedded /> : (
        <div className="conversation-panel">
          <div className="conversation-scroll" ref={transcript} tabIndex={0} aria-label="Conversation">
            {!turns.length && <div className="conversation-welcome">
              <h2>What are you working on?</h2>
              <p>Start with a question or pick a prompt to edit.</p>
              <div className="conversation-prompts">
                {prompts.map(item => (
                  <button key={item.title} className="button-secondary" onClick={() => {
                    setDraft(item.prompt)
                    composer.current?.focus()
                  }}><strong>{item.title}</strong><span>{item.detail}</span></button>
                ))}
              </div>
            </div>}
            <div role="log" aria-label="Chat messages" aria-relevant="additions">
              {turns.map(turn => (
                <article className={`conversation-turn conversation-${turn.role}`} key={`${turn.turn_id}-${turn.role}`}>
                  <h3 className="conversation-author">{turn.role === 'user' ? 'You' : 'Momentum AI'}</h3>
                  {turn.action ? <ChatTaskProposal action={turn.action} onChange={action =>
                    setTurns(current => current.map(row => row.action?.id === action.id ? { ...row, action } : row))
                  } /> : turn.role === 'assistant' ? <AssistantMarkdown text={turn.content} /> : <p>{turn.content}</p>}
                  {turn.role === 'assistant' && !turn.action && <MessageTools content={turn.content} />}
                </article>
              ))}
            </div>
            {busy && <p role="status" className="conversation-pending">Momentum AI is thinking…</p>}
            {!busy && (error || unanswered) && <div className="notice-error">
              <p role="alert">{error || 'The last message is waiting for a reply.'}</p>
              {unanswered && <button className="button-secondary" onClick={() => void request(turns.at(-1)!)}>Retry reply</button>}
            </div>}
          </div>
          <form className="conversation-composer" onSubmit={submit}>
            <label className="sr-only" htmlFor="conversation-message">Message</label>
            <textarea id="conversation-message" ref={composer} className="field" maxLength={4000}
              value={draft} rows={2} placeholder="Message Momentum AI…" onKeyDown={composerKey}
              onChange={event => setDraft(event.target.value)} />
            <button className="button-primary" type="submit" disabled={busy || unanswered || !draft.trim()}>Send</button>
          </form>
          <details className="conversation-privacy">
            <summary>Privacy and capabilities</summary>
            <p>Momentum saves chat history to your account. Google Gemini receives recent messages and selected workspace details. Saved chats do not become approved personal memory.</p>
            <p>Chat can propose a task. Approve it to save it to your workspace. Control saved memory in Settings.</p>
          </details>
        </div>
      )}
    </section>
  )
}
