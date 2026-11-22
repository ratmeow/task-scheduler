import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError, message, SessionChangedError } from './api'
import type { Task } from './api'
import { TaskDialog } from './TaskDialog'
import type { TaskDialogMode } from './TaskDialog'

const pageSizes = [20, 40, 60] as const
const filters = ['All', 'Open', 'Completed'] as const
const viewLabels = { All: 'All tasks', Open: 'Open', Completed: 'Completed' }
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
  const searchInput = useRef<HTMLInputElement>(null)
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
    if (dialog || loggingOut) return
    function focusSearch(event: KeyboardEvent) {
      if (event.key.toLowerCase() !== 'k' || !(event.ctrlKey || event.metaKey) || event.altKey || event.shiftKey) return
      event.preventDefault()
      searchInput.current?.focus()
      searchInput.current?.select()
    }
    window.addEventListener('keydown', focusSearch)
    return () => window.removeEventListener('keydown', focusSearch)
  }, [dialog, loggingOut])

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

  return <div className="workspace-shell">
    <aside className="workspace-sidebar">
      <div className="brand"><span className="brand-mark" aria-hidden="true" />Task Scheduler</div>
      <nav className="task-views" aria-label="Task views">
        <p className="sidebar-label" aria-hidden="true">Views</p>
        {filters.map(filter => <button key={filter} aria-pressed={query.filter === filter} disabled={loggingOut}
          onClick={() => { if (query.filter !== filter) changeQuery({ filter }) }}>
          <span className={`icon view-icon view-${filter.toLowerCase()}`} aria-hidden="true" />
          {viewLabels[filter]}
        </button>)}
      </nav>
      <div className="sidebar-footer">
        <button className="quiet logout" disabled={loggingOut} onClick={() => void logout()}>
          <span className="icon icon-logout" aria-hidden="true" />
          <span>{loggingOut ? 'Logging out…' : 'Log out'}</span>
        </button>
      </div>
    </aside>
    <main className="workspace" id="content">
      <header className="workspace-heading">
        <h1 tabIndex={-1}>{viewLabels[query.filter]}</h1>
        <button className="primary" disabled={!result || loggingOut || pending} onClick={() => setDialog({ kind: 'create' })}>
          <span className="icon icon-plus" aria-hidden="true" />New task
        </button>
      </header>
      {!loggingOut && <div className="task-toolbar">
        <div className="task-search">
          <span className="icon icon-search" aria-hidden="true" />
          <input ref={searchInput} type="search" aria-label="Search tasks by name" placeholder="Search tasks"
            aria-keyshortcuts="Control+K Meta+K"
            value={query.search} onChange={event => changeQuery({ search: event.target.value })} />
          {!query.search && <kbd aria-hidden="true">Ctrl K</kbd>}
        </div>
        <label className="select-control">
          <span>Sort by</span>
          <select value={query.sort} onChange={event => changeQuery({ sort: event.target.value as Query['sort'] })}>
            {Object.entries(sorts).map(([value, { label }]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
      </div>}
      {!loggingOut && <div className="task-feedback">
        <div role="status">{success && <p className="notice success">{success}</p>}</div>
        {actionError && <p className="notice" role="alert">{actionError}</p>}
      </div>}
      <section className="task-panel" aria-label="Task list">
        {loggingOut ? <p className="list-state muted" role="status">Closing your session…</p> : <>
          <div className="task-columns task-grid" aria-hidden="true">
            <span>Task</span><span>Due date</span><span>Status</span>
          </div>
          {!current && <p className="list-state muted" role="status">Loading tasks…</p>}
          {listError && <div className="list-state">
            <h2>Couldn’t load tasks</h2>
            <p className="muted" role="alert">{listError}</p>
            <button onClick={() => setQuery(value => ({ ...value }))}>Try again</button>
          </div>}
          {taskCount === 0 && <div className="list-state" role="status">
            <span className="icon view-icon view-all" aria-hidden="true" />
            <h2>{query.search.trim() ? 'No matching tasks' : query.filter === 'All' ? 'No tasks yet' : `No ${query.filter.toLowerCase()} tasks`}</h2>
            {query.search.trim() && <p className="muted">Try a different name.</p>}
            {!query.search.trim() && query.filter === 'All' && <p className="muted">Create a task to start planning.</p>}
          </div>}
          {!!visibleTasks?.length && <ul className="task-list">
            {visibleTasks.map(task => {
              const due = new Date(task.due_ts)
              const checked = pendingCompletion?.task_id === task.task_id ? pendingCompletion.is_complete : task.is_complete
              const overdue = !checked && due.getTime() < now
              return <li key={task.task_id} className="task-row task-grid">
                <div className="task-details">
                  <label className="task-checkbox" title={checked ? 'Reopen task' : 'Complete task'}>
                    <input type="checkbox" aria-label={`Mark ${task.name} ${checked ? 'open' : 'complete'}`}
                      checked={checked} aria-disabled={pending}
                      onChange={() => void toggleCompletion(task)} />
                  </label>
                  <div className="task-summary">
                    <button className="task-name" aria-label={`Edit ${task.name}`} title={task.name} disabled={pending}
                      onClick={() => setDialog({ kind: 'edit', task })}>{task.name}</button>
                    {task.description && <p className="task-description" title={task.description}>{task.description}</p>}
                  </div>
                </div>
                <p className={overdue ? 'task-due overdue' : 'task-due'}>
                  <span className="mobile-due">{overdue ? 'Overdue' : 'Due'}</span>
                  <time dateTime={task.due_ts}>{dueDate.format(due)}</time>
                  {overdue && <span className="overdue-label">Overdue</span>}
                </p>
                <p className={checked ? 'task-status complete' : 'task-status'}>
                  <span className="status-dot" aria-hidden="true" />{checked ? 'Completed' : 'Open'}
                </p>
                <button className="quiet task-delete" aria-label={`Delete ${task.name}`} title="Delete task" disabled={pending}
                  onClick={() => setDialog({ kind: 'delete', task })}>
                  <span className="icon icon-trash" aria-hidden="true" />
                </button>
              </li>
            })}
          </ul>}
        </>}
      </section>
      {!loggingOut && <footer className="task-pagination">
        <div className="page-summary">
          <p className="muted" role="status">
            {taskCount !== undefined && `${taskCount} ${taskCount === 1 ? 'task' : 'tasks'} on this page`}
          </p>
          <label className="select-control page-size">
            <span>Per page</span>
            <select value={query.pageSize} onChange={event => {
              const pageSize = pageSizes.find(size => String(size) === event.target.value)
              if (pageSize !== undefined) changeQuery({ pageSize })
            }}>
              {pageSizes.map(size => <option key={size} value={size}>{size}</option>)}
            </select>
          </label>
        </div>
        <nav className="task-page-controls" aria-label="Task pages">
          <button aria-label="Previous page" title="Previous page" disabled={query.page === 1 || !current || pending}
            onClick={() => changeQuery({ page: query.page - 1 })}><span className="chevron previous" aria-hidden="true" /></button>
          <span aria-live="polite">Page {query.page}</span>
          <button aria-label="Next page" title="Next page" disabled={!hasNextPage || pending}
            onClick={() => changeQuery({ page: query.page + 1 })}><span className="chevron" aria-hidden="true" /></button>
        </nav>
      </footer>}
      {dialog && <TaskDialog mode={dialog} pending={pending} close={() => setDialog(undefined)} mutate={mutate} />}
    </main>
  </div>
}
