import { useState, useEffect } from 'react';
import { X, Play, Pause, SkipForward, RotateCcw, Clock, Lock, ArrowRight } from 'lucide-react';
import { CaseAuditEvent } from '../../types';
import { StatusBadge } from './StatusBadge';

interface RecoveryReplayModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  auditEvents: CaseAuditEvent[];
}

export function RecoveryReplayModal({ isOpen, onClose, caseId, auditEvents }: RecoveryReplayModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setCurrentStep(0);
      setIsPlaying(false);
    }
  }, [isOpen]);

  useEffect(() => {
    let timer: any;
    if (isPlaying && currentStep < auditEvents.length - 1) {
      timer = setTimeout(() => {
        setCurrentStep(prev => prev + 1);
      }, 1500);
    } else if (currentStep >= auditEvents.length - 1) {
      setIsPlaying(false);
    }
    return () => clearTimeout(timer);
  }, [isPlaying, currentStep, auditEvents.length]);

  if (!isOpen) return null;

  const currentEvent = auditEvents[currentStep];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#0B132B]/60 backdrop-blur-xs animate-fade-in">
      <div className="relative w-full max-w-2xl bg-white border border-[#E5E7EB] rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E7EB] bg-[#F9FAFB]">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-[#6366F1]" />
            <span className="text-sm font-extrabold text-[#0B132B]">Lifecycle Event Replay: <span className="font-mono">{caseId}</span></span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#6B7280] hover:text-[#0B132B] hover:bg-[#E5E7EB] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Replay Stepper Viewport */}
        <div className="p-6 md:p-8 space-y-6 overflow-y-auto">
          {/* Step Counter Bar */}
          <div className="flex items-center justify-between text-xs font-bold text-[#6B7280]">
            <span>Audit Stage {currentStep + 1} of {auditEvents.length || 1}</span>
            <span>{currentEvent ? new Date(currentEvent.created_at).toLocaleTimeString('en-IN') : ''}</span>
          </div>

          {/* Stepper Progress Bar */}
          <div className="h-2 bg-[#F3F4F6] rounded-full overflow-hidden border border-[#E5E7EB]">
            <div
              className="h-full bg-gradient-to-r from-[#6366F1] to-[#10B981] transition-all duration-500 rounded-full"
              style={{ width: `${auditEvents.length > 0 ? ((currentStep + 1) / auditEvents.length) * 100 : 0}%` }}
            />
          </div>

          {/* Active Event Card */}
          {currentEvent ? (
            <div className="premium-card p-6 border-[#6366F1]/30 bg-[#F9FAFB] space-y-4 animate-fade-in">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-black px-2.5 py-0.5 rounded-full bg-[#EEF2FF] text-[#4F46E5] border border-[#C7D2FE] uppercase">
                    {currentEvent.actor_type} • {currentEvent.actor_id}
                  </span>
                  <h3 className="text-lg font-black text-[#0B132B] mt-2">{currentEvent.event_type}</h3>
                </div>
                <div className="flex items-center gap-2">
                  {currentEvent.previous_state && (
                    <>
                      <StatusBadge status={currentEvent.previous_state} />
                      <ArrowRight className="w-3.5 h-3.5 text-[#9CA3AF]" />
                    </>
                  )}
                  <StatusBadge status={currentEvent.new_state} />
                </div>
              </div>

              {/* Rationale description */}
              <div className="p-3.5 bg-white border border-[#E5E7EB] rounded-xl">
                <p className="text-xs font-bold text-[#6B7280] uppercase tracking-wider mb-1">Audit Log Rationale</p>
                <p className="text-sm font-semibold text-[#0B132B] leading-relaxed">
                  {currentEvent.reason || 'State transition recorded into deterministic audit log.'}
                </p>
              </div>

              {/* Cryptographic Link Hash */}
              {(currentEvent.previous_event_hash || currentEvent.current_event_hash) && (
                <div className="p-3 bg-[#EEF2FF]/60 border border-[#C7D2FE] rounded-xl text-[11px] font-mono space-y-1">
                  <div className="flex items-center gap-1.5 text-[#4338CA] font-bold">
                    <Lock className="w-3.5 h-3.5" /> Immutable Hash Chain Link
                  </div>
                  <p className="text-[#6B7280] truncate">
                    Prev Hash: <span className="font-bold text-[#0B132B]">{currentEvent.previous_event_hash ? currentEvent.previous_event_hash.slice(0, 16) + '...' : 'GENESIS'}</span>
                  </p>
                  <p className="text-[#6B7280] truncate">
                    Event Hash: <span className="font-bold text-[#0B132B]">{currentEvent.current_event_hash ? currentEvent.current_event_hash.slice(0, 16) + '...' : '—'}</span>
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-[#6B7280] text-sm py-8">No audit events to replay.</p>
          )}
        </div>

        {/* Player Controls Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-[#E5E7EB] bg-[#F9FAFB]">
          <button
            onClick={() => { setCurrentStep(0); setIsPlaying(false); }}
            className="flex items-center gap-1 text-xs font-bold text-[#6B7280] hover:text-[#0B132B] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
              disabled={currentStep === 0}
              className="px-3 py-1.5 bg-white border border-[#E5E7EB] hover:bg-[#F3F4F6] text-[#0B132B] rounded-xl text-xs font-bold transition-all disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              disabled={currentStep >= auditEvents.length - 1 && !isPlaying}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl text-xs font-bold shadow-xs transition-all disabled:opacity-40"
            >
              {isPlaying ? <><Pause className="w-3.5 h-3.5" /> Pause</> : <><Play className="w-3.5 h-3.5" /> Auto-Play</>}
            </button>
            <button
              onClick={() => setCurrentStep(prev => Math.min(auditEvents.length - 1, prev + 1))}
              disabled={currentStep >= auditEvents.length - 1}
              className="px-3 py-1.5 bg-white border border-[#E5E7EB] hover:bg-[#F3F4F6] text-[#0B132B] rounded-xl text-xs font-bold transition-all disabled:opacity-40"
            >
              Next <SkipForward className="w-3.5 h-3.5 inline ml-0.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
