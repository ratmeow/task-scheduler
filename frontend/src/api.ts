export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message) }
}

export class SessionChangedError extends Error {}

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

  async main(): Promise<string> {
    const generation = this.generation
    const revision = this.refreshRevision
    let result: unknown
    try {
      result = await request('/main')
    } catch (error) {
      this.current(generation)
      if (!(error instanceof ApiError) || error.status !== 401) throw error
      if (revision === this.refreshRevision) {
        if (this.refreshFlight?.generation !== generation) {
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
        }
        await this.refreshFlight.promise
      }
      this.current(generation)
      result = await request('/main')
    }
    this.current(generation)
    if (result === undefined || result === null) return ''
    if (typeof result !== 'string') throw new ApiError('The server returned an unexpected response. Please try again.')
    return result
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
    this.invalidate()
    const flight = request('/auth/sign-out', { method: 'POST' })
    this.logoutFlight = flight
    return flight
  }
}

export const api = new SessionClient()
