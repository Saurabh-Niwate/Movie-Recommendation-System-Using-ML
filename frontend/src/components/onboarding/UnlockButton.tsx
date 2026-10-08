import React from 'react';
import { Lock, Unlock, ArrowRight } from 'lucide-react';

interface UnlockButtonProps {
  ratingsCount: number;
  requiredCount?: number;
  onUnlock: () => void;
  isLoading?: boolean;
}

export const UnlockButton: React.FC<UnlockButtonProps> = ({
  ratingsCount,
  requiredCount = 6,
  onUnlock,
  isLoading = false,
}) => {
  const isUnlocked = ratingsCount >= requiredCount;

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        disabled={!isUnlocked || isLoading}
        onClick={onUnlock}
        data-testid="generate-recommendations-btn"
        className={`relative group px-8 py-4 rounded-xl font-extrabold text-base transition-all duration-300 flex items-center gap-3 shadow-2xl ${
          isUnlocked && !isLoading
            ? 'bg-[#E50914] hover:bg-[#f40612] text-white hover:scale-105 active:scale-95 shadow-red-900/50 cursor-pointer animate-pulse hover:animate-none'
            : 'bg-zinc-800 text-zinc-500 opacity-60 cursor-not-allowed border border-zinc-700/50'
        }`}
      >
        {isUnlocked ? (
          <Unlock className="w-5 h-5 text-white" />
        ) : (
          <Lock className="w-5 h-5 text-zinc-500" />
        )}

        <span>
          {isLoading
            ? 'Running Fold-in Solver...'
            : 'Generate Recommendations'}
        </span>

        {isUnlocked && <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />}
      </button>

      {!isUnlocked && (
        <span className="text-xs text-zinc-500 font-medium">
          Rate {requiredCount - ratingsCount} more movie{requiredCount - ratingsCount > 1 ? 's' : ''} to enable button
        </span>
      )}
    </div>
  );
};
