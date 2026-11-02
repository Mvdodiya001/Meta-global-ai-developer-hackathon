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
