export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message) }
}

export class SessionChangedError extends Error {}

export type Task = {
  task_id: string
  name: string
  description: string | null
  is_complete: boolean
  due_ts: string
}

type TaskFields = Pick<Task, 'name' | 'description' | 'due_ts'>
export type TaskChanges = Partial<TaskFields & Pick<Task, 'is_complete'>>

function json(method: string, body: TaskChanges): RequestInit {
  return { method, body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } }
}

async function request(path: string, options: RequestInit = {}): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...options, credentials: 'same-origin' })
  } catch {
    throw new ApiError('Unable to reach the server. Check your connection and try again.')
  }
  const text = await response.text()
  let body: unknown = text
  try { body = text ? JSON.parse(text) : undefined } catch { /* Proxy errors can be plain text. */ }
  if (!response.ok) {
    let message = `The request failed (${response.status}). Please try again.`
    if (body && typeof body === 'object') {
      if ('message' in body && typeof body.message === 'string') message = body.message
      else if ('detail' in body && Array.isArray(body.detail)) {
        message = body.detail.map((issue: { loc?: unknown[]; msg?: string }) =>
          `${issue.loc?.slice(1).join('.') || 'Form'}: ${issue.msg || 'Invalid value'}`).join('; ')
      } else if ('detail' in body && typeof body.detail === 'string') message = body.detail
    }
    throw new ApiError(message, response.status)
  }
  return body
}

// Each session has its own generation. Logout invalidates every older response.
export class SessionClient {
  private generation = 0
  private refreshRevision = 0
  private refreshFlight?: { generation: number; promise: Promise<unknown> }
  private logoutFlight?: Promise<unknown>

  invalidate() { this.generation += 1 }

  private current(generation: number) {
    if (generation !== this.generation) throw new SessionChangedError()
  }

  private async authenticated(path: string, options?: RequestInit): Promise<unknown> {
    const generation = this.generation
    const revision = this.refreshRevision
    try {
      if (this.logoutFlight) throw new SessionChangedError()
      const result = await request(path, options).catch(async (error: unknown) => {
        this.current(generation)
        if (!(error instanceof ApiError) || error.status !== 401) throw error
        if (revision === this.refreshRevision) await this.refresh(generation)
        this.current(generation)
        return request(path, options)
      })
      this.current(generation)
      return result
    } catch (error) {
      this.current(generation)
      throw error
    }
  }

  private refresh(generation: number) {
    if (this.refreshFlight?.generation === generation) return this.refreshFlight.promise
    const flight = {
      generation,
      promise: request('/auth/refresh', { method: 'POST' }).then(() => {
        this.current(generation)
        this.refreshRevision += 1
      }),
    }
    this.refreshFlight = flight
    void flight.promise.finally(() => {
      if (this.refreshFlight === flight) this.refreshFlight = undefined
    }).catch(() => {})
    return flight.promise
  }

  async tasks(query: URLSearchParams): Promise<Task[]> {
    const result = await this.authenticated(`/tasks?${query}`)
    if (!Array.isArray(result)) throw new ApiError('The server returned an unexpected response. Please try again.')
    return result
  }

  createTask(fields: TaskFields) {
    return this.authenticated('/task', json('POST', fields))
  }

  updateTask(id: string, changes: TaskChanges) {
    return this.authenticated(`/task/${encodeURIComponent(id)}`, json('PATCH', changes))
  }

  deleteTask(id: string) {
    return this.authenticated(`/task/${encodeURIComponent(id)}`, { method: 'DELETE' })
  }

  async login(login: string, password: string) {
    await this.logoutFlight?.catch(() => {})
    const generation = this.generation
    await request('/auth/sign-in', { method: 'POST', body: new URLSearchParams({ login, password }) })
    this.current(generation)
  }

  register(email: string, login: string, password: string) {
    return request('/auth/sign-up', { method: 'POST', body: new URLSearchParams({ email, login, password }) })
  }

  logout() {
    if (this.logoutFlight) return this.logoutFlight
    this.invalidate()
    const flight = (async () => {
      await this.refreshFlight?.promise.catch(() => {})
      return request('/auth/sign-out', { method: 'POST' })
    })()
    this.logoutFlight = flight
    void flight.finally(() => { this.logoutFlight = undefined }).catch(() => {})
    return flight
  }
}

export const api = new SessionClient()

export function message(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}
