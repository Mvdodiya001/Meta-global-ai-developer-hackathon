import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DictationPage } from './DictationPage'

describe('DictationPage live toggle', () => {
  it('defaults to one-shot flow with no live region', async () => {
    render(<DictationPage />)

    const toggle = await screen.findByLabelText(/Transcribe live/i)
    expect(toggle).not.toBeChecked()
    expect(screen.queryByText(/Live transcript \(draft — not saved\)/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start recording/i })).toBeInTheDocument()
  })

  it('reveals the live draft region when toggled on', async () => {
    render(<DictationPage />)

    const toggle = await screen.findByLabelText(/Transcribe live/i)
    fireEvent.click(toggle)

    await waitFor(() => {
      expect(screen.getByText(/Live transcript \(draft — not saved\)/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/Listening…/i)).toBeInTheDocument()
  })
})
