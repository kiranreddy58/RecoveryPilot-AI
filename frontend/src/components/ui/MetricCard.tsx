import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
  trend?: { value: number; positive: boolean };
  glowClass?: string;
  delay?: number;
}

export function MetricCard({
  label, value, sub, icon: Icon,
  iconColor = 'text-[#10B981]',
  bgColor = 'bg-[#10B981]/10',
  trend, delay = 0
}: MetricCardProps) {
  return (
    <div
      className="premium-card p-6 animate-fade-in-up group cursor-default"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 ${bgColor} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 shadow-xs`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        {trend && (
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
            trend.positive ? 'text-[#059669] bg-[#ECFDF5] border border-[#A7F3D0]' : 'text-[#DC2626] bg-[#FEF2F2] border border-[#FECACA]'
          }`}>
            {trend.positive ? '↑' : '↓'} {trend.value}%
          </span>
        )}
      </div>
      <div className="space-y-1">
        <p className="text-[#4B5563] text-xs font-semibold uppercase tracking-wider">{label}</p>
        <p className="text-2xl lg:text-3xl font-extrabold text-[#0B132B] tracking-tight">{value}</p>
        {sub && <p className="text-[#6B7280] text-xs font-medium">{sub}</p>}
      </div>
    </div>
  );
}

interface MiniMetricProps {
  label: string;
  value: string | number;
  color?: string;
}

export function MiniMetric({ label, value, color = 'text-[#0B132B]' }: MiniMetricProps) {
  return (
    <div className="flex justify-between items-center py-2.5 border-b border-[#F3F4F6] last:border-0">
      <span className="text-[#4B5563] text-sm font-medium">{label}</span>
      <span className={`text-sm font-bold ${color}`}>{value}</span>
    </div>
  );
}
