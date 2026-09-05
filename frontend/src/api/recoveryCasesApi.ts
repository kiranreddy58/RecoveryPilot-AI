import { api } from './client';
import { RecoveryCase, CaseAuditEvent, Strategy, GuardianDecision } from '../types';

export const recoveryCasesApi = {
  getCases: (params?: { status?: string; limit?: number; offset?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.limit) q.set('limit', String(params.limit));
    if (params?.offset) q.set('offset', String(params.offset));
    const qs = q.toString();
    return api.get<RecoveryCase[]>(`/cases/${qs ? '?' + qs : ''}`);
  },

  getCaseById: (id: string) => api.get<RecoveryCase>(`/cases/${id}`),

  getCaseAudit: (id: string) => api.get<CaseAuditEvent[]>(`/cases/${id}/audit`),

  getCaseStrategies: (id: string) => api.get<Strategy[]>(`/cases/${id}/strategies`),

  getGuardianDecisions: (id: string) => api.get<GuardianDecision[]>(`/cases/${id}/guardian-decisions`),

  getCaseReceipt: (id: string) => api.get<any>(`/cases/${id}/receipt`),

  verifyAuditChain: (id: string) => api.get<any>(`/cases/${id}/verify-audit`),

  analyze: (id: string) => api.post<any>(`/cases/${id}/analyze`),

  simulate: (id: string) => api.post<any>(`/cases/${id}/simulate`),

  guardianCheck: (id: string, proposed_action?: string) =>
    api.post<any>(`/cases/${id}/guardian-check`, proposed_action ? { proposed_action } : undefined),

  execute: (id: string) => api.post<any>(`/cases/${id}/execute`),

  verify: (id: string) => api.post<any>(`/cases/${id}/verify`),

  runFullWorkflow: (id: string) => api.post<any>(`/cases/${id}/run`),

  escalate: (id: string, reason?: string, escalated_to?: string) =>
    api.post<any>(`/cases/${id}/escalate`, { reason, escalated_to }),

  approve: (id: string, approver_id?: string, notes?: string) =>
    api.post<any>(`/cases/${id}/approve`, { approver_id, notes }),

  reject: (id: string, rejector_id?: string, reason?: string) =>
    api.post<any>(`/cases/${id}/reject`, { rejector_id, reason }),
};
