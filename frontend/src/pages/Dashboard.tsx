import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  TrendingUp, DollarSign, CheckCircle, AlertTriangle,
  Shield, Users, XCircle, RefreshCw, ArrowRight, Layers
} from 'lucide-react';
import { metricsApi } from '../api/metricsApi';
import { FullMetrics } from '../types';
import { MetricCard, MiniMetric } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

const TYPE_LABELS: Record<string, string> = {
  PAYMENT_FAILURE: 'Payment Failure',
  CHECKOUT_ABANDONMENT: 'Checkout Abandonment',
  OVERDUE_RECEIVABLE: 'Overdue Invoice',
  SUBSCRIPTION_FAILURE: 'Subscription Failure',
  PROMISE_TO_PAY_BROKEN: 'Promise Broken',
};

const TYPE_COLORS: Record<string, string> = {
  PAYMENT_FAILURE: 'bg-[#EF4444]',
  CHECKOUT_ABANDONMENT: 'bg-[#F59E0B]',
  OVERDUE_RECEIVABLE: 'bg-[#6366F1]',
  SUBSCRIPTION_FAILURE: 'bg-[#8B5CF6]',
  PROMISE_TO_PAY_BROKEN: 'bg-[#EC4899]',
};

import { useRecoveryStream } from '../hooks/useRecoveryStream';

export function Dashboard() {
  const [metrics, setMetrics] = useState<FullMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setError(null);
      const data = await metricsApi.getFull();
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (e: any) {
      setError(e.message || 'Failed to load metrics');
    } finally {
      setLoading(false);
    }
  }, []);

  // Connect to live SSE stream for instant updates
  const { connected } = useRecoveryStream(
    useCallback(() => {
      fetchMetrics();
    }, [fetchMetrics])
  );

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  if (loading) return <DashboardSkeleton />;

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 bg-[#FEF2F2] rounded-full flex items-center justify-center mx-auto mb-4 border border-[#FECACA]">
          <AlertTriangle className="w-8 h-8 text-[#EF4444]" />
        </div>
        <h2 className="text-[#0B132B] text-xl font-bold mb-2">Backend Connection Issue</h2>
        <p className="text-[#4B5563] text-sm mb-6">{error}</p>
        <button onClick={fetchMetrics} className="px-5 py-2.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl text-sm font-semibold shadow-md shadow-[#6366F1]/20 transition-all">
          Retry Connection
        </button>
      </div>
    );
  }

  if (!metrics) return null;

  const recoveryRate = metrics.recovery_rate_amount;
  const byType = Object.entries(metrics.by_type || {});
  const maxRevenue = Math.max(...byType.map(([, v]) => v.revenue_at_risk), 1);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Control Tower</h2>
            {connected ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping" />
                LIVE STREAM
              </span>
            ) : metrics ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wider bg-[#ECFDF5] text-[#059669] border border-[#A7F3D0]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#10B981]" />
                ONLINE • AUTO-SYNC
              </span>
            ) : error ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FEF2F2] text-[#EF4444] border border-[#FECACA]">
                OFFLINE
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#F3F4F6] text-[#6B7280] border border-[#E5E7EB]">
                CONNECTING...
              </span>
            )}
          </div>
          <p className="text-[#4B5563] text-sm font-medium mt-1">
            Detect lost revenue. Understand why. Recover safely. Know when to stop.
          </p>
        </div>
        <button
          onClick={fetchMetrics}
          className="flex items-center gap-2 px-3.5 py-2 bg-white hover:bg-[#F3F4F6] text-[#4B5563] hover:text-[#0B132B] border border-[#E5E7EB] rounded-xl text-xs font-semibold shadow-xs transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[#6366F1]" />
          {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : 'Refresh'}
        </button>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          label="Revenue at Risk"
          value={INR(metrics.total_revenue_at_risk)}
          icon={DollarSign}
          iconColor="text-[#F59E0B]"
          bgColor="bg-[#FFFBEB]"
          delay={0}
        />
        <MetricCard
          label="Money Recovered"
          value={INR(metrics.total_recovered)}
          sub={`${recoveryRate.toFixed(1)}% recovery rate`}
          icon={TrendingUp}
          iconColor="text-[#10B981]"
          bgColor="bg-[#ECFDF5]"
          delay={100}
        />
        <MetricCard
          label="Total Cases"
          value={metrics.total_cases.toLocaleString()}
          sub={`${metrics.status_breakdown?.CLOSED || 0} closed`}
          icon={Layers}
          iconColor="text-[#6366F1]"
          bgColor="bg-[#EEF2FF]"
          delay={200}
        />
        <MetricCard
          label="Human Escalations"
          value={metrics.escalations?.total || 0}
          sub={`${metrics.escalations?.open || 0} open in queue`}
          icon={Users}
          iconColor="text-[#EA580C]"
          bgColor="bg-[#FFF7ED]"
          delay={300}
        />
      </div>

      {/* Recovery Rate Progress Card */}
      <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-[#0B132B] font-bold text-base">Net Recovery Rate</h3>
            <p className="text-[#4B5563] text-xs mt-0.5">% of detected revenue at risk successfully recovered</p>
          </div>
          <span className="text-3xl font-black text-gradient-emerald">{recoveryRate.toFixed(1)}%</span>
        </div>
        <div className="h-3.5 bg-[#F3F4F6] rounded-full overflow-hidden p-0.5 border border-[#E5E7EB]">
          <div
            className="h-full bg-gradient-to-r from-[#10B981] to-[#34D399] rounded-full transition-all duration-1000 shadow-xs"
            style={{ width: `${Math.min(recoveryRate, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-[11px] font-semibold text-[#6B7280] mt-2">
          <span>0%</span>
          <span>50% Target</span>
          <span>100%</span>
        </div>
      </div>

      {/* Three-column Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Policy Guardian Stats */}
        <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '250ms' }}>
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-[#F3F4F6]">
            <div className="w-8 h-8 rounded-lg bg-[#EEF2FF] flex items-center justify-center">
              <Shield className="w-4 h-4 text-[#6366F1]" />
            </div>
            <div>
              <h3 className="text-[#0B132B] font-bold text-sm">Policy Guardian</h3>
              <p className="text-[#6B7280] text-[11px]">Deterministic Safety Gate</p>
            </div>
          </div>
          <div className="space-y-0">
            <MiniMetric label="Total Policy Checks" value={metrics.guardian.total_checks} />
            <MiniMetric label="Approved Actions" value={metrics.guardian.approved} color="text-[#059669]" />
            <MiniMetric label="Blocked Actions" value={metrics.guardian.blocked} color="text-[#DC2626]" />
            <MiniMetric label="Human Approval Required" value={metrics.guardian.human_required} color="text-[#D97706]" />
          </div>
        </div>

        {/* Action Outcomes */}
        <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '300ms' }}>
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-[#F3F4F6]">
            <div className="w-8 h-8 rounded-lg bg-[#ECFDF5] flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-[#10B981]" />
            </div>
            <div>
              <h3 className="text-[#0B132B] font-bold text-sm">Action Outcomes</h3>
              <p className="text-[#6B7280] text-[11px]">Execution Status</p>
            </div>
          </div>
          <div className="space-y-0">
            <MiniMetric label="Total Actions" value={metrics.actions.total} />
            <MiniMetric label="Verified Success" value={metrics.actions.successful} color="text-[#059669]" />
            <MiniMetric label="Verified Failure" value={metrics.actions.failed} color="text-[#DC2626]" />
            <MiniMetric label="Unknown / Timeout" value={metrics.actions.unknown} color="text-[#4B5563]" />
          </div>
        </div>

        {/* Case State Breakdown */}
        <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '350ms' }}>
          <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-[#F3F4F6]">
            <div className="w-8 h-8 rounded-lg bg-[#FFFBEB] flex items-center justify-center">
              <XCircle className="w-4 h-4 text-[#F59E0B]" />
            </div>
            <div>
              <h3 className="text-[#0B132B] font-bold text-sm">Case States</h3>
              <p className="text-[#6B7280] text-[11px]">State Machine Distribution</p>
            </div>
          </div>
          <div className="space-y-0">
            {['CLOSED', 'ESCALATED', 'BLOCKED', 'STOPPED', 'DETECTED'].map(s => (
              <MiniMetric
                key={s}
                label={s.replace('_', ' ')}
                value={metrics.status_breakdown?.[s] || 0}
                color={
                  s === 'CLOSED' ? 'text-[#059669]' :
                  s === 'ESCALATED' ? 'text-[#D97706]' :
                  s === 'BLOCKED' ? 'text-[#DC2626]' :
                  s === 'STOPPED' ? 'text-[#4B5563]' : 'text-[#6366F1]'
                }
              />
            ))}
          </div>
        </div>
      </div>

      {/* Recovery by Workflow Type */}
      <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
        <h3 className="text-[#0B132B] font-bold text-base mb-5">Recovery by Workflow</h3>
        <div className="space-y-5">
          {byType.map(([type, stats]) => {
            const pct = stats.revenue_at_risk > 0 ? (stats.recovered / stats.revenue_at_risk) * 100 : 0;
            const barWidth = stats.revenue_at_risk > 0 ? (stats.revenue_at_risk / maxRevenue) * 100 : 0;
            return (
              <div key={type} className="group">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2.5">
                    <span className={`w-2.5 h-2.5 rounded-full ${TYPE_COLORS[type] || 'bg-[#4B5563]'}`} />
                    <span className="text-sm text-[#0B132B] font-semibold">{TYPE_LABELS[type] || type}</span>
                    <span className="text-xs text-[#6B7280]">({stats.count} cases)</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm text-[#059669] font-bold">{INR(stats.recovered)}</span>
                    <span className="text-xs text-[#6B7280] ml-1">/ {INR(stats.revenue_at_risk)}</span>
                  </div>
                </div>
                <div className="h-2.5 bg-[#F3F4F6] rounded-full overflow-hidden border border-[#E5E7EB]">
                  <div
                    className={`h-full ${TYPE_COLORS[type] || 'bg-[#6366F1]'} opacity-80 rounded-full transition-all duration-700`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>
                <div className="flex justify-between mt-1 text-[11px] text-[#6B7280]">
                  <span>Revenue at risk</span>
                  <span className="font-semibold text-[#0B132B]">{pct.toFixed(0)}% recovered</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Cases Table */}
      <div className="premium-card p-6 animate-fade-in-up" style={{ animationDelay: '450ms' }}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-[#0B132B] font-bold text-base">Recent Cases</h3>
          <Link to="/cases" className="text-[#6366F1] hover:text-[#4F46E5] text-xs font-bold flex items-center gap-1 transition-colors">
            View all cases <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
        {metrics.recent_cases.length === 0 ? (
          <p className="text-[#6B7280] text-sm text-center py-8">No cases yet. Run Demo Mode or Batch Processing to generate data.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E5E7EB] text-[#4B5563] text-xs uppercase font-bold tracking-wider">
                  <th className="text-left pb-3">Case ID</th>
                  <th className="text-left pb-3">Type</th>
                  <th className="text-left pb-3">Status</th>
                  <th className="text-right pb-3">At Risk</th>
                  <th className="text-right pb-3">Recovered</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3F4F6]">
                {metrics.recent_cases.map((c) => (
                  <tr key={c.case_id} className="hover:bg-[#F9FAFB] transition-colors">
                    <td className="py-3.5">
                      <Link to={`/cases/${c.case_id}`} className="text-[#6366F1] hover:text-[#4F46E5] font-mono text-xs font-bold hover:underline">
                        {c.case_id}
                      </Link>
                    </td>
                    <td className="py-3.5 text-[#4B5563] text-xs font-medium">{TYPE_LABELS[c.case_type] || c.case_type}</td>
                    <td className="py-3.5"><StatusBadge status={c.status} /></td>
                    <td className="py-3.5 text-right text-[#0B132B] font-semibold text-xs">{INR(c.amount_at_risk || 0)}</td>
                    <td className="py-3.5 text-right">
                      <span className={c.recovered_amount ? 'text-[#059669] font-bold text-xs' : 'text-[#9CA3AF] text-xs'}>
                        {c.recovered_amount ? INR(c.recovered_amount) : '—'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="skeleton h-8 w-64" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {[0,1,2,3].map(i => <div key={i} className="skeleton h-32 rounded-2xl" />)}
      </div>
      <div className="skeleton h-28 rounded-2xl" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[0,1,2].map(i => <div key={i} className="skeleton h-56 rounded-2xl" />)}
      </div>
    </div>
  );
}
