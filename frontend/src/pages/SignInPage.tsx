import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, storeToken } from '../api/client'
import { PageHeader } from '../components/layout/PageHeader'
import { Button } from '../components/ui/Button'
import { IconLock, IconUser } from '../components/ui/Icons'
import { StateMessage } from '../components/ui/StateMessage'

export function SignInPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const canSubmit =
    email.trim().length > 0 &&
    password.length > 0 &&
    (mode === 'login' || name.trim().length > 0)

  async function submit() {
    if (!canSubmit || busy) {
      return
    }
    setBusy(true)
    setError(null)
    try {
      const result =
        mode === 'login'
          ? await api.login({ email, password })
          : await api.register({ email, password, name })
      storeToken(result.token)
      navigate('/')
    } catch {
      setError(
        mode === 'login'
          ? 'Email or password is incorrect.'
          : 'That account could not be created. The email may already be registered, or the password needs 8 or more characters.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ct-page ct-page--narrow">
      <PageHeader
        eyebrow="Account"
        title={mode === 'login' ? 'Sign in' : 'Create your account'}
        description="Signing in keeps your reviews attached to the right matter and person."
      />

      <section className="ct-panel ct-panel--surface" aria-labelledby="signin-heading">
        <div className="ct-panel-head">
          <div>
            <h2 id="signin-heading" className="ct-panel-title">
              Your details
            </h2>
            <p className="ct-panel-desc">
              {mode === 'login'
                ? 'Use the email and password for your workspace.'
                : 'Create an account to keep a record of who reviewed each answer.'}
            </p>
          </div>
          <span className="ct-badge">
            {mode === 'login' ? <IconUser size={12} /> : <IconLock size={12} />}
            {mode === 'login' ? 'Existing account' : 'New account'}
          </span>
        </div>

        <form
          className="ct-panel-body space-y-3"
          onSubmit={(event) => {
            event.preventDefault()
            void submit()
          }}
        >
          {mode === 'register' ? (
            <div className="ct-field">
              <label htmlFor="signin-name" className="ct-label">
                Name
              </label>
              <input
                id="signin-name"
                value={name}
                autoComplete="name"
                required
                onChange={(event) => setName(event.target.value)}
                className="ct-input"
              />
            </div>
          ) : null}

          <div className="ct-field">
            <label htmlFor="signin-email" className="ct-label">
              Email
            </label>
            <input
              id="signin-email"
              type="email"
              value={email}
              autoComplete="email"
              required
              onChange={(event) => setEmail(event.target.value)}
              className="ct-input"
            />
          </div>

          <div className="ct-field">
            <label htmlFor="signin-password" className="ct-label">
              Password
            </label>
            <input
              id="signin-password"
              type="password"
              value={password}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
              minLength={mode === 'register' ? 8 : undefined}
              onChange={(event) => setPassword(event.target.value)}
              className="ct-input"
            />
            {mode === 'register' ? (
              <p className="ct-help">Use at least 8 characters.</p>
            ) : null}
          </div>

          {error ? (
            <StateMessage tone="danger" live="alert">
              {error}
            </StateMessage>
          ) : null}

          <div className="flex flex-wrap items-center gap-2 border-t border-ct-line pt-3">
            <Button type="submit" variant="primary" disabled={!canSubmit} loading={busy}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </Button>
            <Button
              variant="ghost"
              disabled={busy}
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login')
                setError(null)
              }}
            >
              {mode === 'login' ? 'New here? Create an account' : 'Already registered? Sign in'}
            </Button>
          </div>
        </form>
      </section>

      <p className="ct-help">
        Your session token is held in this browser only. Signing out clears it locally.
      </p>
    </div>
  )
}
