import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

export function Modal({ title, onClose, children, busy = false }: { title: string; onClose: () => void; children: ReactNode; busy?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const previous = document.activeElement
    ref.current?.showModal()
    return () => { if (previous instanceof HTMLElement && previous.isConnected) previous.focus() }
  }, [])
  return <dialog className="dialog native-dialog" ref={ref} aria-label={title} onCancel={e => { e.preventDefault(); if (!busy) onClose() }}><div className="dialog-title"><h2>{title}</h2><button type="button" disabled={busy} aria-label="Close dialog" onClick={onClose}>×</button></div>{children}</dialog>
}
