import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { SourceImpactPage } from './SourceImpactPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <SourceImpactPage />
    </MemoryRouter>,
  )
}

describe('SourceImpactPage', () => {
  it('loads the simulated version, diff, stale graph summary, and audit trail', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: /Amendment impact/i })).toBeInTheDocument()
    expect(await screen.findByText(/^Simulated$/i)).toBeInTheDocument()
    expect(await screen.findByText(/3 of 8 findings stale/i)).toBeInTheDocument()
    expect(screen.getByText(/Personal data may be transferred outside India except to notified countries/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Audit trail/i })).toBeInTheDocument()
  })

  it('flags no findings when the decoy source is ingested', async () => {
    renderPage()
    await screen.findByLabelText(/Legal source/i)

    fireEvent.change(screen.getByLabelText(/Legal source/i), {
      target: { value: 'SRC-DECOY' },
    })
    fireEvent.click(screen.getByRole('button', { name: /ingest source change/i }))

    expect(await screen.findByText(/No findings flagged/i)).toBeInTheDocument()
    expect(screen.queryByText(/^Simulated$/i)).not.toBeInTheDocument()
  })

  it('keeps the old finding and shows the new one after re-verify', async () => {
    renderPage()
    await screen.findByText(/3 of 8 findings stale/i)

    fireEvent.click(screen.getByRole('button', { name: /re-verify/i }))

    expect(await screen.findByRole('heading', { name: /Before · FND-001/i })).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Finding FND-001/i })).toHaveTextContent('Follows')
    expect(screen.getByRole('heading', { name: /After · FND-002/i })).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Finding FND-002/i })).toHaveTextContent('Unknown')
  })
})
