import { useState, useCallback } from 'react';
import { Database, Loader2, CheckCircle, BarChart3, AlertTriangle } from 'lucide-react';
import { batchApi } from '../api/demoApi';
import { BatchResults } from '../types';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

const TYPE_LABELS: Record<string, string> = {
  PAYMENT_FAILURE: 'Payment Failure',
  CHECKOUT_ABANDONMENT: 'Checkout Abandonment',
  OVERDUE_RECEIVABLE: 'Overdue Invoice',
  SUBSCRIPTION_FAILURE: 'Subscription Failure',
  PROMISE_TO_PAY_BROKEN: 'Promise Broken',
};

function MetaRow({ label, value, color = 'text-[#0B132B]' }: { label: string; value: any; color?: string }) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-[#F3F4F6] last:border-0">
      <span className="text-[#4B5563] text-sm font-medium">{label}</span>
      <span className={`font-bold text-sm ${color}`}>{value}</span>
    </div>
  );
}

export function BatchProcessing() {
  const [targetCount, setTargetCount] = useState(100);
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<BatchResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  const runBatch = useCallback(async () => {
    setRunning(true);
    setError(null);
    setResults(null);
    const start = Date.now();
    try {
      const data = await batchApi.runBatch(targetCount);
      setResults(data);
      setElapsed(Date.now() - start);
    } catch (e: any) {
      setError(e.message || 'Batch failed');
    } finally {
      setRunning(false);
    }
  }, [targetCount]);

  const breakdownEntries = results?.breakdown_by_type
    ? Object.entries(results.breakdown_by_type)
    : [];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Batch Processing</h1>
        <p className="text-[#4B5563] text-sm font-medium mt-1">
          Generate realistic synthetic revenue risk cases (10 to 1,000) and execute the closed-loop recovery pipeline at scale.
        </p>
      </div>

      {/* Configuration Card */}
      <div className="premium-card p-6">
        <h2 className="text-[#0B132B] font-bold text-base mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-[#6366F1]" />
          Batch Generator Configuration
        </h2>
        <div className="flex flex-col sm:flex-row gap-5 items-end">
          <div className="flex-1 w-full">
            <label className="text-[#4B5563] text-xs font-bold uppercase tracking-wider block mb-2">
              Number of Cases to Generate (10 – 1,000)
            </label>
            <div className="flex items-center gap-4 bg-[#F9FAFB] p-3 rounded-xl border border-[#E5E7EB]">
              <input
                type="range"
                min={10}
                max={1000}
                step={10}
                value={targetCount}
                onChange={e => setTargetCount(Number(e.target.value))}
                className="flex-1 h-2 bg-[#E5E7EB] rounded-full appearance-none cursor-pointer accent-[#6366F1]"
              />
              <span className="text-[#0B132B] font-black text-xl w-16 text-right font-mono">{targetCount}</span>
            </div>
            <div className="flex justify-between text-[11px] font-semibold text-[#9CA3AF] mt-1.5 px-1">
              <span>10 cases</span>
              <span>500 cases</span>
              <span>1,000 cases</span>
            </div>
          </div>
          <button
            onClick={runBatch}
            disabled={running}
            className="flex items-center justify-center gap-2 px-6 py-3.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl font-bold shadow-md shadow-[#6366F1]/25 transition-all disabled:opacity-60 whitespace-nowrap w-full sm:w-auto"
          >
            {running
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Processing {targetCount} Cases…</>
              : <><BarChart3 className="w-4 h-4" /> Run Batch Simulation</>}
          </button>
        </div>
        <p className="text-[#6B7280] text-xs mt-4 leading-relaxed font-medium">
          💡 Generates realistic data with intentional real-world distribution: missing amounts, invalid events, duplicates, low AI confidence, and limit breaches.
        </p>
      </div>

      {error && (
        <div className="p-5 bg-[#FEF2F2] border border-[#FECACA] rounded-2xl flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-[#EF4444] shrink-0" />
          <p className="text-[#DC2626] text-sm font-semibold">{error}</p>
        </div>
      )}

      {running && (
        <div className="premium-card p-12 text-center">
          <Loader2 className="w-10 h-10 text-[#6366F1] animate-spin mx-auto mb-4" />
          <p className="text-[#0B132B] font-bold text-lg">Processing {targetCount} cases in parallel…</p>
          <p className="text-[#4B5563] text-sm font-medium mt-1">
            Running DETECT → DIAGNOSE → SIMULATE → GUARDIAN CHECK → EXECUTE → VERIFY for each case
          </p>
          <div className="mt-6 h-2 bg-[#F3F4F6] rounded-full overflow-hidden max-w-xs mx-auto border border-[#E5E7EB]">
            <div className="h-full bg-gradient-to-r from-[#6366F1] to-[#10B981] animate-pulse rounded-full w-3/4" />
          </div>
        </div>
      )}

      {results && !running && (
        <div className="space-y-6 animate-fade-in-up">
          {/* Summary Banner */}
          <div className="premium-card p-6 border-[#A7F3D0] bg-[#ECFDF5]/30">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-[#10B981]" />
              </div>
              <div>
                <h2 className="text-[#0B132B] font-extrabold text-lg">Batch Run Complete</h2>
                <p className="text-[#4B5563] text-xs font-medium">
                  {results.processed_cases} of {results.total_cases} cases processed
                  {elapsed ? ` in ${(elapsed / 1000).toFixed(1)}s` : ''}
                </p>
              </div>
            </div>

            {/* Main KPIs */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Revenue at Risk', value: INR(results.total_revenue_at_risk || 0), color: 'text-[#D97706]' },
                { label: 'Money Recovered', value: INR(results.total_recovered || 0), color: 'text-[#059669]' },
                { label: 'Recovery Rate', value: `${(results.recovery_rate || 0).toFixed(1)}%`, color: 'text-[#059669]' },
                { label: 'Total Cases', value: results.total_cases, color: 'text-[#0B132B]' },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-white rounded-xl p-4 text-center border border-[#E5E7EB] shadow-2xs">
                  <p className="text-[#6B7280] text-xs font-semibold uppercase">{label}</p>
                  <p className={`text-xl lg:text-2xl font-black mt-1 ${color}`}>{value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Detailed Outcomes */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="premium-card p-6">
              <h3 className="text-[#0B132B] font-bold text-sm mb-3">Case Outcomes</h3>
              <MetaRow label="Recovered / Closed" value={results.cases_recovered} color="text-[#059669]" />
              <MetaRow label="Blocked by Guardian" value={results.cases_blocked} color="text-[#DC2626]" />
              <MetaRow label="Escalated to Human" value={results.cases_escalated} color="text-[#D97706]" />
              <MetaRow label="Stopped by Rules" value={results.cases_stopped} color="text-[#4B5563]" />
              <MetaRow label="Failed Verifications" value={results.cases_failed} color="text-[#DC2626]" />
            </div>

            <div className="premium-card p-6">
              <h3 className="text-[#0B132B] font-bold text-sm mb-3">Actions & Guardian Stats</h3>
              <MetaRow label="Actions Executed" value={results.actions_executed} color="text-[#4F46E5]" />
              <MetaRow label="Actions Blocked" value={results.actions_blocked} color="text-[#DC2626]" />
              <MetaRow label="Human Escalations" value={results.human_escalations} color="text-[#D97706]" />
              <MetaRow
                label="Guardian Block Rate"
                value={results.actions_executed > 0
                  ? `${((results.actions_blocked / (results.actions_executed + results.actions_blocked)) * 100).toFixed(1)}%`
                  : '—'}
                color="text-[#EA580C]"
              />
            </div>
          </div>

          {/* Breakdown by Workflow */}
          {breakdownEntries.length > 0 && (
            <div className="premium-card p-6">
              <h3 className="text-[#0B132B] font-bold text-base mb-4">Breakdown by Workflow Type</h3>
              <div className="space-y-4">
                {breakdownEntries.map(([type, stats]) => {
                  const s = stats as any;
                  const rate = s.revenue_at_risk > 0 ? (s.recovered / s.revenue_at_risk) * 100 : 0;
                  return (
                    <div key={type}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-[#0B132B] font-bold">{TYPE_LABELS[type] || type}</span>
                          <span className="text-xs text-[#6B7280]">({s.count || 0} cases)</span>
                        </div>
                        <div className="text-right text-xs">
                          <span className="text-[#059669] font-bold">{INR(s.recovered || 0)}</span>
                          <span className="text-[#6B7280] ml-1">/ {INR(s.revenue_at_risk || 0)}</span>
                        </div>
                      </div>
                      <div className="h-2.5 bg-[#F3F4F6] rounded-full overflow-hidden border border-[#E5E7EB]">
                        <div
                          className="h-full bg-[#10B981] rounded-full transition-all duration-700"
                          style={{ width: `${Math.min(rate, 100)}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-[#6B7280] font-semibold mt-1 text-right">{rate.toFixed(0)}% recovered</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
