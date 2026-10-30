import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DEMO_CHALLENGER_REPORT } from '../api/mocks/challenger'
import { ChallengerPanel } from './ChallengerPanel'

describe('ChallengerPanel', () => {
  it('shows idle copy when the challenger is off', () => {
    render(<ChallengerPanel enabled={false} report={null} />)
    expect(screen.getByRole('heading', { name: /Challenger/i })).toBeInTheDocument()
    expect(screen.getByText(/Challenger is off/i)).toBeInTheDocument()
  })

  it('lists blocking objections and requires review', () => {
    render(<ChallengerPanel enabled report={DEMO_CHALLENGER_REPORT} />)
    expect(screen.getByText(/Blocking objection forces Requires review/i)).toBeInTheDocument()
    expect(screen.getAllByText(/muse-spark-1.2/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Blocking$/i).length).toBeGreaterThan(0)
    expect(
      screen.getByText(/Cited premise text does not match the admitted fact/i),
    ).toBeInTheDocument()
  })
})
