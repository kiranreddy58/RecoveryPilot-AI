import { useState, useEffect } from 'react';
import { Calculator, Sparkles, Info, RefreshCw } from 'lucide-react';
import { metricsApi } from '../api/metricsApi';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

export function RoiCalculator() {
  const [monthlyGmv, setMonthlyGmv] = useState(5000000); // ₹50 Lakhs default
  const [failureRate, setFailureRate] = useState(12);     // 12% default
  const [avgRecoveryRate, setAvgRecoveryRate] = useState(70); // 70% assumption
  const [estCostPerAction, setEstCostPerAction] = useState(50); // ₹50 per bounded recovery action
  const [liveSynced, setLiveSynced] = useState(false);
  const [syncLoading, setSyncLoading] = useState(false);

  // Sync with live control tower metrics if available
  const syncLiveMetrics = async () => {
    setSyncLoading(true);
    try {
      const data = await metricsApi.getFull();
      if (data && data.total_revenue_at_risk > 0) {
        const estGmv = Math.max(500000, Math.round(data.total_revenue_at_risk * 8.33));
        setMonthlyGmv(estGmv);
        if (data.recovery_rate_amount > 0) {
          setAvgRecoveryRate(Math.min(95, Math.max(10, Math.round(data.recovery_rate_amount))));
        }
        setLiveSynced(true);
      }
    } catch (e) {
      // Fall back to default scenario
    } finally {
      setSyncLoading(false);
    }
  };

  useEffect(() => {
    syncLiveMetrics();
  }, []);

  // Unit Economics Formulas (Transparent & Assumptions-based)
  const monthlyLeakage = monthlyGmv * (failureRate / 100);
  const monthlyRecovered = monthlyLeakage * (avgRecoveryRate / 100);
  const annualRecovered = monthlyRecovered * 12;
  
  // Action volume estimate based on average ticket size ₹5,000
  const estimatedMonthlyActions = Math.max(10, Math.round(monthlyLeakage / 5000));
  const annualOperationalCost = estimatedMonthlyActions * estCostPerAction * 12;
  
  const netAnnualBenefit = annualRecovered - annualOperationalCost;
  const benefitCostRatio = annualOperationalCost > 0 ? (netAnnualBenefit / annualOperationalCost).toFixed(1) : '—';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EEF2FF] border border-[#C7D2FE] rounded-full text-xs font-bold text-[#4F46E5] mb-2 shadow-2xs">
            <Calculator className="w-3.5 h-3.5" /> SCENARIO SIMULATION MODEL
          </div>
          <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Revenue Leakage & ROI Scenario Simulator</h1>
          <p className="text-[#4B5563] text-sm font-medium mt-1 max-w-3xl">
            Model projected revenue recovery outcomes across user-defined transaction volume and failure rate assumptions.
          </p>
        </div>
        <button
          onClick={syncLiveMetrics}
          disabled={syncLoading}
          className="flex items-center gap-2 px-3.5 py-2 bg-white hover:bg-[#F3F4F6] text-[#4B5563] hover:text-[#0B132B] border border-[#E5E7EB] rounded-xl text-xs font-bold shadow-2xs transition-all w-fit disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#6366F1] ${syncLoading ? 'animate-spin' : ''}`} />
          {liveSynced ? 'Synced with Live Metrics' : 'Sync Live Telemetry'}
        </button>
      </div>

      {/* Assumptions Banner */}
      <div className="p-4 bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl flex items-start gap-3 text-xs text-[#92400E]">
        <Info className="w-5 h-5 text-[#D97706] shrink-0 mt-0.5" />
        <div>
          <p className="font-bold uppercase tracking-wider">Illustrative Simulation Notice</p>
          <p className="mt-0.5 leading-relaxed font-medium">
            Projections are calculated dynamically from your input parameters and do not represent guaranteed real-world returns.
            Actual merchant recovery depends on customer responsiveness, payment method mix, and policy thresholds.
          </p>
        </div>
      </div>

      {/* Interactive Sliders & Live Projections */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Input Panel */}
        <div className="lg:col-span-5 space-y-5">
          <div className="premium-card p-6 space-y-6">
            <h2 className="text-[#0B132B] font-bold text-sm uppercase tracking-wider pb-2 border-b border-[#F3F4F6]">
              User-Defined Parameters
            </h2>

            {/* GMV Slider */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-[#4B5563] uppercase">Monthly Processed GMV</label>
                <span className="text-sm font-black text-[#0B132B] font-mono">{INR(monthlyGmv)}</span>
              </div>
              <input
                type="range"
                min={500000}
                max={50000000}
                step={500000}
                value={monthlyGmv}
                onChange={e => setMonthlyGmv(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E7EB] rounded-full appearance-none cursor-pointer accent-[#6366F1]"
              />
              <div className="flex justify-between text-[10px] font-semibold text-[#9CA3AF] mt-1">
                <span>₹5 Lakhs</span>
                <span>₹2.5 Crores</span>
                <span>₹5 Crores</span>
              </div>
            </div>

            {/* Failure Rate Slider */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-[#4B5563] uppercase">Estimated Failure / Drop-off Rate</label>
                <span className="text-sm font-black text-[#D97706] font-mono">{failureRate}%</span>
              </div>
              <input
                type="range"
                min={2}
                max={30}
                step={1}
                value={failureRate}
                onChange={e => setFailureRate(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E7EB] rounded-full appearance-none cursor-pointer accent-[#F59E0B]"
              />
              <div className="flex justify-between text-[10px] font-semibold text-[#9CA3AF] mt-1">
                <span>2% (Low)</span>
                <span>12% (Industry Avg)</span>
                <span>30% (High)</span>
              </div>
            </div>

            {/* AI Recovery Benchmark */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-[#4B5563] uppercase">Assumed Target Recovery Rate</label>
                <span className="text-sm font-black text-[#059669] font-mono">{avgRecoveryRate}%</span>
              </div>
              <input
                type="range"
                min={30}
                max={90}
                step={5}
                value={avgRecoveryRate}
                onChange={e => setAvgRecoveryRate(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E7EB] rounded-full appearance-none cursor-pointer accent-[#10B981]"
              />
              <div className="flex justify-between text-[10px] font-semibold text-[#9CA3AF] mt-1">
                <span>30% (Conservative)</span>
                <span>70% (Benchmarked)</span>
                <span>90% (Aggressive)</span>
              </div>
            </div>

            {/* Cost per action */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-[#4B5563] uppercase">Est. Operational Cost / Recovery Action</label>
                <span className="text-sm font-black text-[#4B5563] font-mono">₹{estCostPerAction}</span>
              </div>
              <input
                type="range"
                min={10}
                max={200}
                step={10}
                value={estCostPerAction}
                onChange={e => setEstCostPerAction(Number(e.target.value))}
                className="w-full h-2 bg-[#E5E7EB] rounded-full appearance-none cursor-pointer accent-[#6366F1]"
              />
            </div>
          </div>
        </div>

        {/* Output Hero Metrics Panel */}
        <div className="lg:col-span-7 space-y-5">
          {/* Main Net Revenue Boost Card */}
          <div className="premium-card p-6 bg-[#0B132B] text-white border-0 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/10 rounded-full text-xs font-bold text-[#34D399]">
                <Sparkles className="w-3.5 h-3.5" /> PROJECTED ANNUAL NET BENEFIT
              </span>
              <span className="text-xs font-bold text-[#A7F3D0]">{benefitCostRatio}x Benefit-to-Cost Ratio</span>
            </div>
            <p className="text-4xl lg:text-5xl font-black text-[#10B981] tracking-tight">{INR(netAnnualBenefit)}</p>
            <p className="text-slate-300 text-xs mt-2 font-medium">
              Formula: (Monthly GMV × {failureRate}% Risk × {avgRecoveryRate}% Recovery × 12) − Annual Action Costs
            </p>

            <div className="grid grid-cols-2 gap-3 mt-6 pt-5 border-t border-white/10">
              <div>
                <p className="text-slate-400 text-xs">Projected Monthly Recovery</p>
                <p className="text-xl font-bold text-white mt-0.5">{INR(monthlyRecovered)}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs">Monthly Revenue at Risk</p>
                <p className="text-xl font-bold text-[#F59E0B] mt-0.5">{INR(monthlyLeakage)}</p>
              </div>
            </div>
          </div>

          {/* Breakdown Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="premium-card p-4 text-center">
              <p className="text-[#6B7280] text-xs font-bold uppercase">Annual Gross Leakage</p>
              <p className="text-lg font-black text-[#D97706] mt-1">{INR(monthlyLeakage * 12)}</p>
              <p className="text-[10px] text-[#6B7280] font-medium mt-0.5">Based on {failureRate}% rate</p>
            </div>
            <div className="premium-card p-4 text-center">
              <p className="text-[#6B7280] text-xs font-bold uppercase">Annual Gross Recovery</p>
              <p className="text-lg font-black text-[#059669] mt-1">{INR(annualRecovered)}</p>
              <p className="text-[10px] text-[#6B7280] font-medium mt-0.5">At {avgRecoveryRate}% capture</p>
            </div>
            <div className="premium-card p-4 text-center">
              <p className="text-[#6B7280] text-xs font-bold uppercase">Est. Annual Action Costs</p>
              <p className="text-lg font-black text-[#4B5563] mt-1">{INR(annualOperationalCost)}</p>
              <p className="text-[10px] text-[#6B7280] font-medium mt-0.5">₹{estCostPerAction}/intervention</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
