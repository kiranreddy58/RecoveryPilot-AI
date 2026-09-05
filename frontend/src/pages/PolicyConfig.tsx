import { useState, useEffect } from 'react';
import { Save, RotateCcw, CheckCircle, AlertCircle, Lock, Loader2 } from 'lucide-react';
import { guardianApi, GuardianPolicies } from '../api/guardianApi';

export function PolicyConfig() {
  const [policies, setPolicies] = useState<GuardianPolicies | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await guardianApi.getPolicies();
      setPolicies(res.active_policies);
    } catch (e: any) {
      setError(e.message || 'Failed to load safety policies');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!policies) return;
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const res = await guardianApi.updatePolicies(policies);
      setPolicies(res.active_policies);
      setMessage('Policy Guardian safety rules successfully updated and live.');
      setTimeout(() => setMessage(null), 3500);
    } catch (e: any) {
      setError(e.message || 'Failed to update safety policies');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const res = await guardianApi.resetPolicies();
      setPolicies(res.active_policies);
      setMessage('Policies successfully reset to default baseline.');
      setTimeout(() => setMessage(null), 3500);
    } catch (e: any) {
      setError(e.message || 'Failed to reset safety policies');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !policies) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-[#6366F1] animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EEF2FF] border border-[#C7D2FE] rounded-full text-xs font-bold text-[#4F46E5] mb-2 shadow-2xs">
            <Lock className="w-3.5 h-3.5 text-[#6366F1]" /> DETERMINISTIC COMPLIANCE ENGINE
          </div>
          <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Policy Guardian Rules Configurator</h1>
          <p className="text-[#4B5563] text-sm font-medium mt-1">
            Configure hard safety limits. AI has zero authority to bypass these deterministic boundaries.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            disabled={saving}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-white border border-[#E5E7EB] hover:bg-[#F3F4F6] text-[#4B5563] rounded-xl text-xs font-bold shadow-2xs transition-all disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset Defaults
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl text-xs font-bold shadow-xs transition-all disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Active Rules
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 bg-[#ECFDF5] border border-[#A7F3D0] rounded-2xl flex items-center gap-3 text-[#065F46] text-xs font-bold">
          <CheckCircle className="w-4 h-4 text-[#10B981] shrink-0" />
          {message}
        </div>
      )}

      {error && (
        <div className="p-4 bg-[#FEF2F2] border border-[#FECACA] rounded-2xl flex items-center gap-3 text-[#DC2626] text-xs font-bold">
          <AlertCircle className="w-4 h-4 text-[#EF4444] shrink-0" />
          {error}
        </div>
      )}

      {/* Rules Config List */}
      <div className="premium-card p-6 space-y-6 divide-y divide-[#F3F4F6]">
        {/* Rule 1: Max Payment Retries */}
        <div className="pt-4 first:pt-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="max-w-md">
            <p className="text-sm font-bold text-[#0B132B]">Maximum Automated Payment Retries</p>
            <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed font-medium">
              Maximum retry attempts allowed on failed transactions before halting automation.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={5}
              value={policies.MAX_PAYMENT_RETRIES}
              onChange={e => setPolicies({ ...policies, MAX_PAYMENT_RETRIES: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-black text-[#0B132B] text-center font-mono focus:outline-none focus:border-[#6366F1]"
            />
            <span className="text-xs font-bold text-[#6B7280]">retries max</span>
          </div>
        </div>

        {/* Rule 2: Max Messages */}
        <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="max-w-md">
            <p className="text-sm font-bold text-[#0B132B]">Maximum Communication Messages</p>
            <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed font-medium">
              Caps total recovery reminders/links per case to prevent spamming customers.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={1}
              max={6}
              value={policies.MAX_MESSAGES}
              onChange={e => setPolicies({ ...policies, MAX_MESSAGES: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-black text-[#0B132B] text-center font-mono focus:outline-none focus:border-[#6366F1]"
            />
            <span className="text-xs font-bold text-[#6B7280]">messages max</span>
          </div>
        </div>

        {/* Rule 3: High Value Approval Threshold */}
        <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="max-w-md">
            <p className="text-sm font-bold text-[#0B132B]">High-Value Human Approval Threshold (₹ INR)</p>
            <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed font-medium">
              Transactions exceeding this amount require explicit human approval before execution.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              step={10000}
              value={policies.HIGH_VALUE_THRESHOLD_INR}
              onChange={e => setPolicies({ ...policies, HIGH_VALUE_THRESHOLD_INR: Number(e.target.value) })}
              className="w-36 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-black text-[#0B132B] text-center font-mono focus:outline-none focus:border-[#6366F1]"
            />
            <span className="text-xs font-bold text-[#6B7280]">₹ threshold</span>
          </div>
        </div>

        {/* Rule 4: Min AI Confidence Threshold */}
        <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="max-w-md">
            <p className="text-sm font-bold text-[#0B132B]">Minimum AI Confidence for Autonomous Action</p>
            <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed font-medium">
              If AI diagnosis confidence is below this percentage, automation halts and escalates to human.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0.1}
              max={0.95}
              step={0.05}
              value={policies.MIN_AI_CONFIDENCE_FOR_AUTO_ACTION}
              onChange={e => setPolicies({ ...policies, MIN_AI_CONFIDENCE_FOR_AUTO_ACTION: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-black text-[#0B132B] text-center font-mono focus:outline-none focus:border-[#6366F1]"
            />
            <span className="text-xs font-bold text-[#6B7280]">{(policies.MIN_AI_CONFIDENCE_FOR_AUTO_ACTION * 100).toFixed(0)}% min</span>
          </div>
        </div>

        {/* Rule 5: Max Discount Cap */}
        <div className="pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="max-w-md">
            <p className="text-sm font-bold text-[#0B132B]">Maximum Autonomous Discount Cap</p>
            <p className="text-xs text-[#6B7280] mt-0.5 leading-relaxed font-medium">
              Limits the maximum percentage discount the AI can offer to win back cart abandonments.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="number"
              min={0}
              max={30}
              value={policies.MAX_DISCOUNT_PERCENT}
              onChange={e => setPolicies({ ...policies, MAX_DISCOUNT_PERCENT: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-black text-[#0B132B] text-center font-mono focus:outline-none focus:border-[#6366F1]"
            />
            <span className="text-xs font-bold text-[#6B7280]">% max discount</span>
          </div>
        </div>
      </div>
    </div>
  );
}
