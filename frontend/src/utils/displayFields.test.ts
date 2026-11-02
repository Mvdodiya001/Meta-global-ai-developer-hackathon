import { describe, expect, it } from 'vitest'

import { mockData } from '../api/mocks'
import { ANSWER_WOULD_NOT_FOLLOW, STATUS_LABELS, WOULD_STILL_FOLLOW } from '../content/glossary'
import {
  displayAnswerCaption,
  displayClauseQuote,
  displayLawVersionLabel,
  displayReasonLabel,
  displaySectionQuote,
  displayStatusLabel,
  displayWouldFollow,
} from './displayFields'

describe('displayFields', () => {
  it('uses v9 labels when they are present', () => {
    const finding = mockData.finding
    expect(displayStatusLabel(finding.status, finding.status_label, finding.state)).toBe(
      STATUS_LABELS.FOLLOWS,
    )
    expect(displayClauseQuote(finding)).toBe(finding.clause_quote)
    expect(displaySectionQuote(finding)).toBe(finding.section_quote)
    expect(displayLawVersionLabel(finding)).toBe(finding.law_version_label)
    expect(displayAnswerCaption(finding)).toBe('Clause 9.2')
  })

  it('falls back to glossary copy instead of an id', () => {
    const finding = {
      ...mockData.finding,
      status_label: '',
      clause_ref: 'FND-001',
      clause_quote: '',
      section_quote: '',
      law_version_label: '',
      law_version_date: '',
      fact_lines: [],
    }
    expect(displayStatusLabel(finding.status, finding.status_label)).toBe(STATUS_LABELS.FOLLOWS)
    expect(displayClauseQuote(finding)).toBe('A cited clause')
    expect(displaySectionQuote(finding)).toBe('A cited section of the law')
    expect(displayLawVersionLabel(finding)).toBe('Law version')
    expect(displayAnswerCaption(finding)).toBe('An answer that relied on this section')
    expect(displayReasonLabel('STALE', '')).toBe(STATUS_LABELS.STALE)
    expect(displayWouldFollow({ would_remain_valid: false, would_follow_label: '' })).toBe(
      ANSWER_WOULD_NOT_FOLLOW,
    )
    expect(displayWouldFollow({ would_remain_valid: true, would_follow_label: '' })).toBe(
      WOULD_STILL_FOLLOW,
    )
  })
})
