import { BackendStatus } from '../../types';

interface StatusIndicatorProps {
  label: string;
  status: BackendStatus | 'ONLINE';
}

const statusConfig: Record<string, { color: string; bgColor: string; text: string }> = {
  ONLINE: { color: 'bg-emerald-400', bgColor: 'bg-emerald-400/10 border-emerald-400/20', text: 'text-emerald-400' },
  OFFLINE: { color: 'bg-red-400', bgColor: 'bg-red-400/10 border-red-400/20', text: 'text-red-400' },
  CONNECTING: { color: 'bg-amber-400', bgColor: 'bg-amber-400/10 border-amber-400/20', text: 'text-amber-400' },
};

export function StatusIndicator({ label, status }: StatusIndicatorProps) {
  const config = statusConfig[status] || statusConfig.CONNECTING;

  return (
    <div className={`flex items-center justify-between px-5 py-4 rounded-xl border ${config.bgColor}`}>
      <span className="text-slate-300 text-sm font-medium">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`relative flex h-2.5 w-2.5`}>
          {status === 'CONNECTING' && (
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.color} opacity-75`}></span>
          )}
          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${config.color}`}></span>
        </span>
        <span className={`text-sm font-semibold ${config.text}`}>{status}</span>
      </div>
    </div>
  );
}
