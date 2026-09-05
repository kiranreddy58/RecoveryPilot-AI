import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { CheckSquare, Loader2, AlertCircle, CheckCircle, XCircle, ArrowRight, RefreshCw, User } from 'lucide-react';
import { recoveryCasesApi } from '../api/recoveryCasesApi';
import { RecoveryCase } from '../types';
import { StatusBadge, GuardianBadge } from '../components/ui/StatusBadge';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

const TYPE_LABELS: Record<string, string> = {
  PAYMENT_FAILURE: 'Payment Failure',
  CHECKOUT_ABANDONMENT: 'Checkout Abandonment',
  OVERDUE_RECEIVABLE: 'Overdue Invoice',
  SUBSCRIPTION_FAILURE: 'Subscription Failure',
  PROMISE_TO_PAY_BROKEN: 'Promise Broken',
};

export function ApprovalQueue() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, string>>({});

  const fetchEscalated = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await recoveryCasesApi.getCases({ status: 'ESCALATED', limit: 200 });
      setCases(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e.message || 'Failed to load approval queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchEscalated(); }, [fetchEscalated]);

  const handleAction = async (caseId: string, action: 'approve' | 'reject') => {
    setActionLoading(prev => ({ ...prev, [caseId]: action }));
    try {
      if (action === 'approve') {
        await recoveryCasesApi.approve(caseId, 'HUMAN_AGENT', 'Approved via approval queue');
      } else {
        await recoveryCasesApi.reject(caseId, 'HUMAN_AGENT', 'Rejected via approval queue');
      }
      await fetchEscalated();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(prev => {
        const next = { ...prev };
        delete next[caseId];
        return next;
      });
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight flex items-center gap-3">
            <CheckSquare className="w-7 h-7 text-[#F59E0B]" />
            Human Approval Queue
          </h1>
          <p className="text-[#4B5563] text-sm font-medium mt-1">
            Cases flagged by the Policy Guardian requiring human oversight (high-value transactions, low AI confidence, large discounts).
          </p>
        </div>
        <button
          onClick={fetchEscalated}
          className="flex items-center gap-2 px-3.5 py-2 bg-white hover:bg-[#F3F4F6] text-[#4B5563] hover:text-[#0B132B] border border-[#E5E7EB] rounded-xl text-xs font-semibold shadow-xs transition-all w-fit"
        >
          <RefreshCw className="w-4 h-4 text-[#6366F1]" /> Refresh Queue
        </button>
      </div>

      {/* Policy Reminder Banner */}
      <div className="premium-card p-5 border-[#FDE68A] bg-[#FFFBEB]/60">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 bg-[#FEF3C7] rounded-xl flex items-center justify-center shrink-0 border border-[#FDE68A]">
            <User className="w-5 h-5 text-[#D97706]" />
          </div>
          <div>
            <p className="text-[#92400E] text-sm font-bold">Compliance Checkpoint (Human-in-the-Loop)</p>
            <p className="text-[#78350F] text-xs font-medium mt-0.5 leading-relaxed">
              Autonomous execution is halted for safety whenever transactions exceed ₹1,00,000 or AI confidence dips below 60%.
              Every approved action is logged with human agent ID in the audit trail.
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-48 bg-white rounded-2xl border border-[#E5E7EB]">
          <Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" />
        </div>
      ) : error ? (
        <div className="bg-white rounded-2xl p-8 text-center border border-[#FECACA]">
          <AlertCircle className="w-10 h-10 text-[#EF4444] mx-auto mb-3" />
          <p className="text-[#DC2626] text-sm font-semibold">{error}</p>
          <button onClick={fetchEscalated} className="mt-3 px-4 py-2 bg-[#6366F1] text-white rounded-xl text-xs font-bold">Retry</button>
        </div>
      ) : cases.length === 0 ? (
        <div className="bg-white rounded-2xl p-16 text-center border border-[#E5E7EB] shadow-xs">
          <CheckCircle className="w-12 h-12 text-[#10B981] mx-auto mb-4" />
          <h3 className="text-[#0B132B] font-bold text-lg mb-1">Queue is Clear</h3>
          <p className="text-[#4B5563] text-sm font-medium">No cases currently require human intervention.</p>
          <p className="text-[#9CA3AF] text-xs mt-2 font-medium">Run Demo Scenario 4 or a batch to generate high-value escalation cases.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-[#4B5563] text-xs font-bold uppercase tracking-wider">
            {cases.length} case{cases.length !== 1 ? 's' : ''} awaiting human decision
          </p>
          {cases.map((c) => (
            <div
              key={c.id}
              className="premium-card p-6 border-[#FDE68A] hover:border-[#F59E0B] transition-all animate-fade-in-up"
            >
              <div className="flex items-start justify-between gap-5 flex-wrap">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-3 flex-wrap">
                    <Link
                      to={`/cases/${c.case_id}`}
                      className="text-[#0B132B] font-extrabold font-mono hover:text-[#6366F1] transition-colors text-base"
                    >
                      {c.case_id}
                    </Link>
                    <StatusBadge status={c.status} />
                    {c.risk_level && <StatusBadge status={c.risk_level} />}
                    {c.guardian_status && <GuardianBadge decision={c.guardian_status} />}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3.5 bg-[#F9FAFB] p-3.5 rounded-xl border border-[#E5E7EB]">
                    <div>
                      <p className="text-[#6B7280] text-xs font-medium">Case Type</p>
                      <p className="text-[#0B132B] text-xs font-bold mt-0.5">{TYPE_LABELS[c.case_type] || c.case_type}</p>
                    </div>
                    <div>
                      <p className="text-[#6B7280] text-xs font-medium">Amount at Risk</p>
                      <p className="text-[#D97706] text-xs font-extrabold mt-0.5">{INR(c.amount_at_risk || 0)}</p>
                    </div>
                    <div>
                      <p className="text-[#6B7280] text-xs font-medium">Merchant ID</p>
                      <p className="text-[#0B132B] text-xs font-mono font-bold mt-0.5">{c.merchant_id}</p>
                    </div>
                    <div>
                      <p className="text-[#6B7280] text-xs font-medium">AI Confidence</p>
                      <p className={`text-xs font-bold mt-0.5 ${(c.confidence || 0) < 0.6 ? 'text-[#DC2626]' : 'text-[#4F46E5]'}`}>
                        {c.confidence != null ? `${(c.confidence * 100).toFixed(0)}%` : '—'}
                      </p>
                    </div>
                  </div>

                  {c.guardian_reason && (
                    <div className="bg-[#FFFBEB] border border-[#FDE68A] rounded-xl p-3 mb-3">
                      <p className="text-xs text-[#92400E] font-bold uppercase tracking-wider mb-0.5">Policy Guardian Reason</p>
                      <p className="text-xs text-[#78350F] font-medium leading-relaxed">{c.guardian_reason}</p>
                    </div>
                  )}

                  {c.recommended_strategy && (
                    <p className="text-xs text-[#4B5563] font-medium">
                      Proposed Recovery Action: <span className="text-[#0B132B] font-bold font-mono px-2 py-0.5 bg-[#F3F4F6] rounded-md">{c.recommended_strategy}</span>
                    </p>
                  )}
                </div>

                {/* Decision Actions */}
                <div className="flex flex-col gap-2.5 shrink-0 w-full sm:w-auto">
                  <button
                    onClick={() => handleAction(c.case_id, 'approve')}
                    disabled={!!actionLoading[c.case_id]}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[#10B981] hover:bg-[#059669] text-white rounded-xl text-sm font-bold shadow-sm shadow-[#10B981]/25 transition-all disabled:opacity-50"
                  >
                    {actionLoading[c.case_id] === 'approve'
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <CheckCircle className="w-4 h-4" />}
                    Approve Action
                  </button>
                  <button
                    onClick={() => handleAction(c.case_id, 'reject')}
                    disabled={!!actionLoading[c.case_id]}
                    className="flex items-center justify-center gap-2 px-5 py-2.5 bg-[#F3F4F6] hover:bg-[#FEE2E2] text-[#4B5563] hover:text-[#DC2626] border border-[#E5E7EB] rounded-xl text-sm font-bold transition-all disabled:opacity-50"
                  >
                    {actionLoading[c.case_id] === 'reject'
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <XCircle className="w-4 h-4" />}
                    Reject Case
                  </button>
                  <Link
                    to={`/cases/${c.case_id}`}
                    className="flex items-center justify-center gap-1 text-xs font-bold text-[#6366F1] hover:text-[#4F46E5] transition-colors mt-1"
                  >
                    Inspect Full Details <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
