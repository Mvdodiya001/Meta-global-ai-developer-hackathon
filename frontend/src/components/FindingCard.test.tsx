import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { mockData } from '../api/mocks'
import { FindingCard } from './FindingCard'

describe('FindingCard', () => {
  it('shows status text and AI draft label by default', () => {
    render(<FindingCard finding={mockData.finding} />)
    expect(screen.getByText(/Follows/i)).toBeInTheDocument()
    expect(screen.getByText(/AI draft/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Finding FND-001/i })).toBeInTheDocument()
  })

  it('shows lawyer-reviewed badge when requested', () => {
    render(<FindingCard finding={mockData.finding} lawyerReviewed />)
    expect(screen.getByText(/Lawyer-reviewed/i)).toBeInTheDocument()
  })

  it('shows lawyer-reviewed when the finding state is REVIEWED', () => {
    render(
      <FindingCard
        finding={{
          ...mockData.finding,
          state: 'REVIEWED',
          ai_draft_label: 'Reviewed by lawyer',
        }}
      />,
    )
    expect(screen.getByText(/Lawyer-reviewed/i)).toBeInTheDocument()
    expect(screen.queryByText(/AI draft/i)).not.toBeInTheDocument()
  })
})
