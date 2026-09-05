import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, FolderOpen, PlayCircle, Database,
  CheckSquare, Activity, Shield, Radio, Calculator, Lock
} from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/cases', label: 'Cases', icon: FolderOpen },
  { to: '/approval-queue', label: 'Approval Queue', icon: CheckSquare },
  { to: '/webhooks', label: 'Razorpay Webhooks', icon: Radio },
  { to: '/demo', label: 'Demo Mode', icon: PlayCircle },
  { to: '/batch', label: 'Batch Test', icon: Database },
  { to: '/roi-calculator', label: 'ROI Calculator', icon: Calculator },
  { to: '/policy-config', label: 'Policy Rules', icon: Lock },
];

export function Header() {
  return (
    <header className="bg-[#FFFFFF]/95 backdrop-blur-md border-b border-[#E5E7EB] sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3 group shrink-0">
            <div className="relative">
              <div className="w-9 h-9 bg-gradient-to-br from-[#0B132B] to-[#1E293B] rounded-xl flex items-center justify-center shadow-md shadow-[#0B132B]/10 group-hover:scale-105 transition-transform">
                <Shield className="w-5 h-5 text-[#6366F1]" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-[#10B981] rounded-full border-2 border-white pulse-dot" />
            </div>
            <div>
              <h1 className="text-[#0B132B] font-bold text-base leading-tight tracking-tight">RecoveryPilot AI</h1>
              <p className="text-[#4B5563] text-[10px] font-medium tracking-wider uppercase">Revenue Recovery Control Tower</p>
            </div>
          </NavLink>

          {/* Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all duration-200 ${
                    isActive
                      ? 'bg-[#6366F1]/10 text-[#6366F1] shadow-2xs'
                      : 'text-[#4B5563] hover:text-[#0B132B] hover:bg-[#F3F4F6]'
                  }`
                }
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Status badge */}
          <div className="flex items-center gap-2 px-2.5 py-1 bg-[#10B981]/10 border border-[#10B981]/20 rounded-full text-xs font-semibold text-[#10B981] shrink-0">
            <Activity className="w-3.5 h-3.5 pulse-dot" />
            <span className="hidden sm:block">Control Tower Live</span>
          </div>
        </div>

        {/* Mobile / Tablet Horizontal Navigation Scroll */}
        <nav className="flex lg:hidden items-center gap-2 overflow-x-auto py-2 border-t border-[#F3F4F6] scrollbar-none">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-[#6366F1]/10 text-[#6366F1]'
                    : 'text-[#4B5563] hover:bg-[#F3F4F6]'
                }`
              }
            >
              <Icon className="w-3 h-3" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}
