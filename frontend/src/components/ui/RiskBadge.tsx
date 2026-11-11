import React from 'react';
import { RiskLevel } from '../../types';

interface RiskBadgeProps {
  level: RiskLevel | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ level, score, size = 'md' }) => {
  const normLevel = (level || 'LOW').toUpperCase();

  const colorMap: Record<string, string> = {
    LOW: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    MEDIUM: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    HIGH: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    CRITICAL: 'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse',
  };

  const classes = colorMap[normLevel] || colorMap.LOW;
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5 font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-mono tracking-wide ${sizeClasses} ${classes}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {normLevel}
      {typeof score === 'number' && (
        <span className="opacity-80 font-bold">({score.toFixed(1)})</span>
      )}
    </span>
  );
};

