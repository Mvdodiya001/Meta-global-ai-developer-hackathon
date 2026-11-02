import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DEMO_CHALLENGER_REPORT } from '../api/mocks/challenger'
import { SECOND_REVIEW_BLOCKING } from '../content/glossary'
import { ChallengerPanel } from './ChallengerPanel'

describe('ChallengerPanel', () => {
  it('renders nothing when there is no report', () => {
    const { container } = render(<ChallengerPanel report={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the blocking second-review sentence', () => {
    render(<ChallengerPanel report={DEMO_CHALLENGER_REPORT} />)
    expect(screen.getByRole('heading', { name: /Second-review pass/i })).toBeInTheDocument()
    expect(screen.getByText(SECOND_REVIEW_BLOCKING)).toBeInTheDocument()
    expect(screen.queryByText(/checker/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/muse-spark/i)).not.toBeInTheDocument()
  })

  it('lists a safe objection quote', () => {
    render(<ChallengerPanel report={DEMO_CHALLENGER_REPORT} />)
    expect(
      screen.getByText(/Clause 9.2 forbids all cross-border transfers/i),
    ).toBeInTheDocument()
  })
})
