import type { TrustClass } from '../api/types'

export function asTrustClass(value: string): TrustClass {
  if (
    value === 'document_extracted' ||
    value === 'lawyer_confirmed' ||
    value === 'ai_inferred' ||
    value === 'disputed'
  ) {
    return value
  }
  return 'ai_inferred'
}
