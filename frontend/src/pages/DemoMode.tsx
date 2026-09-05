import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PlayCircle, Loader2, CheckCircle, XCircle, AlertTriangle, ArrowRight, Shield, Zap } from 'lucide-react';
import { demoApi } from '../api/demoApi';
import { DemoResult } from '../types';

const SCENARIOS = [
  {
    id: 1,
    title: 'Successful Payment Recovery',
    subtitle: '₹30,000 payment failure → full recovery loop → RECOVERED',
    icon: '💳',
    tagColor: 'text-[#059669] bg-[#ECFDF5] border-[#A7F3D0]',
    tag: 'SUCCESS PATH',
  },
  {
    id: 2,
    title: 'Checkout Abandonment',
    subtitle: '₹7,500 abandoned cart → recovery link sent after guardian check',
    icon: '🛒',
    tagColor: 'text-[#D97706] bg-[#FEF3C7] border-[#FDE68A]',
    tag: 'ABANDONMENT',
  },
  {
    id: 3,
    title: 'Guardian Blocks Unsafe Action',
    subtitle: 'AI proposes retry → Guardian BLOCKS (max retries 2/2 reached)',
    icon: '🛡️',
    tagColor: 'text-[#DC2626] bg-[#FEF2F2] border-[#FECACA]',
    tag: 'GUARDIAN BLOCK',
  },
  {
    id: 4,
    title: 'Overdue Invoice → Human Escalation',
    subtitle: '₹2,50,000 invoice 25 days overdue → high-value approval required',
    icon: '📄',
    tagColor: 'text-[#B45309] bg-[#FEF3C7] border-[#FCD34D]',
    tag: 'ESCALATION',
  },
  {
    id: 5,
    title: 'Promise-to-Pay Broken',
    subtitle: 'Customer promised ₹50,000 but did not pay → recovery triggered',
    icon: '🤝',
    tagColor: 'text-[#7C3AED] bg-[#F5F3FF] border-[#DDD6FE]',
    tag: 'PROMISE BROKEN',
  },
  {
    id: 6,
    title: 'AI Timeout → Safe Fallback',
    subtitle: 'AI returns low confidence → safe fallback → zero unsafe action',
    icon: '🤖',
    tagColor: 'text-[#4F46E5] bg-[#EEF2FF] border-[#C7D2FE]',
    tag: 'SAFE FALLBACK',
  },
];

function ResultCard({ result }: { result: DemoResult }) {
  const isSuccess = result.final_status === 'CLOSED' || result.final_status === 'RECOVERED';
  const isBlocked = result.guardian_decision === 'BLOCKED' || result.final_status === 'BLOCKED';
  const isEscalated = result.final_status === 'ESCALATED' || result.guardian_decision === 'HUMAN_APPROVAL_REQUIRED';

  const statusColor = isSuccess ? 'border-[#A7F3D0] bg-[#ECFDF5]/60' :
    isBlocked ? 'border-[#FECACA] bg-[#FEF2F2]/60' :
    isEscalated ? 'border-[#FDE68A] bg-[#FFFBEB]/60' :
    'border-[#C7D2FE] bg-[#EEF2FF]/60';

  return (
    <div className={`rounded-2xl border p-5.5 animate-fade-in-up ${statusColor} shadow-xs`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-[#0B132B] font-bold text-sm">{result.title}</h3>
          <p className="text-[#4B5563] text-xs font-medium mt-0.5">{result.description}</p>
        </div>
        {isSuccess ? <CheckCircle className="w-6 h-6 text-[#10B981] shrink-0" /> :
         isBlocked ? <XCircle className="w-6 h-6 text-[#EF4444] shrink-0" /> :
         isEscalated ? <AlertTriangle className="w-6 h-6 text-[#F59E0B] shrink-0" /> :
         <Zap className="w-6 h-6 text-[#6366F1] shrink-0" />}
      </div>

      {/* Demonstration Flow */}
      <div className="bg-white rounded-xl p-3 mb-3 border border-[#E5E7EB] shadow-2xs">
        <p className="text-xs font-mono font-semibold text-[#0B132B] leading-relaxed">{result.demonstration}</p>
      </div>

      {/* Key Stats */}
      <div className="grid grid-cols-2 gap-3 text-xs mb-3">
        {result.final_status && (
          <div className="bg-white rounded-xl p-2.5 border border-[#E5E7EB] shadow-2xs">
            <p className="text-[#6B7280] font-medium">Final Status</p>
            <p className="text-[#0B132B] font-bold mt-0.5">{result.final_status}</p>
          </div>
        )}
        {result.recovered_amount !== undefined && (
          <div className="bg-white rounded-xl p-2.5 border border-[#E5E7EB] shadow-2xs">
            <p className="text-[#6B7280] font-medium">Money Recovered</p>
            <p className={`font-bold mt-0.5 ${result.recovered_amount > 0 ? 'text-[#059669]' : 'text-[#6B7280]'}`}>
              {result.recovered_amount > 0
                ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(result.recovered_amount)
                : '—'}
            </p>
          </div>
        )}
        {result.guardian_decision && (
          <div className="bg-white rounded-xl p-2.5 border border-[#E5E7EB] shadow-2xs">
            <p className="text-[#6B7280] font-medium">Guardian Decision</p>
            <p className={`font-bold mt-0.5 ${
              result.guardian_decision === 'APPROVED' ? 'text-[#059669]' :
              result.guardian_decision === 'BLOCKED' ? 'text-[#DC2626]' : 'text-[#D97706]'
            }`}>{result.guardian_decision}</p>
          </div>
        )}
        {result.ai_confidence !== undefined && (
          <div className="bg-white rounded-xl p-2.5 border border-[#E5E7EB] shadow-2xs">
            <p className="text-[#6B7280] font-medium">AI Confidence</p>
            <p className={`font-bold mt-0.5 ${(result.ai_confidence || 0) < 0.6 ? 'text-[#DC2626]' : 'text-[#4F46E5]'}`}>
              {((result.ai_confidence || 0) * 100).toFixed(0)}%
            </p>
          </div>
        )}
        {result.unsafe_action_executed === false && (
          <div className="bg-white rounded-xl p-2.5 border border-[#E5E7EB] shadow-2xs col-span-2">
            <p className="text-[#6B7280] font-medium">Safety Verification</p>
            <p className="text-[#059669] font-bold mt-0.5">✓ ZERO Unsafe Actions Executed (Safe Fallback)</p>
          </div>
        )}
      </div>

      {/* Steps */}
      {result.steps && result.steps.length > 0 && (
        <div className="mt-3">
          <p className="text-xs text-[#6B7280] font-bold mb-2">Workflow Progression:</p>
          <div className="flex flex-wrap gap-1.5">
            {result.steps.map((s, i) => (
              <span key={i} className="text-[11px] font-semibold px-2.5 py-0.5 bg-white border border-[#E5E7EB] rounded-full text-[#4B5563] shadow-2xs">
                {i + 1}. {s.step}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Link to case */}
      {result.case_id && (
        <Link
          to={`/cases/${result.case_id}`}
          className="mt-3.5 inline-flex items-center gap-1.5 text-xs font-bold text-[#6366F1] hover:text-[#4F46E5] transition-colors"
        >
          View Case Details ({result.case_id}) <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      )}
    </div>
  );
}

export function DemoMode() {
  const [results, setResults] = useState<Record<number, DemoResult | null>>({});
  const [loading, setLoading] = useState<Record<number, boolean>>({});
  const [runningAll, setRunningAll] = useState(false);

  const runScenario = async (id: number) => {
    setLoading(prev => ({ ...prev, [id]: true }));
    try {
      const data = await demoApi.runScenario(id);
      setResults(prev => ({ ...prev, [id]: data }));
    } catch (e: any) {
      alert(`Scenario ${id} failed: ${e.message}`);
    } finally {
      setLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const runAll = async () => {
    setRunningAll(true);
    for (let i = 1; i <= 6; i++) {
      await runScenario(i);
    }
    setRunningAll(false);
  };

  const completedCount = Object.keys(results).length;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto">
        <div className="w-14 h-14 bg-gradient-to-br from-[#6366F1] to-[#4F46E5] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-[#6366F1]/20">
          <PlayCircle className="w-7 h-7 text-white" />
        </div>
        <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight mb-2">Interactive Demo Mode</h1>
        <p className="text-[#4B5563] text-sm font-medium leading-relaxed">
          Run realistic end-to-end recovery scenarios. Experience how RecoveryPilot detects risk, diagnoses causes, consults the Policy Guardian, and guarantees safe execution.
        </p>
        <div className="flex items-center justify-center gap-4 mt-6">
          <button
            onClick={runAll}
            disabled={runningAll}
            className="flex items-center gap-2 px-6 py-3 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl text-sm font-bold shadow-md shadow-[#6366F1]/25 transition-all disabled:opacity-60"
          >
            {runningAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            {runningAll ? 'Running All Scenarios…' : 'Run All 6 Scenarios'}
          </button>
          {completedCount > 0 && (
            <span className="text-sm font-bold text-[#059669] bg-[#ECFDF5] px-3 py-1.5 rounded-full border border-[#A7F3D0]">
              ✓ {completedCount}/6 Scenarios Executed
            </span>
          )}
        </div>
      </div>

      {/* Guardian Principle Banner */}
      <div className="premium-card p-4.5 flex items-center gap-4 border-[#C7D2FE] bg-[#EEF2FF]/50">
        <div className="w-10 h-10 bg-[#6366F1]/10 rounded-xl flex items-center justify-center shrink-0">
          <Shield className="w-5 h-5 text-[#6366F1]" />
        </div>
        <div>
          <p className="text-[#4338CA] text-sm font-bold">The Policy Guardian Principle</p>
          <p className="text-[#4B5563] text-xs font-medium mt-0.5">
            AI PROPOSES ACTION → POLICY GUARDIAN VALIDATES → APPROVE / BLOCK / ESCALATE → ONLY APPROVED ACTIONS EXECUTE
          </p>
        </div>
      </div>

      {/* Scenario Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {SCENARIOS.map(sc => (
          <div key={sc.id} className="space-y-4">
            {/* Scenario Card */}
            <div className="premium-card p-6 flex flex-col justify-between h-full">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl p-2 bg-[#F9FAFB] rounded-xl border border-[#E5E7EB]">{sc.icon}</span>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-[#0B132B] font-bold text-sm">{sc.title}</h3>
                      </div>
                      <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${sc.tagColor}`}>{sc.tag}</span>
                    </div>
                  </div>
                  <span className="text-[#9CA3AF] text-xs font-mono font-bold">#{sc.id}</span>
                </div>
                <p className="text-[#4B5563] text-xs font-medium mt-3 mb-5 leading-relaxed">{sc.subtitle}</p>
              </div>
              <button
                onClick={() => runScenario(sc.id)}
                disabled={loading[sc.id] || runningAll}
                className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#F9FAFB] hover:bg-[#F3F4F6] text-[#0B132B] border border-[#E5E7EB] hover:border-[#D1D5DB] rounded-xl text-xs font-bold transition-all shadow-2xs disabled:opacity-50"
              >
                {loading[sc.id]
                  ? <><Loader2 className="w-3.5 h-3.5 animate-spin text-[#6366F1]" /> Executing Scenario {sc.id}…</>
                  : results[sc.id]
                  ? <><CheckCircle className="w-3.5 h-3.5 text-[#10B981]" /> Run Again</>
                  : <><PlayCircle className="w-3.5 h-3.5 text-[#6366F1]" /> Run Scenario {sc.id}</>}
              </button>
            </div>

            {/* Result */}
            {results[sc.id] && (
              <ResultCard result={results[sc.id]!} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
