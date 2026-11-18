import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { api, ApiError, SessionChangedError } from './api'
import { registrationErrors } from './validation'

function message(error: unknown) {
  return error instanceof Error ? error.message : 'Something went wrong. Please try again.'
}

function RouteFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    document.querySelector<HTMLElement>('h1')?.focus()
    document.title = `${pathname === '/register' ? 'Create account' : pathname === '/login' ? 'Log in' : 'Workspace'} · Task Scheduler`
  }, [pathname])
  return null
}

function AuthPage({ register = false }: { register?: boolean }) {
  const navigate = useNavigate()
  const location = useLocation()
  const notice = location.state as { login?: string; success?: string; error?: string; logoutFailed?: boolean } | null
  const [login, setLogin] = useState(notice?.login || '')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [logoutFailed, setLogoutFailed] = useState(!!notice?.logoutFailed)
  const [logoutNotice, setLogoutNotice] = useState('')
  const form = useRef<HTMLFormElement>(null)
  const active = useRef(true)
  useEffect(() => {
    active.current = true
    return () => { active.current = false }
  }, [])

  async function retryLogout() {
    setPending(true)
    try {
      await api.logout()
      if (active.current) {
        setLogoutFailed(false)
        setLogoutNotice('You have been logged out.')
      }
    } catch (error) {
      if (active.current) setLogoutNotice(message(error))
    } finally {
      if (active.current) setPending(false)
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending) return
    const invalid = register ? registrationErrors(email, login, password) : {
      ...(!login ? { login: 'Enter your login.' } : {}),
      ...(!password ? { password: 'Enter your password.' } : {}),
    }
    setErrors(invalid)
    setError('')
    const first = Object.keys(invalid)[0]
    if (first) {
      form.current?.querySelector<HTMLInputElement>(`[name="${first}"]`)?.focus()
      return
    }
    setPending(true)
    try {
      if (register) await api.register(email, login, password)
      else await api.login(login, password)
      if (!active.current) return
      setPassword('')
      navigate(register ? '/login' : '/', {
        replace: true,
        state: register ? { login, success: 'Account created. Log in to continue.' } : null,
      })
    } catch (error) {
      if (active.current && !(error instanceof SessionChangedError)) setError(message(error))
    } finally {
      if (active.current) setPending(false)
    }
  }

  return <main className="auth-page" id="content">
    <div className="auth-heading">
      <p className="eyebrow">YOUR WORK, IN ONE PLACE</p>
      <h1 tabIndex={-1}>{register ? 'Create your account' : 'Welcome back'}</h1>
      <p className="muted">{register ? 'A little structure for what comes next.' : 'Log in to your Task Scheduler workspace.'}</p>
    </div>
    {notice?.success && <p className="notice success" role="status">{notice.success}</p>}
    {notice?.error && !logoutNotice && <p className="notice" role="alert">{notice.error}</p>}
    {logoutNotice && <p className={`notice ${logoutFailed ? '' : 'success'}`} role="status">{logoutNotice}</p>}
    {logoutFailed && <button className="retry-logout" disabled={pending} onClick={() => void retryLogout()}>Retry sign-out</button>}
    <form ref={form} onSubmit={submit} noValidate aria-busy={pending}>
      {register && <div className="field">
        <label htmlFor="email">Email</label>
        <input id="email" name="email" type="email" autoComplete="email" required value={email}
          disabled={pending} onChange={event => setEmail(event.target.value)}
          aria-invalid={!!errors.email} aria-describedby={errors.email ? 'email-error' : undefined} />
        {errors.email && <p className="field-error" id="email-error">{errors.email}</p>}
      </div>}
      <div className="field">
        <label htmlFor="login">Login</label>
        <input id="login" name="login" autoComplete="username" autoCapitalize="none" spellCheck={false}
          required disabled={pending} value={login} onChange={event => setLogin(event.target.value)}
          aria-invalid={!!errors.login} aria-describedby={errors.login ? 'login-error' : undefined} />
        {errors.login && <p className="field-error" id="login-error">{errors.login}</p>}
      </div>
      <div className="field">
        <label htmlFor="password">Password</label>
        <input id="password" name="password" type="password" autoComplete={register ? 'new-password' : 'current-password'}
          required disabled={pending} value={password} onChange={event => setPassword(event.target.value)}
          aria-invalid={!!errors.password} aria-describedby={errors.password ? 'password-error' : register ? 'password-hint' : undefined} />
        {errors.password ? <p className="field-error" id="password-error">{errors.password}</p> :
          register && <p className="hint" id="password-hint">At least 8 characters. Use Latin letters and a digit or !@#$%^&*_.</p>}
      </div>
      {error && <p className="notice" role="alert">{error}</p>}
      <button className="primary full" disabled={pending} type="submit">
        {pending ? register ? 'Creating account…' : 'Logging in…' : register ? 'Create account' : 'Log in'}
      </button>
    </form>
    <p className="auth-switch">{register ? 'Already have an account?' : 'New here?'}{' '}
      <Link to={register ? '/login' : '/register'}>{register ? 'Log in' : 'Create an account'}</Link>
    </p>
  </main>
}

function MainPage() {
  const navigate = useNavigate()
  const [content, setContent] = useState<string | null>(null)
  const [pending, setPending] = useState(true)
  const [error, setError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const sequence = useRef(0)

  function load() {
    const current = ++sequence.current
    return api.main().then(result => {
      if (current === sequence.current) setContent(result)
    }).catch((error: unknown) => {
      if (current !== sequence.current || error instanceof SessionChangedError) return
      if (error instanceof ApiError && error.status === 401) {
        navigate('/login', { replace: true, state: { error: 'Please log in to continue.' } })
      } else setError(message(error))
    }).finally(() => {
      if (current === sequence.current) setPending(false)
    })
  }

  function reload() {
    setPending(true)
    setError('')
    void load()
  }

  useEffect(() => {
    void load()
    return () => { sequence.current += 1 }
    // Only restore on mount; reload is an explicit user action.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function logout() {
    sequence.current += 1
    setContent(null)
    setLoggingOut(true)
    let error: string | undefined
    try { await api.logout() } catch (cause) {
      error = `Sign-out could not be confirmed. ${message(cause)} Retry sign-out to clear your server session.`
    }
    navigate('/login', { replace: true, state: error ? { error, logoutFailed: true } : { success: 'You have been logged out.' } })
  }

  return <main className="workspace" id="content">
    <div className="workspace-heading">
      <div><p className="eyebrow">YOUR WORKSPACE</p><h1 tabIndex={-1}>A fresh start.</h1></div>
      <button onClick={() => void logout()} disabled={loggingOut}>{loggingOut ? 'Logging out…' : 'Log out'}</button>
    </div>
    <section className="response-panel" aria-labelledby="response-title" aria-busy={pending || loggingOut}>
      <div className="panel-heading"><h2 id="response-title">Welcome to Task Scheduler</h2>
        <button onClick={reload} disabled={pending || loggingOut}>{pending ? 'Loading…' : 'Reload'}</button>
      </div>
      {loggingOut ? <p role="status" className="muted">Closing your session…</p> : <>
        {pending && <p role="status" className="muted">{content === null ? 'Checking your session…' : 'Updating your workspace…'}</p>}
        {error && <div className="notice" role="alert"><p>{error}</p><button onClick={reload}>Try again</button></div>}
        {content !== null && <p className="server-message">{content || 'The server returned an empty response. Use Reload to check again.'}</p>}
      </>}
    </section>
  </main>
}

export default function App() {
  return <BrowserRouter>
    <a className="skip-link" href="#content">Skip to content</a>
    <header className="site-header"><Link className="brand" to="/">Task Scheduler<span className="brand-dot" aria-hidden="true" /></Link></header>
    <RouteFocus />
    <Routes>
      <Route path="/" element={<MainPage />} />
      <Route path="/login" element={<AuthPage key="login" />} />
      <Route path="/register" element={<AuthPage key="register" register />} />
      <Route path="/index.html" element={<Navigate to="/" replace />} />
      <Route path="*" element={<main className="auth-page" id="content"><h1 tabIndex={-1}>Page not found</h1><p className="muted">This page doesn’t exist.</p><Link to="/">Go to your workspace</Link></main>} />
    </Routes>
    <footer>Make room for what matters.</footer>
  </BrowserRouter>
}

