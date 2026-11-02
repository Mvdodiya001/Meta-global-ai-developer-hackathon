import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { mockData } from '../api/mocks'
import { FindingCard } from './FindingCard'

describe('FindingCard', () => {
  it('shows status text and AI draft label by default', () => {
    render(<FindingCard finding={mockData.finding} />)
    expect(
      screen.getByText(/Meets the requirement — on the facts and law listed below/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/AI draft/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Legal test/i })).toBeInTheDocument()
    expect(screen.getByText(mockData.finding.clause_quote)).toBeInTheDocument()
    expect(screen.getByText(mockData.finding.section_quote)).toBeInTheDocument()
    expect(
      screen.getByText(`${mockData.finding.law_version_label} · ${mockData.finding.law_version_date}`),
    ).toBeInTheDocument()
    expect(screen.queryByText(/FND-/i)).not.toBeInTheDocument()
  })

  it('falls back to glossary copy when display fields are missing', () => {
    render(
      <FindingCard
        finding={{
          ...mockData.finding,
          status_label: '',
          clause_quote: '',
          section_quote: '',
          law_version_label: '',
          law_version_date: '',
          fact_lines: [],
        }}
      />,
    )
    expect(screen.getByText(/A cited clause/i)).toBeInTheDocument()
    expect(screen.getByText(/A cited section of the law/i)).toBeInTheDocument()
    expect(screen.getByText(/Law version/i)).toBeInTheDocument()
    expect(screen.queryByText(/FND-/i)).not.toBeInTheDocument()
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
