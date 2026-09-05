import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Loader2, AlertCircle, Shield, Zap, CheckCircle, CheckCircle2, AlertTriangle,
  XCircle, Clock, TrendingUp, DollarSign, ChevronDown, ChevronUp, FileText, Play,
  ShieldCheck
} from 'lucide-react';
import { recoveryCasesApi } from '../api/recoveryCasesApi';
import { RecoveryCase, CaseAuditEvent, Strategy, GuardianDecision } from '../types';
import { StatusBadge, GuardianBadge } from '../components/ui/StatusBadge';
import { ActionReceiptModal } from '../components/ui/ActionReceiptModal';
import { RecoveryReplayModal } from '../components/ui/RecoveryReplayModal';
import { useRecoveryStream } from '../hooks/useRecoveryStream';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

const TYPE_LABELS: Record<string, string> = {
  PAYMENT_FAILURE: 'Payment Failure',
  CHECKOUT_ABANDONMENT: 'Checkout Abandonment',
  OVERDUE_RECEIVABLE: 'Overdue Invoice',
  SUBSCRIPTION_FAILURE: 'Subscription Failure',
  PROMISE_TO_PAY_BROKEN: 'Promise Broken',
};

const EVENT_ICONS: Record<string, any> = {
  STATE_TRANSITION: Zap,
  ESCALATION: AlertCircle,
  GUARDIAN_DECISION: Shield,
  default: Clock,
};

export function CaseDetail() {
  const { caseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();

  const [caseData, setCaseData] = useState<RecoveryCase | null>(null);
  const [audit, setAudit] = useState<CaseAuditEvent[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [guardianDecisions, setGuardianDecisions] = useState<GuardianDecision[]>([]);
  const [receiptData, setReceiptData] = useState<any>(null);
  const [isReceiptOpen, setIsReceiptOpen] = useState(false);
  const [isReplayOpen, setIsReplayOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showFullAudit, setShowFullAudit] = useState(false);
  const [chainVerifyResult, setChainVerifyResult] = useState<any>(null);
  const [verifyingChain, setVerifyingChain] = useState(false);

  const load = useCallback(async () => {
    if (!caseId) return;
    try {
      setLoading(true);
      setError(null);
      const [c, a, s, g] = await Promise.allSettled([
        recoveryCasesApi.getCaseById(caseId),
        recoveryCasesApi.getCaseAudit(caseId),
        recoveryCasesApi.getCaseStrategies(caseId),
        recoveryCasesApi.getGuardianDecisions(caseId),
      ]);
      if (c.status === 'fulfilled') setCaseData(c.value);
      else throw new Error('Case not found');
      if (a.status === 'fulfilled') setAudit(Array.isArray(a.value) ? a.value : []);
      if (s.status === 'fulfilled') setStrategies(Array.isArray(s.value) ? s.value : []);
      if (g.status === 'fulfilled') setGuardianDecisions(Array.isArray(g.value) ? g.value : []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  // Connect to live SSE stream for real-time state changes
  useRecoveryStream(
    useCallback((event: any) => {
      if (event.data?.case_id === caseId) {
        load();
      }
    }, [caseId, load])
  );

  useEffect(() => { load(); }, [load]);

  const verifyChain = async () => {
    if (!caseId) return;
    setVerifyingChain(true);
    try {
      const res = await recoveryCasesApi.verifyAuditChain(caseId);
      setChainVerifyResult(res);
    } catch (e: any) {
      alert(e.message || 'Failed to verify chain');
    } finally {
      setVerifyingChain(false);
    }
  };

  const runAction = async (action: string) => {
    if (!caseId) return;
    setActionLoading(action);
    try {
      if (action === 'run') await recoveryCasesApi.runFullWorkflow(caseId);
      else if (action === 'analyze') await recoveryCasesApi.analyze(caseId);
      else if (action === 'simulate') await recoveryCasesApi.simulate(caseId);
      else if (action === 'guardian') await recoveryCasesApi.guardianCheck(caseId);
      else if (action === 'execute') await recoveryCasesApi.execute(caseId);
      else if (action === 'verify') await recoveryCasesApi.verify(caseId);
      await load();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setActionLoading(null);
    }
  };

  const openReceipt = async () => {
    if (!caseId) return;
    try {
      const data = await recoveryCasesApi.getCaseReceipt(caseId);
      setReceiptData(data);
      setIsReceiptOpen(true);
    } catch (e: any) {
      alert(e.message || 'Failed to fetch receipt');
    }
  };

  const handleApprove = async () => {
    if (!caseId) return;
    setActionLoading('approve');
    try {
      await recoveryCasesApi.approve(caseId, 'HUMAN_AGENT', 'Manually approved via UI');
      try {
        await recoveryCasesApi.execute(caseId);
        await recoveryCasesApi.verify(caseId);
      } catch {}
      await load();
    } catch (e: any) { alert(e.message); }
    finally { setActionLoading(null); }
  };

  const handleReject = async () => {
    if (!caseId) return;
    setActionLoading('reject');
    try {
      await recoveryCasesApi.reject(caseId, 'HUMAN_AGENT', 'Manually rejected via UI');
      await load();
    } catch (e: any) { alert(e.message); }
    finally { setActionLoading(null); }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64"><Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" /></div>
  );

  if (error || !caseData) return (
    <div className="max-w-4xl mx-auto px-4 py-16 text-center">
      <AlertCircle className="w-12 h-12 text-[#EF4444] mx-auto mb-3" />
      <p className="text-[#0B132B] font-bold">{error || 'Case not found'}</p>
      <button onClick={() => navigate('/cases')} className="mt-4 px-4 py-2 bg-[#6366F1] text-white rounded-xl text-xs font-semibold">← Back to Cases</button>
    </div>
  );

  const isEscalated = caseData.status === 'ESCALATED';
  const auditToShow = showFullAudit ? audit : audit.slice(-8);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      <ActionReceiptModal
        receipt={receiptData}
        isOpen={isReceiptOpen}
        onClose={() => setIsReceiptOpen(false)}
      />

      <RecoveryReplayModal
        isOpen={isReplayOpen}
        onClose={() => setIsReplayOpen(false)}
        caseId={caseData.case_id}
        auditEvents={audit}
      />

      {/* Back & Header */}
      <div>
        <Link to="/cases" className="inline-flex items-center gap-1.5 text-[#4B5563] hover:text-[#0B132B] text-sm font-semibold mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Cases
        </Link>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-3xl font-extrabold text-[#0B132B] font-mono tracking-tight">{caseData.case_id}</h1>
              <StatusBadge status={caseData.status} size="md" />
            </div>
            <p className="text-[#4B5563] text-sm font-medium">
              {TYPE_LABELS[caseData.case_type] || caseData.case_type} •
              <span className="ml-1 text-[#6B7280]">Created {new Date(caseData.created_at).toLocaleString('en-IN')}</span>
            </p>
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              onClick={() => setIsReplayOpen(true)}
              className="flex items-center gap-1.5 px-3.5 py-2.5 bg-[#EEF2FF] border border-[#C7D2FE] hover:bg-[#E0E7FF] text-[#4F46E5] rounded-xl text-xs font-bold shadow-2xs transition-all"
            >
              <Play className="w-3.5 h-3.5" />
              Replay Event Lifecycle
            </button>

            <button
              onClick={openReceipt}
              className="flex items-center gap-1.5 px-4 py-2.5 bg-white border border-[#E5E7EB] hover:bg-[#F9FAFB] text-[#0B132B] rounded-xl text-xs font-bold shadow-2xs transition-all"
            >
              <FileText className="w-4 h-4 text-[#6366F1]" />
              AI Action Receipt & Policy Record
            </button>

            {/* Human approval buttons */}
            {isEscalated && (
              <div className="flex gap-2">
                <button
                  onClick={handleApprove}
                  disabled={!!actionLoading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#10B981] hover:bg-[#059669] text-white rounded-xl text-sm font-bold shadow-md shadow-[#10B981]/20 transition-all disabled:opacity-50"
                >
                  {actionLoading === 'approve' ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  Approve Action
                </button>
                <button
                  onClick={handleReject}
                  disabled={!!actionLoading}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#EF4444] hover:bg-[#DC2626] text-white rounded-xl text-sm font-bold shadow-md shadow-[#EF4444]/20 transition-all disabled:opacity-50"
                >
                  {actionLoading === 'reject' ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                  Reject Case
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Action Triggers */}
      {isEscalated ? (
        <div className="p-4 bg-[#FEF3C7] border border-[#FCD34D] rounded-2xl flex items-center justify-between flex-wrap gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-[#D97706] shrink-0" />
            <div>
              <h4 className="text-xs font-extrabold text-[#92400E] uppercase tracking-wider">Human Approval Required</h4>
              <p className="text-xs text-[#B45309] mt-0.5 font-medium">
                {caseData.guardian_reason || "Policy Guardian flagged this case for human review before execution."}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleApprove}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#10B981] hover:bg-[#059669] text-white rounded-xl text-xs font-bold shadow-xs transition-all disabled:opacity-50"
            >
              {actionLoading === 'approve' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
              Approve & Execute Action
            </button>
            <button
              onClick={handleReject}
              disabled={!!actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#EF4444] hover:bg-[#DC2626] text-white rounded-xl text-xs font-bold shadow-xs transition-all disabled:opacity-50"
            >
              {actionLoading === 'reject' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <XCircle className="w-3.5 h-3.5" />}
              Reject
            </button>
          </div>
        </div>
      ) : caseData.status !== 'CLOSED' && caseData.status !== 'RECOVERED' ? (
        <div className="flex flex-wrap gap-2.5 p-3 bg-white border border-[#E5E7EB] rounded-2xl shadow-xs">
          {[
            { key: 'run', label: '⚡ Run Full Workflow Loop', color: 'bg-[#10B981] hover:bg-[#059669] text-white' },
            { key: 'analyze', label: '1. Diagnose Root Cause', color: 'bg-[#F3F4F6] hover:bg-[#E5E7EB] text-[#0B132B]' },
            { key: 'simulate', label: '2. Simulate Strategies', color: 'bg-[#F3F4F6] hover:bg-[#E5E7EB] text-[#0B132B]' },
            { key: 'guardian', label: '3. Guardian Check', color: 'bg-[#EEF2FF] hover:bg-[#E0E7FF] text-[#4F46E5] border border-[#C7D2FE]' },
            { key: 'execute', label: '4. Execute Action', color: 'bg-[#F3F4F6] hover:bg-[#E5E7EB] text-[#0B132B]' },
            { key: 'verify', label: '5. Verify Payment', color: 'bg-[#F3F4F6] hover:bg-[#E5E7EB] text-[#0B132B]' },
          ].map(({ key, label, color }) => (
            <button
              key={key}
              onClick={() => runAction(key)}
              disabled={!!actionLoading}
              className={`flex items-center gap-1.5 px-3.5 py-2 ${color} rounded-xl text-xs font-bold transition-all disabled:opacity-50 shadow-2xs`}
            >
              {actionLoading === key ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
              {label}
            </button>
          ))}
        </div>
      ) : (
        <div className="p-3.5 bg-[#10B981]/10 border border-[#10B981]/20 rounded-2xl flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-[#065F46]">
            <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
            Recovery Workflow Completed — Case is Closed & Reconciled
          </div>
          <button
            onClick={openReceipt}
            className="px-3 py-1 bg-white border border-[#10B981]/30 hover:bg-[#10B981]/10 text-[#065F46] rounded-xl text-xs font-bold transition-all shadow-2xs"
          >
            View Cryptographic Receipt
          </button>
        </div>
      )}

      {/* Case Summary + Financial Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Core Info */}
        <div className="premium-card p-6">
          <h2 className="text-[#0B132B] text-sm font-bold uppercase tracking-wider mb-4 pb-2 border-b border-[#F3F4F6]">
            Case Metadata
          </h2>
          <dl className="space-y-3.5 text-sm">
            {[
              ['Case Type', TYPE_LABELS[caseData.case_type] || caseData.case_type],
              ['Merchant ID', caseData.merchant_id],
              ['Customer ID', caseData.customer_id],
              ['Currency', caseData.currency || 'INR'],
              ['Risk Level', caseData.risk_level || '—'],
              ['Priority', caseData.priority || '—'],
              ['Retry Count', caseData.retry_count ?? 0],
              ['Message Count', caseData.message_count ?? 0],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between items-center py-1 border-b border-[#F9FAFB] last:border-0">
                <dt className="text-[#4B5563] font-medium">{k}</dt>
                <dd className="text-[#0B132B] font-semibold text-right max-w-[60%] truncate font-mono text-xs">{String(v)}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Financial & AI Diagnosis Info */}
        <div className="premium-card p-6">
          <h2 className="text-[#0B132B] text-sm font-bold uppercase tracking-wider mb-4 pb-2 border-b border-[#F3F4F6]">
            Financial & Root Cause
          </h2>
          <div className="space-y-4">
            <div className="flex items-center gap-3.5 p-4 bg-[#FFFBEB] border border-[#FDE68A] rounded-xl">
              <DollarSign className="w-6 h-6 text-[#F59E0B] shrink-0" />
              <div>
                <p className="text-xs text-[#B45309] font-bold uppercase tracking-wider">Revenue at Risk</p>
                <p className="text-2xl font-black text-[#0B132B]">{INR(caseData.amount_at_risk || 0)}</p>
              </div>
            </div>
            <div className={`flex items-center gap-3.5 p-4 border rounded-xl ${caseData.recovered_amount ? 'bg-[#ECFDF5] border-[#A7F3D0]' : 'bg-[#F9FAFB] border-[#E5E7EB]'}`}>
              <TrendingUp className={`w-6 h-6 shrink-0 ${caseData.recovered_amount ? 'text-[#10B981]' : 'text-[#9CA3AF]'}`} />
              <div>
                <p className={`text-xs font-bold uppercase tracking-wider ${caseData.recovered_amount ? 'text-[#047857]' : 'text-[#6B7280]'}`}>
                  Money Recovered
                </p>
                <p className={`text-2xl font-black ${caseData.recovered_amount ? 'text-[#059669]' : 'text-[#9CA3AF]'}`}>
                  {caseData.recovered_amount ? INR(caseData.recovered_amount) : '—'}
                </p>
              </div>
            </div>
            {caseData.root_cause && (
              <div className="p-4 bg-[#EEF2FF] border border-[#C7D2FE] rounded-xl">
                <p className="text-xs text-[#4338CA] font-bold uppercase tracking-wider mb-1">AI Root Cause Diagnosis</p>
                <p className="text-sm font-bold text-[#0B132B]">{caseData.root_cause}</p>
                {caseData.confidence != null && (
                  <p className="text-xs text-[#4B5563] mt-1.5 font-medium">
                    AI Confidence: <span className="text-[#4F46E5] font-bold">{(caseData.confidence * 100).toFixed(0)}%</span>
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Strategies Evaluated */}
      {strategies.length > 0 && (
        <div className="premium-card p-6">
          <h2 className="text-[#0B132B] font-bold text-base mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-[#6366F1]" />
            Counterfactual Strategies Evaluated ({strategies.length})
          </h2>
          <div className="space-y-3">
            {strategies.map((s, i) => (
              <div
                key={s.id}
                className={`p-4.5 rounded-xl border transition-all ${
                  s.is_selected === 'YES'
                    ? 'border-[#10B981] bg-[#ECFDF5]/60 shadow-xs'
                    : 'border-[#E5E7EB] bg-[#F9FAFB]'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-black ${
                      s.rank === 1 ? 'bg-[#10B981] text-white shadow-xs' : 'bg-[#E5E7EB] text-[#4B5563]'
                    }`}>
                      #{s.rank || i + 1}
                    </span>
                    <div>
                      <p className="text-[#0B132B] text-sm font-bold">{s.strategy_label || s.strategy_name}</p>
                      {s.description && <p className="text-[#4B5563] text-xs mt-0.5 font-medium">{s.description}</p>}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    {s.recovery_probability != null && (
                      <p className="text-sm font-black text-[#059669]">{(s.recovery_probability * 100).toFixed(0)}% success</p>
                    )}
                    {s.expected_net_recovery != null && (
                      <p className="text-xs text-[#4B5563] font-semibold mt-0.5">Net: {INR(s.expected_net_recovery)}</p>
                    )}
                    {s.is_selected === 'YES' && (
                      <span className="inline-block mt-1 text-[11px] font-extrabold text-[#047857] bg-[#D1FAE5] px-2 py-0.5 rounded-full border border-[#A7F3D0]">
                        ✓ SELECTED STRATEGY
                      </span>
                    )}
                  </div>
                </div>
                {s.ai_explanation && (
                  <p className="text-xs text-[#4B5563] mt-2.5 pl-10 italic border-l-2 border-[#10B981]/30 ml-2">"{s.ai_explanation}"</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Guardian Decisions */}
      {guardianDecisions.length > 0 && (
        <div className="premium-card p-6">
          <h2 className="text-[#0B132B] font-bold text-base mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#6366F1]" />
            Policy Guardian Decisions ({guardianDecisions.length})
          </h2>
          <div className="space-y-3">
            {guardianDecisions.map(d => (
              <div key={d.id} className={`p-4.5 rounded-xl border ${
                d.decision === 'APPROVED' ? 'border-[#A7F3D0] bg-[#ECFDF5]' :
                d.decision === 'BLOCKED' ? 'border-[#FECACA] bg-[#FEF2F2]' :
                'border-[#FDE68A] bg-[#FFFBEB]'
              }`}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <p className="text-sm text-[#0B132B] font-bold">
                      Action: <span className="font-mono text-xs px-2 py-0.5 bg-white rounded-md border border-[#E5E7EB]">{d.proposed_action}</span>
                    </p>
                    <p className="text-xs text-[#6B7280] font-medium mt-1">
                      {new Date(d.created_at).toLocaleString('en-IN')} • Verified by {d.decided_by}
                      {d.human_approver && ` (${d.human_approver})`}
                    </p>
                  </div>
                  <GuardianBadge decision={d.decision} />
                </div>
                {d.reason && <p className="text-xs text-[#4B5563] font-medium mt-2">{d.reason}</p>}
                {d.checks_passed && d.checks_passed.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {d.checks_passed.map(check => (
                      <span key={check} className="text-[10px] font-bold px-2.5 py-0.5 bg-white text-[#059669] rounded-md border border-[#A7F3D0] shadow-2xs">
                        ✓ {check}
                      </span>
                    ))}
                  </div>
                )}
                {d.checks_failed && d.checks_failed.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {d.checks_failed.map(check => (
                      <span key={check} className="text-[10px] font-bold px-2.5 py-0.5 bg-white text-[#DC2626] rounded-md border border-[#FECACA] shadow-2xs">
                        ✕ {check}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stop Reason Alert */}
      {caseData.stop_reason && (
        <div className="p-5 bg-[#FEF2F2] border border-[#FECACA] rounded-2xl">
          <h2 className="text-[#DC2626] font-bold text-sm mb-1 flex items-center gap-2">
            <XCircle className="w-4 h-4" /> Automation Stopped
          </h2>
          <p className="text-[#4B5563] text-sm font-medium">{caseData.stop_reason}</p>
        </div>
      )}

      {/* Audit Timeline */}
      <div className="premium-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-4 border-b border-[#F3F4F6]">
          <h2 className="text-[#0B132B] font-bold text-base flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#6366F1]" />
            Immutable Audit Timeline ({audit.length} events)
          </h2>
          <button
            onClick={verifyChain}
            disabled={verifyingChain}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#EEF2FF] hover:bg-[#E0E7FF] text-[#4F46E5] rounded-xl text-xs font-bold border border-[#C7D2FE] transition-all disabled:opacity-50 w-fit"
          >
            {verifyingChain ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ShieldCheck className="w-3.5 h-3.5" />}
            Verify Cryptographic Chain (SHA-256)
          </button>
        </div>

        {/* Cryptographic Chain Status Panel */}
        {chainVerifyResult && (
          <div className={`p-4 rounded-xl mb-5 border animate-fade-in ${
            chainVerifyResult.is_valid ? 'bg-[#ECFDF5] border-[#A7F3D0]' : 'bg-[#FEF2F2] border-[#FECACA]'
          }`}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className={`w-5 h-5 ${chainVerifyResult.is_valid ? 'text-[#059669]' : 'text-[#DC2626]'}`} />
                <div>
                  <p className="text-xs font-extrabold text-[#0B132B] uppercase tracking-wider">
                    {chainVerifyResult.is_valid ? 'Cryptographic Chain Verified Valid' : 'Tamper Detected in Hash Chain'}
                  </p>
                  <p className="text-xs text-[#4B5563] mt-0.5">{chainVerifyResult.message}</p>
                </div>
              </div>
              <span className={`px-2 py-0.5 text-[10px] font-black rounded-md ${
                chainVerifyResult.is_valid ? 'bg-[#10B981] text-white' : 'bg-[#EF4444] text-white'
              }`}>
                {chainVerifyResult.status}
              </span>
            </div>
            {chainVerifyResult.latest_block_hash && (
              <div className="mt-2.5 pt-2 border-t border-black/5 font-mono text-[10px] text-[#6B7280] break-all">
                <span className="font-bold text-[#0B132B]">Chain Head SHA-256: </span>
                {chainVerifyResult.latest_block_hash}
              </div>
            )}
          </div>
        )}
        {audit.length === 0 ? (
          <p className="text-[#6B7280] text-sm">No audit events recorded yet.</p>
        ) : (
          <div className="relative">
            <div className="space-y-0">
              {auditToShow.map((ev, i) => {
                const Icon = EVENT_ICONS[ev.event_type] || EVENT_ICONS.default;
                return (
                  <div key={ev.id} className={`flex gap-4 ${i < auditToShow.length - 1 ? 'pb-5' : ''}`}>
                    <div className="flex flex-col items-center">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 shadow-2xs ${
                        ev.new_state === 'CLOSED' || ev.new_state === 'RECOVERED' ? 'bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]' :
                        ev.new_state === 'BLOCKED' || ev.new_state === 'FAILED' ? 'bg-[#FEF2F2] text-[#DC2626] border border-[#FECACA]' :
                        ev.new_state === 'ESCALATED' ? 'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]' :
                        'bg-[#F3F4F6] text-[#4B5563] border border-[#E5E7EB]'
                      }`}>
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      {i < auditToShow.length - 1 && <div className="w-0.5 flex-1 bg-[#E5E7EB] mt-1" />}
                    </div>
                    <div className="pb-1 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-semibold text-[#6B7280]">{new Date(ev.created_at).toLocaleTimeString('en-IN')}</span>
                        <span className="text-xs font-bold text-[#0B132B]">{ev.event_type}</span>
                        {ev.previous_state && (
                          <>
                            <StatusBadge status={ev.previous_state} />
                            <span className="text-[#9CA3AF] text-xs">→</span>
                          </>
                        )}
                        <StatusBadge status={ev.new_state} />
                      </div>
                      {ev.reason && <p className="text-xs text-[#4B5563] font-medium mt-1">{ev.reason}</p>}
                      <p className="text-[10px] text-[#9CA3AF] font-mono mt-0.5">{ev.actor_type} / {ev.actor_id}</p>
                    </div>
                  </div>
                );
              })}
            </div>
            {audit.length > 8 && (
              <button
                onClick={() => setShowFullAudit(!showFullAudit)}
                className="mt-4 flex items-center gap-1 text-xs font-bold text-[#6366F1] hover:text-[#4F46E5] transition-colors"
              >
                {showFullAudit ? <><ChevronUp className="w-4 h-4" /> Show fewer</> : <><ChevronDown className="w-4 h-4" /> Show all {audit.length} events</>}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
