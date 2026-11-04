import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import App from './App'
import { DISCLAIMER_TEXT } from './content/disclaimer'

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App screens', () => {
  it('shows the matters home with workflow links', async () => {
    renderAt('/')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Your matters' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Your matters' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /Review a clause/i }).length).toBeGreaterThan(1)
    expect(screen.getAllByRole('link', { name: /Law changes/i }).length).toBeGreaterThan(1)
    expect(screen.getAllByRole('link', { name: /Your control room/i }).length).toBeGreaterThan(1)
  })

  it('shows the evidence page for one answer', async () => {
    renderAt('/evidence/FND-001')
    expect(await screen.findByRole('heading', { name: 'Evidence for this answer' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: /Facts relied on/i })).toBeInTheDocument()
    expect(screen.getAllByText(/Meets the requirement/i).length).toBeGreaterThan(0)
  })

  it('shows the internal overview page', async () => {
    renderAt('/admin')
    expect(await screen.findByRole('heading', { name: 'Internal overview' })).toBeInTheDocument()
    expect(screen.getByText(/Not part of the lawyer workflow/i)).toBeInTheDocument()
  })

  it('shows the sign-in page', async () => {
    renderAt('/signin')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(screen.getByLabelText(/^Email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument()
  })

  it('shows the dictation page', async () => {
    renderAt('/dictate')
    expect(await screen.findByRole('heading', { name: 'Dictate a fact' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start recording/i })).toBeInTheDocument()
    expect(screen.getByText(/not relied on/i)).toBeInTheDocument()
  })

  it('shows the clause update page', async () => {
    renderAt('/clauses')
    expect(
      await screen.findByRole('heading', { name: 'Update clause wording' }),
    ).toBeInTheDocument()
    expect(await screen.findByLabelText(/^Clause$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Save new wording/i })).toBeInTheDocument()
  })

  it('shows the disclaimer on clause review', async () => {
    renderAt('/review')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toHaveTextContent(
      DISCLAIMER_TEXT.slice(0, 40),
    )
    expect(screen.getByRole('link', { name: 'Review a clause' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Review a clause' })).toBeInTheDocument()
    expect(screen.getByText(/Cross-border transfer/i)).toBeInTheDocument()
    expect(screen.getAllByText(/AI draft — not yet reviewed/i).length).toBeGreaterThan(0)
  })

  it('shows the disclaimer on source impact', async () => {
    renderAt('/impact')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Law changes' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Law changes' })).toBeInTheDocument()
    expect(screen.getAllByText(/AI draft — not yet reviewed/i).length).toBeGreaterThan(0)
  })

  it('shows the disclaimer on lawyer control', async () => {
    renderAt('/control')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Your control room' })).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Your control room' })).toBeInTheDocument()
    expect(screen.getAllByText(/AI draft — not yet reviewed/i).length).toBeGreaterThan(0)
  })
})
