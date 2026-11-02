import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { clearClaimId, rememberClaimId } from '../api/demoSession'
import { FACT_MISMATCH } from '../content/glossary'
import { LawyerControlPage } from './LawyerControlPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <LawyerControlPage />
    </MemoryRouter>,
  )
}

describe('LawyerControlPage', () => {
  afterEach(() => {
    clearClaimId()
  })

  it('scans a page and shows the clause as an AI draft', async () => {
    renderPage()
    const input = await screen.findByLabelText(/^Add a scanned clause page$/i, {
      selector: 'input',
    })
    const file = new File(['png-bytes'], 'clause_9_2_page.png', { type: 'image/png' })
    fireEvent.change(input, { target: { files: [file] } })

    const scan = screen.getByRole('region', { name: /Add a scanned clause page/i })
    expect(await within(scan).findByText(/Scanned page states Nimbus/i)).toBeInTheDocument()
    expect(within(scan).getByText(/Taken from the document/i)).toBeInTheDocument()
    expect(within(scan).getByText(/Clause 9\.2/i)).toBeInTheDocument()
  })

  it('dictates a WAV clip and shows a proposed fact', async () => {
    renderPage()
    const input = await screen.findByLabelText(/^Dictate a fact$/i, { selector: 'input' })
    const file = new File(['RIFF'], 'dictation_fact.wav', { type: 'audio/wav' })
    fireEvent.change(input, { target: { files: [file] } })

    const dictation = screen.getByRole('region', { name: /^Dictate a fact$/i })
    expect(
      await within(dictation).findByText(/Nimbus keeps transfer logs for review/i),
    ).toBeInTheDocument()
    expect(within(dictation).getByText(/Proposed — not yet approved by you/i)).toBeInTheDocument()
  })

  it('asks to run clause review first when no claim exists', async () => {
    clearClaimId()
    renderPage()
    expect(await screen.findByRole('heading', { name: /Your control room/i })).toBeInTheDocument()
    expect(await screen.findByText(/Ask about a clause first/i)).toBeInTheDocument()
    const approve = screen.queryAllByRole('button', { name: /^Approve$/i })
    for (const button of approve) {
      expect(button).toBeDisabled()
    }
    expect(screen.getByRole('button', { name: /^Re-check$/i })).toBeDisabled()
  })

  describe('after Screen 1 has a claim', () => {
    beforeEach(() => {
      rememberClaimId('from-screen-1')
    })

    it('approves an extracted fact and shows lawyer-reviewed', async () => {
      renderPage()
      const item = await screen.findByRole('listitem', {
        name: /Clause 9.2 permits transfer of order data outside India/i,
      })

      fireEvent.click(within(item).getByRole('button', { name: /^Approve$/i }))

      await waitFor(() => {
        expect(item).toHaveTextContent('Confirmed by you')
      })
      expect(item).toHaveTextContent('Lawyer-reviewed')
    })

    it('shows Already confirmed when a fact is approved twice', async () => {
      renderPage()
      const item = await screen.findByRole('listitem', {
        name: /Clause 9.2 permits transfer of order data outside India/i,
      })

      fireEvent.click(within(item).getByRole('button', { name: /^Approve$/i }))
      await waitFor(() => {
        expect(item).toHaveTextContent('Confirmed by you')
      })

      fireEvent.click(within(item).getByRole('button', { name: /^Approve$/i }))

      expect(await screen.findByRole('status')).toHaveTextContent('Already confirmed')
    })

    it('challenges a premise and recomputes dependents to unknown', async () => {
      renderPage()
      const item = await screen.findByRole('listitem', {
        name: /Clause 9.2 permits transfer of order data outside India/i,
      })

      fireEvent.click(within(item).getByRole('button', { name: /^Challenge$/i }))

      await waitFor(() => {
        expect(item).toHaveTextContent('Disputed by you')
      })
      expect(screen.getByText(/Related answers were updated/i)).toBeInTheDocument()
      expect(screen.getByText(/Illustration, not a server answer/i)).toBeInTheDocument()
      expect(screen.getByRole('article', { name: /Current answer/i })).toHaveTextContent(
        'Cannot be determined from the available material',
      )
    })

    it('marks the provision not in force when as-of is before commencement', async () => {
      renderPage()
      const asOfInput = await screen.findByLabelText(/^As-of date$/i)

      fireEvent.change(asOfInput, {
        target: { value: '2025-09-01' },
      })

      expect(screen.getByText(/not in force/i)).toBeInTheDocument()
      expect(
        screen.getByRole('article', { name: /Answer as of this date/i }),
      ).toHaveTextContent('Cannot be determined from the available material')
    })

    it('returns unknown with no invented citations for an out-of-corpus claim', async () => {
      renderPage()
      await screen.findByRole('button', { name: /ask a question this file does not cover/i })

      fireEvent.click(
        screen.getByRole('button', { name: /ask a question this file does not cover/i }),
      )

      expect(await screen.findByText(/no source on file covers this/i)).toBeInTheDocument()
      expect(
        screen.getByRole('article', { name: /Answer that cannot be determined/i }),
      ).toHaveTextContent('Cannot be determined from the available material')
    })

    it('rejects changed fact wording that no longer matches the document', async () => {
      renderPage()
      const editor = await screen.findByLabelText(/Fact sentence/i)
      fireEvent.change(editor, {
        target: { value: 'This wording is not in the document.' },
      })
      fireEvent.click(screen.getByRole('button', { name: /^Re-check$/i }))

      expect(await screen.findByText(FACT_MISMATCH)).toBeInTheDocument()
      expect(screen.getByText(/A second review flagged this — needs your review/i)).toBeInTheDocument()
    })
  })
})
