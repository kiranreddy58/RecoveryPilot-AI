interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

const STATUS_CONFIG: Record<string, { color: string; dot: string; label?: string }> = {
  DETECTED:         { color: 'text-[#D97706] bg-[#FEF3C7] border-[#FDE68A]', dot: 'bg-[#F59E0B]' },
  ANALYZING:        { color: 'text-[#6366F1] bg-[#EEF2FF] border-[#E0E7FF]', dot: 'bg-[#6366F1]' },
  DIAGNOSED:        { color: 'text-[#4F46E5] bg-[#EEF2FF] border-[#C7D2FE]', dot: 'bg-[#6366F1]' },
  STRATEGY_SELECTED:{ color: 'text-[#7C3AED] bg-[#F5F3FF] border-[#DDD6FE]', dot: 'bg-[#8B5CF6]', label: 'STRATEGY' },
  GUARDIAN_REVIEW:  { color: 'text-[#D97706] bg-[#FFFBEB] border-[#FDE68A]', dot: 'bg-[#F59E0B]', label: 'GUARDIAN' },
  APPROVED:         { color: 'text-[#059669] bg-[#ECFDF5] border-[#A7F3D0]', dot: 'bg-[#10B981]' },
  BLOCKED:          { color: 'text-[#DC2626] bg-[#FEF2F2] border-[#FECACA]', dot: 'bg-[#EF4444]' },
  EXECUTING:        { color: 'text-[#4F46E5] bg-[#EEF2FF] border-[#C7D2FE]', dot: 'bg-[#6366F1]' },
  VERIFYING:        { color: 'text-[#7C3AED] bg-[#F5F3FF] border-[#DDD6FE]', dot: 'bg-[#8B5CF6]' },
  RECOVERED:        { color: 'text-[#059669] bg-[#ECFDF5] border-[#A7F3D0]', dot: 'bg-[#10B981]' },
  CLOSED:           { color: 'text-[#047857] bg-[#ECFDF5] border-[#6EE7B7]', dot: 'bg-[#10B981]' },
  FAILED:           { color: 'text-[#B91C1C] bg-[#FEF2F2] border-[#FCA5A5]', dot: 'bg-[#EF4444]' },
  ESCALATED:        { color: 'text-[#B45309] bg-[#FEF3C7] border-[#FCD34D]', dot: 'bg-[#F59E0B]' },
  STOPPED:          { color: 'text-[#4B5563] bg-[#F3F4F6] border-[#E5E7EB]', dot: 'bg-[#9CA3AF]' },
  // Risk
  LOW:    { color: 'text-[#059669] bg-[#ECFDF5] border-[#A7F3D0]', dot: 'bg-[#10B981]' },
  MEDIUM: { color: 'text-[#D97706] bg-[#FEF3C7] border-[#FDE68A]', dot: 'bg-[#F59E0B]' },
  HIGH:   { color: 'text-[#EA580C] bg-[#FFF7ED] border-[#FFEDD5]', dot: 'bg-[#F97316]' },
  CRITICAL: { color: 'text-[#DC2626] bg-[#FEF2F2] border-[#FECACA]', dot: 'bg-[#EF4444]' },
};

const DEFAULT = { color: 'text-[#4B5563] bg-[#F3F4F6] border-[#E5E7EB]', dot: 'bg-[#9CA3AF]' };

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const cfg = STATUS_CONFIG[status] || DEFAULT;
  const label = cfg.label || status.replace(/_/g, ' ');
  const textSize = size === 'md' ? 'text-sm px-3 py-1' : 'text-xs px-2.5 py-0.5';

  return (
    <span className={`inline-flex items-center gap-1.5 ${textSize} font-semibold rounded-full border ${cfg.color} shadow-2xs`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${['DETECTED','ANALYZING','EXECUTING'].includes(status) ? 'pulse-dot' : ''}`} />
      {label}
    </span>
  );
}

export function GuardianBadge({ decision }: { decision: string }) {
  const map: Record<string, { color: string; label: string }> = {
    APPROVED: { color: 'text-[#059669] bg-[#ECFDF5] border-[#A7F3D0]', label: '✓ APPROVED' },
    BLOCKED: { color: 'text-[#DC2626] bg-[#FEF2F2] border-[#FECACA]', label: '✕ BLOCKED' },
    HUMAN_APPROVAL_REQUIRED: { color: 'text-[#B45309] bg-[#FEF3C7] border-[#FCD34D]', label: '⚠ HUMAN REQUIRED' },
    MANUALLY_APPROVED: { color: 'text-[#0D9488] bg-[#F0FDFA] border-[#99F6E4]', label: '✓ MANUALLY APPROVED' },
    PENDING: { color: 'text-[#4B5563] bg-[#F3F4F6] border-[#E5E7EB]', label: '— PENDING' },
  };
  const cfg = map[decision] || map['PENDING'];
  return (
    <span className={`inline-flex items-center px-3 py-1 text-xs font-bold rounded-full border ${cfg.color} shadow-2xs`}>
      {cfg.label}
    </span>
  );
}
