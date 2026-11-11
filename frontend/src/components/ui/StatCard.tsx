import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  isPositive?: boolean;
  icon?: React.ReactNode;
  subtitle?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  isPositive,
  icon,
  subtitle,
}) => {
  return (
    <div className="bg-phantom-surface border border-phantom-border rounded-xl p-5 shadow-lg relative overflow-hidden group hover:border-phantom-accent/40 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">
          {title}
        </span>
        {icon && <div className="text-slate-400 group-hover:text-phantom-accent transition-colors">{icon}</div>}
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
          {value}
        </span>
        {change && (
          <span
            className={`text-xs font-mono font-medium ${
              isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {change}
          </span>
        )}
      </div>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
      <div className="absolute inset-x-0 bottom-0 h-0.5 bg-gradient-to-r from-transparent via-phantom-accent/20 to-transparent group-hover:via-phantom-accent transition-all" />
    </div>
  );
};

