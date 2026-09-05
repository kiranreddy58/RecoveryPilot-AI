import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Radio, Send, Loader2, CheckCircle, ArrowRight, Zap, Code, AlertTriangle } from 'lucide-react';
import { razorpayApi, SimulateWebhookResponse } from '../api/razorpayApi';

const PRESET_EVENTS = [
  {
    event_type: 'payment.failed',
    label: '💳 payment.failed (Card/UPI Timeout)',
    default_amount: 18500,
    desc: 'Simulates a Razorpay ₹18,500 UPI/Card payment failure with bank timeout error.',
    category: 'PAYMENT_FAILURE',
  },
  {
    event_type: 'checkout.abandoned',
    label: '🛒 checkout.abandoned (Cart Drop-off)',
    default_amount: 6200,
    desc: 'Simulates a Razorpay Standard/Magic Checkout abandonment on payment screen.',
    category: 'CHECKOUT_ABANDONMENT',
  },
  {
    event_type: 'invoice.expired',
    label: '📄 invoice.expired (B2B Receivable)',
    default_amount: 145000,
    desc: 'Simulates a high-value B2B invoice (> ₹1,00,000) overdue past due date.',
    category: 'OVERDUE_RECEIVABLE',
  },
  {
    event_type: 'subscription.halted',
    label: '🔄 subscription.halted (Recurring SaaS Mandate)',
    default_amount: 2499,
    desc: 'Simulates a recurring subscription auto-debit failure on NACH/Card mandate.',
    category: 'SUBSCRIPTION_FAILURE',
  },
  {
    event_type: 'promise_to_pay.broken',
    label: '🤝 promise_to_pay.broken (Customer Promise Lapsed)',
    default_amount: 45000,
    desc: 'Simulates a broken customer promise-to-pay date triggering urgent recovery.',
    category: 'PROMISE_TO_PAY_BROKEN',
  },
];

export function WebhookSimulator() {
  const [selectedPreset, setSelectedPreset] = useState(PRESET_EVENTS[0]);
  const [amount, setAmount] = useState(PRESET_EVENTS[0].default_amount);
  const [merchantId, setMerchantId] = useState('MERCHANT_RAZORPAY_INDIA');
  const [customerId, setCustomerId] = useState('CUST_RAZORPAY_881');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<SimulateWebhookResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSelectPreset = (preset: typeof PRESET_EVENTS[0]) => {
    setSelectedPreset(preset);
    setAmount(preset.default_amount);
  };

  const handleDispatch = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await razorpayApi.simulateWebhook({
        event_type: selectedPreset.event_type,
        amount: Number(amount),
        currency: 'INR',
        merchant_id: merchantId,
        customer_id: customerId,
      });
      setResponse(res);
    } catch (e: any) {
      setError(e.message || 'Webhook simulation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#EEF2FF] border border-[#C7D2FE] rounded-full text-xs font-bold text-[#4F46E5] mb-2 shadow-2xs">
          <Radio className="w-3.5 h-3.5 animate-pulse text-[#6366F1]" /> NATIVE RAZORPAY WEBHOOK INTEGRATION
        </div>
        <h1 className="text-3xl font-extrabold text-[#0B132B] tracking-tight">Razorpay Webhook Simulator</h1>
        <p className="text-[#4B5563] text-sm font-medium mt-1 max-w-3xl">
          Test real-time webhook ingestion and observe the bounded autonomous recovery engine close the loop from event ingestion to measured money recovery.
        </p>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Preset Selector & Config */}
        <div className="lg:col-span-5 space-y-5">
          <div className="premium-card p-6 space-y-4">
            <h2 className="text-[#0B132B] font-bold text-sm uppercase tracking-wider pb-2 border-b border-[#F3F4F6]">
              1. Select Razorpay Webhook Event
            </h2>
            <div className="space-y-2.5">
              {PRESET_EVENTS.map(preset => (
                <button
                  key={preset.event_type}
                  onClick={() => handleSelectPreset(preset)}
                  className={`w-full text-left p-3.5 rounded-xl border text-xs font-bold transition-all shadow-2xs ${
                    selectedPreset.event_type === preset.event_type
                      ? 'border-[#6366F1] bg-[#EEF2FF] text-[#4338CA]'
                      : 'border-[#E5E7EB] bg-white text-[#4B5563] hover:bg-[#F9FAFB]'
                  }`}
                >
                  <p className="font-extrabold text-[#0B132B] text-xs">{preset.label}</p>
                  <p className="text-[11px] text-[#6B7280] font-normal mt-1 leading-snug">{preset.desc}</p>
                </button>
              ))}
            </div>

            <div className="pt-2 border-t border-[#F3F4F6] space-y-3">
              <div>
                <label className="text-xs font-bold text-[#4B5563] uppercase">Transaction Amount (₹ INR)</label>
                <input
                  type="number"
                  value={amount}
                  onChange={e => setAmount(Number(e.target.value))}
                  className="w-full mt-1 px-3.5 py-2 bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl text-sm font-bold text-[#0B132B] focus:outline-none focus:border-[#6366F1]"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-[#6B7280] uppercase">Merchant ID</label>
                  <input
                    type="text"
                    value={merchantId}
                    onChange={e => setMerchantId(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg text-xs font-mono text-[#0B132B]"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-bold text-[#6B7280] uppercase">Customer ID</label>
                  <input
                    type="text"
                    value={customerId}
                    onChange={e => setCustomerId(e.target.value)}
                    className="w-full mt-1 px-3 py-1.5 bg-[#F9FAFB] border border-[#E5E7EB] rounded-lg text-xs font-mono text-[#0B132B]"
                  />
                </div>
              </div>
            </div>

            <button
              onClick={handleDispatch}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl font-bold text-sm shadow-md shadow-[#6366F1]/25 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              Dispatch Razorpay Webhook Event
            </button>
          </div>
        </div>

        {/* Right Panel: Live Pipeline Execution & JSON Response */}
        <div className="lg:col-span-7 space-y-5">
          {error && (
            <div className="p-4 bg-[#FEF2F2] border border-[#FECACA] rounded-2xl flex items-center gap-3 text-[#DC2626] text-xs font-bold">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              {error}
            </div>
          )}

          {response ? (
            <div className="space-y-5 animate-fade-in-up">
              {/* Outcome Banner */}
              <div className="premium-card p-6 border-[#A7F3D0] bg-[#ECFDF5]/50">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] flex items-center justify-center">
                      <CheckCircle className="w-6 h-6 text-[#10B981]" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[#047857] uppercase tracking-wider">Webhook Processed Successfully</p>
                      <h3 className="text-lg font-black text-[#0B132B]">
                        Created Case: <span className="font-mono text-[#4F46E5]">{response.case_id}</span>
                      </h3>
                    </div>
                  </div>
                  {response.case_id && (
                    <Link
                      to={`/cases/${response.case_id}`}
                      className="flex items-center gap-1 text-xs font-bold px-3 py-1.5 bg-[#10B981] text-white rounded-xl shadow-xs hover:bg-[#059669] transition-all"
                    >
                      View Case <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  )}
                </div>

                {/* Workflow Summary */}
                {response.workflow_result && (
                  <div className="grid grid-cols-3 gap-3 mt-4 text-xs font-bold">
                    <div className="bg-white p-3 rounded-xl border border-[#E5E7EB] shadow-2xs">
                      <p className="text-[#6B7280] text-[10px] uppercase">Final State</p>
                      <p className="text-[#0B132B] font-extrabold mt-0.5">{response.workflow_result.final_status}</p>
                    </div>
                    <div className="bg-white p-3 rounded-xl border border-[#E5E7EB] shadow-2xs">
                      <p className="text-[#6B7280] text-[10px] uppercase">Recovered Money</p>
                      <p className="text-[#059669] font-extrabold mt-0.5">
                        ₹{(response.workflow_result.recovered_amount || 0).toLocaleString('en-IN')}
                      </p>
                    </div>
                    <div className="bg-white p-3 rounded-xl border border-[#E5E7EB] shadow-2xs">
                      <p className="text-[#6B7280] text-[10px] uppercase">Steps Closed</p>
                      <p className="text-[#6366F1] font-extrabold mt-0.5">
                        {response.workflow_result.steps?.length || 0} stages
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Payload Viewer */}
              <div className="premium-card p-5">
                <div className="flex items-center gap-2 mb-3 text-xs font-bold text-[#0B132B]">
                  <Code className="w-4 h-4 text-[#6366F1]" /> Ingested Webhook Payload & Signature Metadata
                </div>
                <pre className="p-4 bg-[#0B132B] text-[#A7F3D0] rounded-xl text-xs font-mono overflow-x-auto max-h-64">
                  {JSON.stringify(response.simulated_payload, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="premium-card p-12 text-center border-dashed border-[#CBD5E1]">
              <Zap className="w-10 h-10 text-[#6366F1] mx-auto mb-3 opacity-60" />
              <h3 className="text-[#0B132B] font-bold text-base">Awaiting Webhook Dispatch</h3>
              <p className="text-[#6B7280] text-xs mt-1 max-w-sm mx-auto">
                Select an event preset on the left and click "Dispatch Razorpay Webhook Event" to witness bounded recovery.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
