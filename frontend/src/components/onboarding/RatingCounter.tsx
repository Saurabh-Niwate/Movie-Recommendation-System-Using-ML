import React from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';

interface RatingCounterProps {
  count: number;
  target?: number;
}

export const RatingCounter: React.FC<RatingCounterProps> = ({ count, target = 6 }) => {
  const progressPercent = Math.min(100, Math.round((count / target) * 100));
  const isComplete = count >= target;

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-xl p-5 shadow-xl max-w-xl mx-auto">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isComplete ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          ) : (
            <Sparkles className="w-5 h-5 text-amber-400" />
          )}
          <span className="font-bold text-sm text-white">
            Cold-Start Calibration Progress
          </span>
        </div>
        <span
          data-testid="onboarding-rating-counter"
          className={`font-mono text-xs px-2.5 py-1 rounded-full font-bold ${
            isComplete
              ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/40'
              : 'bg-zinc-800 text-amber-400 border border-zinc-700'
          }`}
        >
          Rated {count} of {target} movies
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-zinc-950 h-3 rounded-full overflow-hidden border border-zinc-800 my-2">
        <div
          className={`h-full transition-all duration-500 ease-out ${
            isComplete
              ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
              : 'bg-gradient-to-r from-[#E50914] to-amber-500'
          }`}
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">
        {isComplete ? (
          <span className="text-emerald-400 font-medium">
            ✓ Criteria met! Click &quot;Generate Recommendations&quot; below to explore your personalized feed.
          </span>
        ) : (
          <span>
            Please rate at least <strong>6 movies</strong> to unlock your personalized recommendations. (
            {target - count} more required)
          </span>
        )}
      </p>
    </div>
  );
};
