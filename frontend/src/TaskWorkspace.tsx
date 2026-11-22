import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError, message, SessionChangedError } from './api'
import type { Task } from './api'
import { TaskDialog } from './TaskDialog'
import type { TaskDialogMode } from './TaskDialog'

const pageSizes = [20, 40, 60] as const
const filters = ['All', 'Open', 'Completed'] as const
const sorts = {
  updated_ts: { label: 'Recently updated', descending: true },
  due_ts: { label: 'Due soonest', descending: false },
  created_ts: { label: 'Newest', descending: true },
  name: { label: 'Name', descending: false },
}
const dueDate = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

type Query = {
  search: string
  filter: typeof filters[number]
  sort: keyof typeof sorts
  page: number
  pageSize: typeof pageSizes[number]
}

type TaskPage =
  | { query: Query; tasks: Task[] }
  | { query: Query; error: string }

function taskParams({ page, pageSize, search, filter, sort }: Query) {
  const params = new URLSearchParams({
    limit: String(pageSize + 1),
    offset: String((page - 1) * pageSize),
    sort_by: sort,
    sort_desc: String(sorts[sort].descending),
  })
  if (search.trim()) params.set('name', search.trim())
  if (filter !== 'All') params.set('is_complete', String(filter === 'Completed'))
  return params
}

export function TaskWorkspace() {
  const navigate = useNavigate()
  const [query, setQuery] = useState<Query>({
    search: '', filter: 'All', sort: 'updated_ts', page: 1, pageSize: pageSizes[0],
  })
  const [result, setResult] = useState<TaskPage>()
  const [dialog, setDialog] = useState<TaskDialogMode>()
  const [pending, setPending] = useState(false)
  const [pendingCompletion, setPendingCompletion] = useState<Pick<Task, 'task_id' | 'is_complete'>>()
  const [loggingOut, setLoggingOut] = useState(false)
  const [listRevision, setListRevision] = useState(0)
  const [success, setSuccess] = useState('')
  const [actionError, setActionError] = useState('')
  const [now, setNow] = useState(Date.now)
  const active = useRef(false)
  const current = result?.query === query ? result : undefined
  const tasks = current && 'tasks' in current ? current.tasks : undefined
  const visibleTasks = tasks?.slice(0, query.pageSize)
  const taskCount = visibleTasks?.length
  const hasNextPage = (tasks?.length ?? 0) > query.pageSize
  const listError = current && 'error' in current ? current.error : ''

  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    if (!success) return
    const timer = window.setTimeout(() => setSuccess(''), 5000)
    return () => window.clearTimeout(timer)
  }, [success])

  useEffect(() => {
    if (loggingOut) return
    let currentRequest = true
    void api.tasks(taskParams(query)).then(tasks => {
      if (!currentRequest || !active.current) return
      if (!tasks.length && query.page > 1) {
        setQuery(value => value === query ? { ...query, page: query.page - 1 } : value)
        return
      }
      setResult({ query, tasks })
    }).catch((error: unknown) => {
      if (!currentRequest || !active.current || error instanceof SessionChangedError) return
      if (error instanceof ApiError && error.status === 401) {
        navigate('/login', { replace: true, state: { error: 'Please log in to continue.' } })
      } else {
        setResult({ query, error: message(error) })
      }
    })
    return () => { currentRequest = false }
  }, [query, listRevision, loggingOut, navigate])

  function changeQuery(changes: Partial<Query>) {
    setSuccess('')
    setActionError('')
    setQuery(value => ({ ...value, page: 1, ...changes }))
  }

  async function mutate(
    operation: () => Promise<unknown>,
    notice: string,
    onError: (message: string) => void = setActionError,
    onSuccess?: () => void,
  ) {
    if (pending || loggingOut) return
    setPending(true)
    setActionError('')
    setSuccess('')
    try {
      await operation()
      if (!active.current) return
      onSuccess?.()
      setDialog(undefined)
      setSuccess(notice)
      setListRevision(value => value + 1)
    } catch (error) {
      if (!active.current || error instanceof SessionChangedError) return
      if (error instanceof ApiError && error.status === 401) {
        navigate('/login', { replace: true, state: { error: 'Please log in to continue.' } })
      } else {
        onError(message(error))
      }
    } finally {
      if (active.current) setPending(false)
    }
  }

  async function toggleCompletion(task: Task) {
    if (pending || loggingOut) return
    const completion = { task_id: task.task_id, is_complete: !task.is_complete }
    setPendingCompletion(completion)
    try {
      await mutate(
        () => api.updateTask(task.task_id, { is_complete: completion.is_complete }),
        completion.is_complete ? 'Task completed.' : 'Task reopened.',
        setActionError,
        () => setResult(page => {
          if (!page || !('tasks' in page)) return page
          return {
            ...page,
            tasks: page.tasks.map(item => item.task_id === completion.task_id ? { ...item, ...completion } : item),
          }
        }),
      )
    } finally {
      if (active.current) setPendingCompletion(undefined)
    }
  }

  async function logout() {
    active.current = false
    setLoggingOut(true)
    setDialog(undefined)
    let error: string | undefined
    try { await api.logout() } catch (cause) {
      error = `Sign-out could not be confirmed. ${message(cause)} Retry sign-out to clear your server session.`
    }
    navigate('/login', { replace: true, state: error ? { error, logoutFailed: true } : { success: 'You have been logged out.' } })
  }

  return <main className="workspace" id="content">
    {!loggingOut && <div className="task-feedback">
      <div role="status">{success && <p className="notice success">{success}</p>}</div>
      {actionError && <p className="notice" role="alert">{actionError}</p>}
    </div>}
    <div className="workspace-heading">
      <h1 tabIndex={-1}>Tasks</h1>
      <div className="workspace-actions">
        <button className="quiet" disabled={loggingOut} onClick={() => void logout()}>
          {loggingOut ? 'Logging out…' : 'Log out'}
        </button>
        <button className="primary" disabled={!result || loggingOut || pending} onClick={() => setDialog({ kind: 'create' })}>
          <span aria-hidden="true">+</span> New task
        </button>
      </div>
    </div>
    {!loggingOut && <div className="task-toolbar">
      <input type="search" aria-label="Search tasks by name" placeholder="Search tasks"
        value={query.search} onChange={event => changeQuery({ search: event.target.value })} />
      <div className="task-filters" role="group" aria-label="Task status">
        {filters.map(filter => <button key={filter} aria-pressed={query.filter === filter}
          onClick={() => { if (query.filter !== filter) changeQuery({ filter }) }}>{filter}</button>)}
      </div>
      <label className="task-sort">
        <span>Sort by</span>
        <select value={query.sort} onChange={event => changeQuery({ sort: event.target.value as Query['sort'] })}>
          {Object.entries(sorts).map(([value, { label }]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </label>
    </div>}
    <section className="task-panel" aria-label="Task list">
      {loggingOut ? <p className="list-state muted" role="status">Closing your session…</p> : <>
        {!current && <p className="list-state muted" role="status">Loading tasks…</p>}
        {listError && <div className="list-state">
          <p role="alert">{listError}</p>
          <button onClick={() => setQuery(value => ({ ...value }))}>Try again</button>
        </div>}
        {taskCount === 0 && <div className="list-state" role="status">
          <h2>{query.search.trim() ? 'No matching tasks' : query.filter === 'All' ? 'No tasks yet' : `No ${query.filter.toLowerCase()} tasks`}</h2>
          {query.search.trim() && <p className="muted">Try a different name.</p>}
          {!query.search.trim() && query.filter === 'All' && <p className="muted">Select New task to get started.</p>}
        </div>}
        {!!visibleTasks?.length && <ul className="task-list">
          {visibleTasks.map(task => {
            const due = new Date(task.due_ts)
            const checked = pendingCompletion?.task_id === task.task_id ? pendingCompletion.is_complete : task.is_complete
            const overdue = !checked && due.getTime() < now
            return <li key={task.task_id} className={overdue ? 'task-row task-overdue' : 'task-row'}>
              <label className="task-checkbox" title={checked ? 'Reopen task' : 'Complete task'}>
                <input type="checkbox" aria-label={`Mark ${task.name} ${checked ? 'open' : 'complete'}`}
                  checked={checked} aria-disabled={pending}
                  onChange={() => void toggleCompletion(task)} />
              </label>
              <div className="task-details">
                <h2>{task.name}</h2>
                {task.description && <p className="task-description">{task.description}</p>}
                <p className="task-due">
                  {overdue ? 'Overdue' : 'Due'} <time dateTime={task.due_ts}>{dueDate.format(due)}</time>
                </p>
              </div>
              <div className="task-actions">
                <button className="quiet" aria-label={`Edit ${task.name}`} disabled={pending}
                  onClick={() => setDialog({ kind: 'edit', task })}>Edit</button>
                <button className="quiet" aria-label={`Delete ${task.name}`} disabled={pending}
                  onClick={() => setDialog({ kind: 'delete', task })}>Delete</button>
              </div>
            </li>
          })}
        </ul>}
        <div className="task-pagination">
          <label className="task-page-size">
            <span>Tasks per page</span>
            <select value={query.pageSize} onChange={event => {
              const pageSize = pageSizes.find(size => String(size) === event.target.value)
              if (pageSize !== undefined) changeQuery({ pageSize })
            }}>
              {pageSizes.map(size => <option key={size} value={size}>{size}</option>)}
            </select>
          </label>
          <p className="muted task-page-count" role="status">
            {taskCount !== undefined && `${taskCount} ${taskCount === 1 ? 'task' : 'tasks'} on this page`}
          </p>
          <nav className="task-page-controls" aria-label="Task pages">
            <button disabled={query.page === 1 || !current || pending}
              onClick={() => changeQuery({ page: query.page - 1 })}>Previous</button>
            <span aria-live="polite">Page {query.page}</span>
            <button disabled={!hasNextPage || pending}
              onClick={() => changeQuery({ page: query.page + 1 })}>Next</button>
          </nav>
        </div>
      </>}
    </section>
    {dialog && <TaskDialog mode={dialog} pending={pending} close={() => setDialog(undefined)} mutate={mutate} />}
  </main>
}
