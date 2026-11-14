import { useEffect, useState } from 'react'
import { ApiRequestError } from '../auth/authenticated-fetch'
import { ConversationAssistant } from './ConversationAssistant'
import { createConversation, deleteConversation, listConversations, loadMessages, renameConversation } from './conversation-api'
import type { Conversation, SavedMessage } from './conversation-api'

const uuid = /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i

function initialChat() {
  const id = new URLSearchParams(location.search).get('chat')
  return id && uuid.test(id) ? id : null
}

function updateChatUrl(id: string | null) {
  const url = new URL(location.href)
  url.searchParams.set('chat', id ?? '')
  history.replaceState(history.state, '', url)
}

export function ConversationWorkspace() {
  const [active, setActive] = useState(initialChat)
  const [createdHere, setCreatedHere] = useState<string | null>(null)
  const selected = active ?? createdHere
  const [items, setItems] = useState<Conversation[] | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [blankVersion, setBlankVersion] = useState(0)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    listConversations(controller.signal).then(rows => {
      if (!controller.signal.aborted) setItems(rows)
    }, failure => {
      if (!controller.signal.aborted) setError(failure.message)
    })
    return () => controller.abort()
  }, [attempt])

  function select(id: string | null) {
    updateChatUrl(id)
    setActive(id)
    setCreatedHere(null)
  }

  async function change(action: () => Promise<void>) {
    setBusy(true)
    setError('')
    try { await action() } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Could not update conversations.')
    } finally { setBusy(false) }
  }

  function rename(item: Conversation) {
    const title = window.prompt('Conversation name', item.title)?.trim()
    if (!title || title === item.title) return
    if (Array.from(title).length > 120) { setError('Use a conversation name up to 120 characters.'); return }
    void change(async () => {
      const updated = await renameConversation(item.id, title)
      setItems(rows => rows?.map(row => row.id === item.id ? updated : row) ?? null)
    })
  }

  function remove(item: Conversation) {
    if (!window.confirm(`Delete “${item.title}” and its messages?`)) return
    void change(async () => {
      await deleteConversation(item.id)
      setItems(rows => rows?.filter(row => row.id !== item.id) ?? null)
      if (selected === item.id) {
        if (createdHere === item.id) setBlankVersion(value => value + 1)
        select(null)
      }
    })
  }

  return <div className="conversation-workspace">
    <aside className="conversation-sidebar" aria-label="Recent conversations">
      <button className="button-primary" disabled={busy || items === null} onClick={() => void change(async () => {
        const item = await createConversation('New chat', new AbortController().signal)
        setItems(rows => [item, ...(rows ?? [])].slice(0, 50))
        select(item.id)
      })}>+ New chat</button>
      <h2>Recent chats</h2>
      {error && <div className="notice-error" role="alert">{error} <button className="text-button" onClick={() => {
        setError('')
        setAttempt(value => value + 1)
      }}>Reload chats</button></div>}
      {!items && !error && <p role="status">Loading chats…</p>}
      {items?.length === 0 && <p>No conversations yet.</p>}
      <ul>{items?.map(item => <li key={item.id}>
        <button className="conversation-select" disabled={busy} aria-current={selected === item.id ? 'true' : undefined}
          onClick={() => select(item.id)}>{item.title}</button>
        <div className="conversation-row-actions">
          <button className="text-button" disabled={busy} aria-label={`Rename ${item.title}`} onClick={() => rename(item)}>Rename</button>
          <button className="text-button" disabled={busy} aria-label={`Delete ${item.title}`} onClick={() => remove(item)}>Delete</button>
        </div>
      </li>)}</ul>
    </aside>
    {active ? <OpenConversation key={active} id={active} /> : items === null ? null : <ConversationAssistant key={`blank-${blankVersion}`} chatId={null}
      onStart={async (title, signal) => {
        const item = await createConversation(title, signal)
        signal.throwIfAborted()
        // Keep this editor mounted until the first request finishes.
        updateChatUrl(item.id)
        setCreatedHere(item.id)
        setItems(rows => [item, ...(rows ?? [])].slice(0, 50))
        return item.id
      }} />}
  </div>
}

function OpenConversation({ id }: { id: string }) {
  const [messages, setMessages] = useState<SavedMessage[] | null>(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    loadMessages(id, controller.signal).then(rows => {
      if (!controller.signal.aborted) setMessages(rows)
    }, failure => {
      if (controller.signal.aborted) return
      setError(failure instanceof ApiRequestError && failure.status === 404
        ? 'This conversation is unavailable. Select another chat.' : failure.message)
    })
    return () => controller.abort()
  }, [id, attempt])

  if (messages) return <ConversationAssistant chatId={id} initialMessages={messages} />
  if (error) return <div className="error-state" role="alert">{error} <button className="button-secondary" onClick={() => {
    setError('')
    setAttempt(value => value + 1)
  }}>Retry conversation</button></div>
  return <p role="status">Loading conversation…</p>
}
