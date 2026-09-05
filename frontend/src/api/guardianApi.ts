import { api } from './client';

export interface GuardianPolicies {
  MAX_PAYMENT_RETRIES: number;
  MAX_MESSAGES: number;
  MIN_HOURS_BETWEEN_CONTACTS: number;
  MAX_RECOVERY_DAYS: number;
  HIGH_VALUE_THRESHOLD_INR: number;
  MIN_AI_CONFIDENCE_FOR_AUTO_ACTION: number;
  MAX_DISCOUNT_PERCENT: number;
  [key: string]: any;
}

export interface PolicyResponse {
  active_policies: GuardianPolicies;
  default_policies?: GuardianPolicies;
  message?: string;
}

export const guardianApi = {
  getPolicies: () => api.get<PolicyResponse>('/guardian/policies'),
  updatePolicies: (policies: GuardianPolicies) =>
    api.post<PolicyResponse>('/guardian/policies', policies),
  resetPolicies: () => api.post<PolicyResponse>('/guardian/policies/reset'),
};
