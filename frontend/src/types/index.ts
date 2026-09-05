export type BackendStatus = 'CONNECTING' | 'ONLINE' | 'OFFLINE';

export interface SystemStatus {
  frontend: 'ONLINE';
  backend: BackendStatus;
  backendVersion?: string;
  backendEnv?: string;
}

export enum CaseType {
  PAYMENT_FAILURE = "PAYMENT_FAILURE",
  CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT",
  OVERDUE_RECEIVABLE = "OVERDUE_RECEIVABLE",
  SUBSCRIPTION_FAILURE = "SUBSCRIPTION_FAILURE",
  PROMISE_TO_PAY_BROKEN = "PROMISE_TO_PAY_BROKEN",
}

export enum CaseState {
  DETECTED = "DETECTED",
  ANALYZING = "ANALYZING",
  DIAGNOSED = "DIAGNOSED",
  STRATEGY_SELECTED = "STRATEGY_SELECTED",
  GUARDIAN_REVIEW = "GUARDIAN_REVIEW",
  APPROVED = "APPROVED",
  BLOCKED = "BLOCKED",
  EXECUTING = "EXECUTING",
  VERIFYING = "VERIFYING",
  RECOVERED = "RECOVERED",
  FAILED = "FAILED",
  ESCALATED = "ESCALATED",
  STOPPED = "STOPPED",
  CLOSED = "CLOSED",
}

export enum RiskLevel {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum Priority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export interface RecoveryCase {
  id: string;
  case_id: string;
  merchant_id: string;
  customer_id: string;
  case_type: CaseType;
  reference_id: string | null;
  amount_at_risk: number | null;
  currency: string | null;
  status: CaseState;
  risk_level: RiskLevel | null;
  priority: Priority | null;
  source_event_id: string | null;
  root_cause: string | null;
  confidence: number | null;
  recommended_strategy: string | null;
  guardian_status: string | null;
  guardian_reason: string | null;
  recovered_amount: number | null;
  recovery_verified: boolean | null;
  escalation_level: string | null;
  stop_reason: string | null;
  retry_count: number | null;
  message_count: number | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface CaseAuditEvent {
  id: string;
  case_id: string;
  event_type: string;
  previous_state: string | null;
  new_state: string;
  actor_type: string;
  actor_id: string;
  reason: string | null;
  metadata_payload: any;
  previous_event_hash?: string | null;
  current_event_hash?: string | null;
  created_at: string;
}

export interface Strategy {
  id: string;
  strategy_name: string;
  strategy_label: string | null;
  description: string | null;
  recovery_probability: number | null;
  operational_cost: number | null;
  discount_amount: number | null;
  expected_net_recovery: number | null;
  rank: number | null;
  is_selected: string | null;
  ai_explanation: string | null;
  risk_notes: string | null;
}

export interface GuardianDecision {
  id: string;
  proposed_action: string;
  decision: string;
  reason: string | null;
  checks_passed: string[] | null;
  checks_failed: string[] | null;
  decided_by: string | null;
  human_approver: string | null;
  created_at: string;
}

export interface LiveMetrics {
  total_cases: number;
  active_cases: number;
  recovered_cases: number;
  revenue_at_risk: number;
  money_recovered: number;
  recovery_rate: number;
  blocked_actions: number;
  human_escalations: number;
}

export interface FullMetrics {
  total_cases: number;
  total_revenue_at_risk: number;
  total_recovered: number;
  recovery_rate_amount: number;
  recovery_rate_cases: number;
  status_breakdown: Record<string, number>;
  guardian: {
    total_checks: number;
    approved: number;
    blocked: number;
    human_required: number;
  };
  escalations: { total: number; open: number };
  actions: { total: number; successful: number; failed: number; unknown: number };
  by_type: Record<string, { count: number; revenue_at_risk: number; recovered: number }>;
  recent_cases: Array<{
    case_id: string;
    case_type: string;
    status: string;
    amount_at_risk: number;
    recovered_amount: number;
    created_at: string;
  }>;
}

export interface BatchRun {
  batch_id: string;
  status: string;
  total_cases: number;
  processed_cases: number;
  total_recovered: number;
  recovery_rate: number;
  created_at: string | null;
  completed_at: string | null;
}

export interface BatchResults {
  batch_id: string;
  status: string;
  total_cases: number;
  processed_cases: number;
  total_revenue_at_risk: number;
  total_recovered: number;
  recovery_rate: number;
  cases_recovered: number;
  cases_failed: number;
  cases_blocked: number;
  cases_escalated: number;
  cases_stopped: number;
  actions_executed: number;
  actions_blocked: number;
  human_escalations: number;
  breakdown_by_type: Record<string, any> | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface DemoResult {
  scenario: number;
  title: string;
  description: string;
  case_id: string;
  amount?: number;
  steps?: Array<{ step: string; result: any }>;
  final_status?: string;
  recovered_amount?: number;
  demonstration: string;
  guardian_decision?: string;
  guardian_reason?: string;
  ai_confidence?: number;
  unsafe_action_executed?: boolean;
  proposed_action?: string;
  retry_count?: number;
  max_retries?: number;
  promise_status?: string;
}
