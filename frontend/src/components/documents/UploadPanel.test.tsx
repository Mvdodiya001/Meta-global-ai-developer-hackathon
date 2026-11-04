import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'

import { api } from '../../api/client'

import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { UploadPanel } from './UploadPanel'

describe('UploadPanel', () => {
  it('rejects unsupported file types with a plain message', async () => {
    render(
      <MemoryRouter>
        <UploadPanel />
      </MemoryRouter>,
    )
    const input = screen.getByLabelText(/^File$/i) as HTMLInputElement
    const file = new File(['data'], 'scan.tiff', { type: 'image/tiff' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(await screen.findByText(/not supported/i)).toBeInTheDocument()
  })

  it('tells the lawyer a failed file needs live mode, not that it is unreadable', async () => {
    const failed = {
      id: 'JOB-02',
      kind: 'document_extract',
      status: 'failed',
      stage: 'failed',
      document_id: 'DOC-02',
      result: null,
      error: 'CassetteMissing: no cassette for request abc123',
    }
    vi.spyOn(api, 'jobStatus').mockResolvedValueOnce(failed as never)
    render(
      <MemoryRouter>
        <UploadPanel />
      </MemoryRouter>,
    )
    const input = screen.getByLabelText(/^File$/i) as HTMLInputElement
    const file = new File(['%PDF fake'], 'other.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })
    const upload = screen.getByRole('button', { name: /Upload and extract/i })
    await waitFor(() => expect(upload).toBeEnabled())
    fireEvent.click(upload)
    expect(await screen.findByText(/demo is offline/i)).toBeInTheDocument()
    expect(screen.queryByText(/unreadable/i)).not.toBeInTheDocument()
    vi.restoreAllMocks()
  })

  it('uploads a PDF and shows per-page origins', async () => {
    render(
      <MemoryRouter>
        <UploadPanel />
      </MemoryRouter>,
    )
    const input = screen.getByLabelText(/^File$/i) as HTMLInputElement
    const file = new File(['%PDF fake'], 'mixed.pdf', { type: 'application/pdf' })
    fireEvent.change(input, { target: { files: [file] } })
    const upload = screen.getByRole('button', { name: /Upload and extract/i })
    await waitFor(() => expect(upload).toBeEnabled())
    fireEvent.click(upload)
    await waitFor(() => {
      expect(screen.getByText(/Done — 2 clauses extracted/i)).toBeInTheDocument()
    })
    expect(screen.getByText(/Page 1 — read from the file/i)).toBeInTheDocument()
    expect(screen.getByText(/Page 2 — transcribed from a scan/i)).toBeInTheDocument()
  })
})
