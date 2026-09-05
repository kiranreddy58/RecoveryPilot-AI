import { useState, useEffect } from 'react';
import { X, ShieldCheck, CheckCircle2, Lock, Printer, Award } from 'lucide-react';
import { api } from '../../api/client';

const INR = (v: number) =>
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(v);

interface ActionReceiptModalProps {
  receipt: any;
  isOpen: boolean;
  onClose: () => void;
}

export function ActionReceiptModal({ receipt, isOpen, onClose }: ActionReceiptModalProps) {
  const [copied, setCopied] = useState(false);
  const [auditVerification, setAuditVerification] = useState<any>(null);

  useEffect(() => {
    if (isOpen && receipt?.case_id) {
      verifyAuditChain(receipt.case_id);
    }
  }, [isOpen, receipt]);

  const verifyAuditChain = async (caseId: string) => {
    try {
      const res: any = await api.get(`/cases/${caseId}/verify-audit`);
      setAuditVerification(res);
    } catch (e) {
      console.error('Audit verification error', e);
    }
  };

  if (!isOpen || !receipt) return null;

  const copyHash = () => {
    if (receipt.compliance_hash) {
      navigator.clipboard.writeText(receipt.compliance_hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0B132B]/60 backdrop-blur-xs animate-fade-in">
      <div className="relative w-full max-w-2xl bg-white border border-[#E5E7EB] rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Modal Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E7EB] bg-[#F9FAFB]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#6366F1]" />
            <span className="text-sm font-extrabold text-[#0B132B]">AI Action Receipt & Policy Verification Record</span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#6B7280] hover:text-[#0B132B] hover:bg-[#E5E7EB] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Certificate Body (Printable Area) */}
        <div className="p-6 md:p-8 overflow-y-auto space-y-6">
          {/* Certificate Title Badge */}
          <div className="text-center pb-5 border-b border-[#E5E7EB]">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EEF2FF] border border-[#C7D2FE] rounded-full text-xs font-bold text-[#4F46E5] mb-2 shadow-2xs">
              <Award className="w-3.5 h-3.5" /> POLICY VERIFICATION RESULT
            </div>
            <h2 className="text-2xl font-black text-[#0B132B] tracking-tight">Autonomous Recovery Action Record</h2>
            <p className="text-xs text-[#6B7280] font-mono mt-1">
              Record ID: <span className="font-bold text-[#0B132B]">{receipt.certificate_id || `REC-${receipt.case_id}`}</span>
            </p>
          </div>

          {/* Core Case Information Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#F9FAFB] p-4 rounded-2xl border border-[#E5E7EB]">
            <div>
              <p className="text-[11px] font-bold text-[#6B7280] uppercase">Case ID</p>
              <p className="text-xs font-black text-[#0B132B] font-mono mt-0.5">{receipt.case_id}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-[#6B7280] uppercase">Merchant ID</p>
              <p className="text-xs font-bold text-[#0B132B] font-mono mt-0.5 truncate">{receipt.merchant_id}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-[#6B7280] uppercase">Revenue at Risk</p>
              <p className="text-xs font-black text-[#D97706] mt-0.5">{INR(receipt.revenue_at_risk || 0)}</p>
            </div>
            <div>
              <p className="text-[11px] font-bold text-[#6B7280] uppercase">Measured Recovered</p>
              <p className="text-xs font-black text-[#059669] mt-0.5">{INR(receipt.money_recovered || 0)}</p>
            </div>
          </div>

          {/* AI Root Cause & Confidence */}
          <div className="p-4 bg-[#EEF2FF]/60 border border-[#C7D2FE] rounded-2xl">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-extrabold text-[#4338CA] uppercase tracking-wider">AI Root Cause Diagnosis</p>
                <p className="text-sm font-bold text-[#0B132B] mt-1">{receipt.root_cause || 'Pattern Analysis Diagnosed'}</p>
              </div>
              <span className="px-2.5 py-1 bg-white border border-[#C7D2FE] rounded-lg text-xs font-black text-[#4F46E5] shadow-2xs shrink-0">
                Confidence Estimate: {receipt.ai_confidence_formatted || `${((receipt.ai_confidence || 0.85) * 100).toFixed(0)}%`}
              </span>
            </div>
          </div>

          {/* Counterfactual Evaluation Matrix */}
          {receipt.strategies_matrix && receipt.strategies_matrix.length > 0 && (
            <div>
              <div className="flex justify-between items-center mb-2">
                <p className="text-xs font-extrabold text-[#0B132B] uppercase tracking-wider">
                  Counterfactual Net Value Simulation
                </p>
                <span className="text-[10px] text-[#6B7280] font-mono">E[Net] = P(Success) × Amount − Cost − Discount</span>
              </div>
              <div className="border border-[#E5E7EB] rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-[#F9FAFB] border-b border-[#E5E7EB] text-[#4B5563] font-bold">
                    <tr>
                      <th className="text-left px-3 py-2">Strategy Candidate</th>
                      <th className="text-right px-3 py-2">Est. Success %</th>
                      <th className="text-right px-3 py-2">Net Value</th>
                      <th className="text-right px-3 py-2">Decision</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#F3F4F6]">
                    {receipt.strategies_matrix.map((s: any, idx: number) => (
                      <tr key={idx} className={s.is_selected ? 'bg-[#ECFDF5]/80 font-bold' : ''}>
                        <td className="px-3 py-2 text-[#0B132B]">{s.label || s.name}</td>
                        <td className="px-3 py-2 text-right text-[#059669]">{((s.probability || 0) * 100).toFixed(0)}%</td>
                        <td className="px-3 py-2 text-right text-[#0B132B]">{INR(s.expected_net_recovery || 0)}</td>
                        <td className="px-3 py-2 text-right">
                          {s.is_selected ? (
                            <span className="text-[10px] bg-[#10B981] text-white px-2 py-0.5 rounded-full font-black">SELECTED</span>
                          ) : (
                            <span className="text-[10px] text-[#9CA3AF]">REJECTED</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Policy Guardian Validation */}
          <div className="p-4 bg-[#ECFDF5] border border-[#A7F3D0] rounded-2xl">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-[#10B981]" />
              <p className="text-xs font-black text-[#065F46] uppercase">Deterministic Policy Guardian Review</p>
            </div>
            <p className="text-xs text-[#047857] font-medium mb-2">
              Action <span className="font-bold font-mono">{receipt.selected_strategy}</span> evaluated against hard stopping and bounding rules.
            </p>
            {receipt.policy_checks_passed && (
              <div className="flex flex-wrap gap-1.5">
                {receipt.policy_checks_passed.map((chk: string) => (
                  <span key={chk} className="text-[10px] font-bold bg-white text-[#059669] px-2 py-0.5 rounded border border-[#A7F3D0] shadow-2xs">
                    ✓ {chk}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Cryptographic Proof & Hash Chain Status */}
          <div className="p-4 bg-[#F9FAFB] border border-[#E5E7EB] rounded-2xl space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#6366F1]" />
                <p className="text-xs font-bold text-[#0B132B]">Tamper-Evident SHA-256 Event Chain</p>
              </div>
              {auditVerification && (
                <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                  auditVerification.tamper_detected
                    ? 'bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]'
                    : 'bg-[#ECFDF5] text-[#059669] border-[#A7F3D0]'
                }`}>
                  {auditVerification.tamper_detected ? '⚠️ TAMPER DETECTED' : `✓ CHAIN VERIFIED (${auditVerification.events_count || 0} events)`}
                </span>
              )}
            </div>
            <div className="p-2.5 bg-white border border-[#E5E7EB] rounded-xl flex items-center justify-between text-xs font-mono">
              <div className="truncate mr-2">
                <p className="text-[10px] text-[#6B7280] uppercase font-bold">Latest Immutable Block Hash</p>
                <p className="text-[#0B132B] font-bold truncate">{auditVerification?.latest_block_hash || receipt.compliance_hash}</p>
              </div>
              <button
                onClick={copyHash}
                className="px-2.5 py-1 text-[11px] font-bold bg-[#F9FAFB] border border-[#E5E7EB] hover:bg-[#F3F4F6] rounded-lg text-[#0B132B] shrink-0"
              >
                {copied ? '✓ Copied' : 'Copy Hash'}
              </button>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#E5E7EB] bg-[#F9FAFB]">
          <span className="text-xs text-[#6B7280] font-medium">Policy-Governed Record — RecoveryPilot AI</span>
          <div className="flex gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 px-4 py-2 bg-white border border-[#E5E7EB] hover:bg-[#F3F4F6] text-[#0B132B] rounded-xl text-xs font-bold shadow-2xs transition-all"
            >
              <Printer className="w-3.5 h-3.5" /> Print Record
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl text-xs font-bold shadow-xs transition-all"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
