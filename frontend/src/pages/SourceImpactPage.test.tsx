import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ANSWER_WOULD_NOT_FOLLOW, PREVIEW_LAW_CHANGE } from '../content/glossary'
import { SourceImpactPage } from './SourceImpactPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <SourceImpactPage />
    </MemoryRouter>,
  )
}

describe('SourceImpactPage', () => {
  it('loads the simulated version, diff, stale graph summary, and history', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: /Law changes/i })).toBeInTheDocument()
    expect(await screen.findByText(/^Simulated$/i)).toBeInTheDocument()
    expect(await screen.findByText(/3 of 8 answers need re-check/i)).toBeInTheDocument()
    expect(
      screen.getAllByText(/Personal data may be transferred outside India except to notified countries/i)
        .length,
    ).toBeGreaterThan(0)
    expect(screen.getByRole('heading', { name: /History/i })).toBeInTheDocument()
  })

  it('flags no answers when the decoy source is applied', async () => {
    renderPage()
    await screen.findByLabelText(/Legal source/i)

    fireEvent.change(screen.getByLabelText(/Legal source/i), {
      target: { value: 'SRC-DECOY' },
    })
    fireEvent.click(screen.getByRole('button', { name: /apply this law change/i }))

    expect(await screen.findByText(/No answers need re-check/i)).toBeInTheDocument()
    expect(screen.queryByText(/^Simulated$/i)).not.toBeInTheDocument()
  })

  it('runs a read-only preview without ids or JSON', async () => {
    renderPage()
    expect(
      await screen.findByRole('button', { name: PREVIEW_LAW_CHANGE }),
    ).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: PREVIEW_LAW_CHANGE }))

    expect(await screen.findByText(ANSWER_WOULD_NOT_FOLLOW)).toBeInTheDocument()
    expect(screen.getByText(PREVIEW_LAW_CHANGE, { selector: 'p' })).toBeInTheDocument()
    expect(screen.queryByText(/FND-/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/rule_RC_/)).not.toBeInTheDocument()
    expect(screen.queryByText(/\{/)).not.toBeInTheDocument()
  })

  it('lists the re-check queue with glossary reasons', async () => {
    renderPage()
    expect(await screen.findByText(/Two readings of the law conflict — your call/i)).toBeInTheDocument()
    expect(
      screen.getAllByText(/Needs re-check: the law it relied on has changed/i).length,
    ).toBeGreaterThan(0)
    expect(screen.getAllByText(/Clause 9\.2/i).length).toBeGreaterThan(0)
    expect(screen.queryByText(/FND-CONFLICT/)).not.toBeInTheDocument()
    expect(screen.queryByText(/sha256/i)).not.toBeInTheDocument()
  })

  it('keeps the old answer and shows the new one after re-check', async () => {
    renderPage()
    await screen.findByText(/3 of 8 answers need re-check/i)

    fireEvent.click(screen.getByRole('button', { name: /^Re-check$/i }))

    expect(await screen.findByRole('article', { name: /Earlier answer/i })).toHaveTextContent(
      'Meets the requirement',
    )
    expect(screen.getByRole('article', { name: /Later answer/i })).toHaveTextContent(
      'Cannot be determined from the available material',
    )
  })
})
