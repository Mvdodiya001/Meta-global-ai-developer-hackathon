import type { components } from './schema'

export type Finding = components['schemas']['Finding']
export type FactLine = components['schemas']['FactLine']
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
export type FactAction = components['schemas']['FactAction']
export type ProofVerifyResult = components['schemas']['ProofVerifyResult']
export type ProofVerifyBody = components['schemas']['ProofVerifyBody']
export type DocumentList = components['schemas']['DocumentList']
export type IngestVersionBody = components['schemas']['IngestVersionBody']
export type Run = components['schemas']['Run']
export type ReviewBody = components['schemas']['ReviewBody']
export type ReviewResult = components['schemas']['ReviewResult']
export type CounterfactualResult = components['schemas']['CounterfactualResult']
export type CounterfactualAffected = components['schemas']['CounterfactualAffected']
export type ReverifyList = components['schemas']['ReverifyList']
export type ReverifyListItem = components['schemas']['ReverifyListItem']
export type ScanRequest = components['schemas']['ScanRequest']
export type ScanResult = components['schemas']['ScanResult']
export type DictationRequest = components['schemas']['DictationRequest']
export type DictationResult = components['schemas']['DictationResult']

export type CounterfactualBody = {
  source_version_id: string
}

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
  | 'CONFLICTING'
