/**
 * Shared TypeScript definitions for miniBlue Enterprise Platform.
 */

export type UserRole = 'employee' | 'manager' | 'admin' | 'auditor';

export interface User {
  id: number;
  employee_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department: string | null;
  is_active: boolean;
  last_login_at?: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  role: UserRole;
  full_name: string;
  email: string;
}

export type GovernanceDecision =
  | 'APPROVE'
  | 'FLAG_FOR_REVIEW'
  | 'BLOCK'
  | 'APPROVE_WITH_EXCEPTION'
  | 'REJECT_CONFIRMED'
  | 'ESCALATED';

export type ReviewStatus = 'none' | 'pending' | 'approved_exception' | 'rejected';

export interface Citation {
  doc_id?: string;
  section?: string;
  text?: string;
  score?: number;
  source_file?: string;
  chunk_id?: number;
}

export interface ActionLog {
  id: number;
  entry_type: 'action' | 'review_resolution';
  ref_action_id?: number | null;
  session_id?: string | null;
  requester_id?: number | null;
  requester_name?: string | null;
  employee_id?: string | null;
  timestamp: string;
  intent: string;
  action_type?: string | null;
  payload: Record<string, any>;
  decision: GovernanceDecision;
  reason: string;
  cited_rule: string;
  prev_hash: string;
  entry_hash: string;
  review_status: ReviewStatus;
}

export interface ChatMessage {
  id: string | number;
  timestamp: string;
  user_message: string;
  agent_used: string;
  intent: string;
  confidence: number;
  reply: string;
  governance_decision?: GovernanceDecision | null;
  action_log_id?: number | null;
  latency_ms?: number;
  citations?: Citation[];
  action?: {
    id?: number | null;
    type?: string | null;
    payload?: Record<string, any> | null;
  } | null;
}

export interface ChatSession {
  session_id: string;
  user_id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_draft_json?: string | null;
}

export interface TelemetryData {
  total_actions: number;
  total_reviews_pending: number;
  approved_count: number;
  flagged_count: number;
  blocked_count: number;
  approved_rate: number;
  flagged_rate: number;
  blocked_rate: number;
  avg_latency_ms: number;
  intent_distribution: Record<string, number>;
  daily_trend: Array<{
    day: string;
    intent: string;
    decision: string;
    count: number;
  }>;
}

export interface AuditVerification {
  valid: boolean;
  entries: number;
  first_broken_id?: number | null;
  message: string;
  head_hash?: string | null;
}

export interface PolicyDoc {
  doc_id: string;
  title: string;
  filename: string;
  version: string;
  chunk_count: number;
  content?: string;
}

export interface PolicyChunk {
  chunk_id: number;
  section: string;
  heading_path?: string | null;
  text: string;
}

export interface SimulationShift {
  action_id: number;
  action_type?: string | null;
  original_decision: string;
  simulated_decision: string;
  rule_applied: string;
  description?: string | null;
}

export interface SimulationResult {
  params: {
    broadband_cap: number;
    ergonomic_cap: number;
    meal_cap: number;
    hotel_cap: number;
    sick_notice_threshold: number;
  };
  before: Record<string, number>;
  after: Record<string, number>;
  shifts: SimulationShift[];
  total_evaluated: number;
  chain_head_hash: string;
  created_at: string;
}

export interface EvalRun {
  id: number;
  run_by: string;
  metrics: {
    governance_accuracy: number;
    intent_accuracy: number;
    violation_catch_rate: number;
    in_scope_accuracy: number;
    refusal_accuracy: number;
    retrieval_hit_rate: number;
  };
  passed: boolean;
  git_sha?: string | null;
  created_at: string;
}
