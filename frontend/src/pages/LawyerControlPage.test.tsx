import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { LawyerControlPage } from './LawyerControlPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <LawyerControlPage />
    </MemoryRouter>,
  )
}

describe('LawyerControlPage', () => {
  it('approves an extracted fact and shows lawyer-reviewed', async () => {
    renderPage()
    expect(await screen.findByRole('listitem', { name: /Fact F-001/i })).toBeInTheDocument()

    fireEvent.click(screen.getAllByRole('button', { name: /^Approve$/i })[0])

    await waitFor(() => {
      expect(screen.getByRole('listitem', { name: /Fact F-001/i })).toHaveTextContent(
        'Lawyer confirmed',
      )
    })
    expect(screen.getByRole('listitem', { name: /Fact F-001/i })).toHaveTextContent(
      'Lawyer-reviewed',
    )
  })

  it('challenges a premise and recomputes dependents to unknown', async () => {
    renderPage()
    await screen.findByRole('listitem', { name: /Fact F-001/i })

    fireEvent.click(screen.getAllByRole('button', { name: /^Challenge$/i })[0])

    await waitFor(() => {
      expect(screen.getByRole('listitem', { name: /Fact F-001/i })).toHaveTextContent('Disputed')
    })
    expect(screen.getByText(/Dependents recomputed/i)).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Finding FND-001/i })).toHaveTextContent('Unknown')
  })

  it('marks the provision not in force when as-of is before commencement', async () => {
    renderPage()
    const asOfInput = await screen.findByLabelText(/^As-of date$/i)

    fireEvent.change(asOfInput, {
      target: { value: '2025-09-01' },
    })

    expect(screen.getByText(/not in force/i)).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Finding FND-ASOF/i })).toHaveTextContent('Unknown')
  })

  it('returns unknown with no invented citations for an out-of-corpus claim', async () => {
    renderPage()
    await screen.findByRole('button', { name: /ask out-of-corpus claim/i })

    fireEvent.click(screen.getByRole('button', { name: /ask out-of-corpus claim/i }))

    expect(await screen.findByText(/no source on file covers this/i)).toBeInTheDocument()
    expect(screen.getByRole('article', { name: /Finding FND-UNK/i })).toHaveTextContent('Unknown')
  })

  it('rejects a tampered proof with PREMISE_MISMATCH', async () => {
    renderPage()
    const editor = await screen.findByLabelText(/Proof JSON/i)
    fireEvent.change(editor, {
      target: { value: JSON.stringify({ tampered: true }) },
    })
    fireEvent.click(screen.getByRole('button', { name: /verify proof/i }))

    expect(await screen.findByText(/PREMISE_MISMATCH/i)).toBeInTheDocument()
    expect(screen.getByText(/Checker rejects/i)).toBeInTheDocument()
    expect(screen.getByText(/Blocking objection forces Requires review/i)).toBeInTheDocument()
  })
})
