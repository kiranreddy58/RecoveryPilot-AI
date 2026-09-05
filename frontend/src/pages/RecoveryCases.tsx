import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, Loader2, RefreshCw, Search, Filter } from 'lucide-react';
import { recoveryCasesApi } from '../api/recoveryCasesApi';
import { RecoveryCase } from '../types';
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

export function RecoveryCases() {
  const [cases, setCases] = useState<RecoveryCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params: any = { limit: 200 };
      if (statusFilter !== 'ALL') params.status = statusFilter;
      const data = await recoveryCasesApi.getCases(params);
      const arr = Array.isArray(data) ? data : [];
      setCases(arr);
      setTotal(arr.length);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cases');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { fetchCases(); }, [fetchCases]);

  const filtered = cases.filter(c =>
    !search ||
    c.case_id.toLowerCase().includes(search.toLowerCase()) ||
    c.merchant_id.toLowerCase().includes(search.toLowerCase()) ||
    c.customer_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Recovery Cases</h1>
          <p className="text-[#4B5563] text-sm font-medium mt-1">{total} total revenue risk cases recorded</p>
        </div>
        <button
          onClick={fetchCases}
          className="flex items-center gap-2 px-3.5 py-2 bg-white hover:bg-[#F3F4F6] text-[#4B5563] hover:text-[#0B132B] border border-[#E5E7EB] rounded-xl text-xs font-semibold shadow-xs transition-all w-fit"
        >
          <RefreshCw className="w-4 h-4 text-[#6366F1]" />
          Refresh Cases
        </button>
      </div>

      {/* Filters & Search Bar */}
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between bg-white p-4 rounded-2xl border border-[#E5E7EB] shadow-xs">
        <div className="relative w-full lg:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search Case ID, merchant…"
            className="w-full pl-10 pr-4 py-2 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm text-[#0B132B] placeholder-[#9CA3AF] focus:outline-none focus:border-[#6366F1] focus:bg-white transition-all font-medium"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1 text-xs font-bold text-[#6B7280] uppercase tracking-wider mr-1">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          {['ALL', 'DETECTED', 'DIAGNOSED', 'ESCALATED', 'BLOCKED', 'CLOSED', 'RECOVERED', 'STOPPED'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-2xs ${
                statusFilter === s
                  ? 'bg-[#6366F1] text-white shadow-sm shadow-[#6366F1]/30'
                  : 'bg-[#F9FAFB] text-[#4B5563] hover:bg-[#F3F4F6] hover:text-[#0B132B] border border-[#E5E7EB]'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center h-64 bg-white rounded-2xl border border-[#E5E7EB]">
          <Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" />
        </div>
      ) : error ? (
        <div className="flex flex-col items-center justify-center h-64 bg-white rounded-2xl border border-[#FECACA] text-[#DC2626] space-y-4">
          <AlertCircle className="w-10 h-10 text-[#EF4444]" />
          <p className="text-sm font-semibold">{error}</p>
          <button onClick={fetchCases} className="px-4 py-2 bg-[#6366F1] text-white rounded-xl text-xs font-bold hover:bg-[#4F46E5]">Retry</button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-2xl p-16 text-center border border-[#E5E7EB]">
          <p className="text-[#0B132B] font-bold text-base">No cases found</p>
          <p className="text-[#6B7280] text-xs mt-1">Try changing your search query or run a demo scenario to create cases.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E5E7EB] bg-[#F9FAFB] text-[#4B5563] text-xs uppercase font-bold tracking-wider">
                  <th className="text-left px-6 py-4">Case ID</th>
                  <th className="text-left px-6 py-4">Type</th>
                  <th className="text-left px-6 py-4">Merchant</th>
                  <th className="text-right px-6 py-4">At Risk</th>
                  <th className="text-right px-6 py-4">Recovered</th>
                  <th className="text-left px-6 py-4">Risk</th>
                  <th className="text-left px-6 py-4">Status</th>
                  <th className="text-left px-6 py-4">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F3F4F6]">
                {filtered.map((c) => (
                  <tr key={c.id} className="hover:bg-[#F9FAFB] transition-colors group">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        to={`/cases/${c.case_id}`}
                        className="text-[#6366F1] hover:text-[#4F46E5] font-mono text-xs font-bold hover:underline"
                      >
                        {c.case_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-[#4B5563] text-xs font-medium">
                      {TYPE_LABELS[c.case_type] || c.case_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-[#6B7280] text-xs font-mono">
                      {c.merchant_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-[#0B132B] font-bold text-xs">
                      {c.amount_at_risk != null ? INR(c.amount_at_risk) : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-xs">
                      <span className={c.recovered_amount ? 'text-[#059669] font-bold' : 'text-[#9CA3AF]'}>
                        {c.recovered_amount ? INR(c.recovered_amount) : '—'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {c.risk_level ? <StatusBadge status={c.risk_level} /> : <span className="text-[#9CA3AF] text-xs">—</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-[#6B7280] text-xs">
                      {new Date(c.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-3.5 border-t border-[#E5E7EB] bg-[#F9FAFB] flex justify-between items-center text-xs font-semibold text-[#6B7280]">
            <span>Showing {filtered.length} of {total} cases</span>
          </div>
        </div>
      )}
    </div>
  );
}
