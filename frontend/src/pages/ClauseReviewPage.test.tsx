import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ClauseReviewPage } from './ClauseReviewPage'

describe('ClauseReviewPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('runs mock verification and reveals tool trace then finding', async () => {
    render(
      <MemoryRouter>
        <ClauseReviewPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Cross-border transfer/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /run verification/i }))

    await waitFor(() => {
      expect(screen.getByText(/lookup_source/i)).toBeInTheDocument()
    })

    await vi.runAllTimersAsync()

    expect(await screen.findByRole('heading', { name: /Finding FND-001/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Source trace/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /What would change my answer/i })).toBeInTheDocument()
  })

  it('can show lawyer-reviewed badge after demo action', async () => {
    render(
      <MemoryRouter>
        <ClauseReviewPage />
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: /run verification/i }))
    await vi.runAllTimersAsync()
    await screen.findByRole('heading', { name: /Finding FND-001/i })

    fireEvent.click(screen.getByRole('button', { name: /mark lawyer-reviewed/i }))
    const finding = screen.getByRole('article', { name: /Finding FND-001/i })
    expect(finding).toHaveTextContent('Lawyer-reviewed')
    expect(finding).not.toHaveTextContent('AI draft')
  })
})
