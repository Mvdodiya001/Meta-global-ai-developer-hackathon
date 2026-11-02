import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { DEFAULT_AS_OF, DEFAULT_VERIFY_QUESTION, SECONDARY_AS_OF } from '../api/mocks/runTrace'
import { ClauseReviewPage } from './ClauseReviewPage'

describe('ClauseReviewPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('defaults to the recorded 9.2 question and as-of dates', async () => {
    render(
      <MemoryRouter>
        <ClauseReviewPage />
      </MemoryRouter>,
    )

    expect(await screen.findByLabelText(/Legal question/i)).toHaveValue(
      DEFAULT_VERIFY_QUESTION,
    )
    expect(screen.getByLabelText(/^As-of date$/i)).toHaveValue(DEFAULT_AS_OF)
    expect(screen.getByRole('option', { name: SECONDARY_AS_OF })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Ask about a clause/i })).toBeInTheDocument()
  })

  it('asks about a clause and shows the legal test without a tool trace', async () => {
    render(
      <MemoryRouter>
        <ClauseReviewPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Cross-border transfer/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^Ask$/i }))
    await vi.runAllTimersAsync()

    expect(await screen.findByRole('heading', { name: /Legal test/i })).toBeInTheDocument()
    expect(
      screen.getByText(/Meets the requirement — on the facts and law listed below/i),
    ).toBeInTheDocument()
    expect(
      screen.getAllByText(/Nimbus may transfer order data to its analytics cluster/i).length,
    ).toBeGreaterThan(0)
    expect(screen.getByRole('heading', { name: /^Section$/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /What would change this answer/i })).toBeInTheDocument()
    expect(screen.getAllByText(/Confirmed by You/i).length).toBeGreaterThan(0)
    expect(screen.queryByText(/lookup_source/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Tool trace/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/FND-/i)).not.toBeInTheDocument()
  })

  it('can show lawyer-reviewed badge after demo action', async () => {
    render(
      <MemoryRouter>
        <ClauseReviewPage />
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: /^Ask$/i }))
    await vi.runAllTimersAsync()
    await screen.findByRole('heading', { name: /Legal test/i })

    fireEvent.click(screen.getByRole('button', { name: /mark lawyer-reviewed/i }))
    const finding = await screen.findByRole('article', { name: /Legal test/i })
    await waitFor(() => {
      expect(finding).toHaveTextContent('Lawyer-reviewed')
    })
    expect(finding).not.toHaveTextContent('AI draft')
  })
})
