import type { components } from './schema'

export type Finding = components['schemas']['Finding']
export type Proof = components['schemas']['Proof']
export type Fact = components['schemas']['Fact']
export type Clause = components['schemas']['Clause']
export type GraphSlice = components['schemas']['GraphSlice']
export type DiffResult = components['schemas']['DiffResult']
export type AuditTrail = components['schemas']['AuditTrail']
export type SourceVersionList = components['schemas']['SourceVersionList']
export type ImpactReport = components['schemas']['ImpactReport']
export type Matter = components['schemas']['Matter']
export type ToolCall = components['schemas']['ToolCall']
export type RunEvents = components['schemas']['RunEvents']
export type ClaimCreated = components['schemas']['ClaimCreated']
export type SourceList = components['schemas']['SourceList']
export type SourceVersion = components['schemas']['SourceVersion']
export type IngestResult = components['schemas']['IngestResult']
export type ReverifyResult = components['schemas']['ReverifyResult']

export type TrustClass =
  | 'document_extracted'
  | 'lawyer_confirmed'
  | 'ai_inferred'
  | 'disputed'

export type FindingStatus =
  | 'FOLLOWS'
  | 'RULED_OUT'
  | 'UNKNOWN'
  | 'REQUIRES_REVIEW'
