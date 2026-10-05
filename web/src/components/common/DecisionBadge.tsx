import React from 'react';
import { CheckCircle2, AlertTriangle, ShieldAlert, ArrowUpRight, CheckCheck, XCircle } from 'lucide-react';
import { GovernanceDecision } from '../../types';

interface DecisionBadgeProps {
  decision?: GovernanceDecision | string | null;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({
  decision = 'APPROVE',
  size = 'md',
  showIcon = true,
}) => {
  const dec = (decision || '').toUpperCase();

  let colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-emerald-glow';
  let label = 'APPROVED';
  let Icon = CheckCircle2;

  if (dec.includes('FLAG')) {
    colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/40 shadow-amber-glow';
    label = 'FLAGGED FOR REVIEW';
    Icon = AlertTriangle;
  } else if (dec.includes('BLOCK') || dec.includes('REJECT')) {
    colorClasses = 'bg-rose-500/10 text-rose-400 border-rose-500/40 shadow-rose-glow';
    label = 'POLICY BLOCKED';
    Icon = ShieldAlert;
  } else if (dec.includes('EXCEPTION')) {
    colorClasses = 'bg-emerald-500/15 text-emerald-300 border-emerald-400/50 shadow-emerald-glow';
    label = 'APPROVED W/ EXCEPTION';
    Icon = CheckCheck;
  } else if (dec.includes('ESCALAT')) {
    colorClasses = 'bg-sky-500/10 text-sky-400 border-sky-500/40 shadow-ice-glow';
    label = 'HUMAN ESCALATION';
    Icon = ArrowUpRight;
  }

  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono font-medium rounded-full border transition-all duration-200 ${colorClasses} ${sizeClasses}`}
    >
      {showIcon && <Icon className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />}
      <span className="tracking-wide">{label}</span>
    </span>
  );
};
