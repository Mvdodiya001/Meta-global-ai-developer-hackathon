import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { DiffResult } from '../api/types'
import { DiffView } from './DiffView'

const diff: DiffResult = {
  against: 'SV-01',
  current: 'SV-02',
  changed_keys: ['DPDP-Act-2023_s8(6)'],
  before: [
    {
      id: 'P1',
      source_version_id: 'SV-01',
      key: 'DPDP-Act-2023_s1',
      text: 'Commencement wording',
      text_sha256: 'a',
      effective_from: '2025-11-13',
      effective_until: null,
    },
    {
      id: 'P2',
      source_version_id: 'SV-01',
      key: 'DPDP-Act-2023_s8(6)',
      text: 'Old breach intimation wording',
      text_sha256: 'b',
      effective_from: '2027-05-13',
      effective_until: null,
    },
  ],
  after: [
    {
      id: 'P3',
      source_version_id: 'SV-02',
      key: 'DPDP-Act-2023_s1',
      text: 'Commencement wording',
      text_sha256: 'a',
      effective_from: '2025-11-13',
      effective_until: null,
    },
    {
      id: 'P4',
      source_version_id: 'SV-02',
      key: 'DPDP-Act-2023_s8(6)',
      text: 'New breach intimation wording',
      text_sha256: 'c',
      effective_from: '2027-05-13',
      effective_until: null,
    },
  ],
}

describe('DiffView', () => {
  it('shows the amended section named in changed_keys, not the first provision', () => {
    render(<DiffView diff={diff} />)
    expect(screen.getByText(/Old breach intimation wording/i)).toBeInTheDocument()
    expect(screen.getByText(/New breach intimation wording/i)).toBeInTheDocument()
    expect(screen.queryByText(/Commencement wording/i)).not.toBeInTheDocument()
  })
})
