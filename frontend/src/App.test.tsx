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
    expect(await screen.findByText(/Cross-border transfer/i)).toBeInTheDocument()
  })

  it('shows the disclaimer on source impact', async () => {
    renderAt('/impact')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toBeInTheDocument()
    expect(await screen.findByText(/Amendment impact/i)).toBeInTheDocument()
  })

  it('shows the disclaimer on lawyer control', async () => {
    renderAt('/control')
    expect(screen.getByRole('note', { name: /legal disclaimer/i })).toBeInTheDocument()
    expect(await screen.findByText(/Premises & trust/i)).toBeInTheDocument()
  })
})
