import { useLayoutEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { api } from './api'
import type { Task, TaskChanges } from './api'

export type TaskDialogMode =
  | { kind: 'create' }
  | { kind: 'edit' | 'delete'; task: Task }

function localDateTime(date: Date) {
  const pad = (value: number) => String(value).padStart(2, '0')
  const year = String(date.getFullYear()).padStart(4, '0')
  return `${year}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function defaultDueDate() {
  const today = new Date()
  today.setHours(23, 59, 0, 0)
  return localDateTime(today)
}

type Props = {
  mode: TaskDialogMode
  pending: boolean
  close: () => void
  mutate: (operation: () => Promise<unknown>, notice: string, onError: (message: string) => void) => Promise<void>
}

export function TaskDialog({ mode, pending, close, mutate }: Props) {
  const task = mode.kind === 'create' ? undefined : mode.task
  const deleting = mode.kind === 'delete'
  const originalDue = task ? localDateTime(new Date(task.due_ts)) : ''
  const [name, setName] = useState(task?.name ?? '')
  const [description, setDescription] = useState(task?.description ?? '')
  const [due, setDue] = useState(() => task ? originalDue : defaultDueDate())
  const [errors, setErrors] = useState<{ name?: string; due?: string }>({})
  const [saveError, setSaveError] = useState('')
  const dialog = useRef<HTMLDialogElement>(null)
  const nameInput = useRef<HTMLInputElement>(null)
  const dueInput = useRef<HTMLInputElement>(null)
  const cancelButton = useRef<HTMLButtonElement>(null)

  useLayoutEffect(() => {
    const element = dialog.current
    if (!element) return
    const opener = document.activeElement
    const heading = element.closest('main')?.querySelector('h1')
    element.showModal()
    if (nameInput.current) nameInput.current.focus()
    else cancelButton.current?.focus()
    return () => {
      element.close()
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus()
      else heading?.focus()
    }
  }, [])

  function submit(event: FormEvent) {
    event.preventDefault()
    if (pending) return
    setSaveError('')
    if (mode.kind === 'delete') {
      void mutate(() => api.deleteTask(mode.task.task_id), 'Task deleted.', setSaveError)
      return
    }
    const cleanName = name.trim()
    const date = new Date(due)
    const invalid: typeof errors = {}
    if (Array.from(cleanName).length < 3) invalid.name = 'Enter at least 3 characters.'
    if (!due || !Number.isFinite(date.getTime()) || localDateTime(date) !== due) {
      invalid.due = 'Enter a valid due date and time.'
    }
    setErrors(invalid)
    if (invalid.name || invalid.due) {
      if (invalid.name) nameInput.current?.focus()
      else dueInput.current?.focus()
      return
    }
    if (mode.kind === 'create') {
      const fields = { name: cleanName, description: description || null, due_ts: date.toISOString() }
      void mutate(() => api.createTask(fields), 'Task created.', setSaveError)
      return
    }
    const changes: TaskChanges = {}
    if (name !== mode.task.name && cleanName !== mode.task.name) changes.name = cleanName
    if (description !== (mode.task.description ?? '')) changes.description = description
    if (due !== originalDue) changes.due_ts = date.toISOString()
    if (!Object.keys(changes).length) {
      close()
      return
    }
    void mutate(() => api.updateTask(mode.task.task_id, changes), 'Task updated.', setSaveError)
  }

  return <dialog ref={dialog} className="task-dialog" aria-labelledby="task-dialog-title"
    aria-describedby={deleting ? 'delete-task-details' : undefined}
    onCancel={event => {
      event.preventDefault()
      if (!pending) close()
    }}>
    <h2 id="task-dialog-title">{deleting ? 'Delete task?' : task ? 'Edit task' : 'New task'}</h2>
    <form onSubmit={submit} noValidate>
      {deleting ? <p id="delete-task-details">“{task?.name}” will be permanently deleted.</p> : <>
        <div className="field">
          <label htmlFor="task-name">Name</label>
          <input id="task-name" ref={nameInput} required value={name} readOnly={pending}
            onChange={event => setName(event.target.value)}
            aria-invalid={!!errors.name} aria-describedby={errors.name ? 'task-name-error' : undefined} />
          {errors.name && <p className="field-error" id="task-name-error" role="alert">{errors.name}</p>}
        </div>
        <div className="field">
          <label htmlFor="task-description">Description <span className="optional">(optional)</span></label>
          <textarea id="task-description" rows={3} value={description} readOnly={pending}
            onChange={event => setDescription(event.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="task-due">Due date and time</label>
          <input id="task-due" ref={dueInput} type="datetime-local" required value={due} readOnly={pending}
            onChange={event => setDue(event.target.value)}
            aria-invalid={!!errors.due} aria-describedby={errors.due ? 'task-due-error' : undefined} />
          {errors.due && <p className="field-error" id="task-due-error" role="alert">{errors.due}</p>}
        </div>
      </>}
      {saveError && <p className="notice" role="alert">{saveError}</p>}
      <div className="dialog-actions">
        <button ref={cancelButton} type="button" disabled={pending} onClick={close}>Cancel</button>
        <button className={deleting ? 'danger' : 'primary'} disabled={pending} type="submit">
          {deleting ? pending ? 'Deleting…' : 'Delete task' : pending ? 'Saving…' : 'Save task'}
        </button>
      </div>
    </form>
  </dialog>
}
