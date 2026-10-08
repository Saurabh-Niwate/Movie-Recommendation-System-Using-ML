import React from 'react';

interface MatchBadgeProps {
  score?: number;
  className?: string;
}

export const MatchBadge: React.FC<MatchBadgeProps> = ({ score = 95, className = '' }) => {
  const safeScore = Math.min(99, Math.max(50, Math.round(score)));
  const isHigh = safeScore >= 85;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold tracking-tight ${
        isHigh
          ? 'text-emerald-400 bg-emerald-950/60 border border-emerald-500/30'
          : 'text-amber-400 bg-amber-950/60 border border-amber-500/30'
      } ${className}`}
    >
      {safeScore}% Match
    </span>
  );
};

interface GenreBadgeProps {
  genre: string;
  className?: string;
}

export const GenreBadge: React.FC<GenreBadgeProps> = ({ genre, className = '' }) => {
  return (
    <span
      className={`inline-block px-2 py-0.5 text-[11px] font-medium text-zinc-300 bg-zinc-800/80 rounded border border-zinc-700/50 ${className}`}
    >
      {genre}
    </span>
  );
};
