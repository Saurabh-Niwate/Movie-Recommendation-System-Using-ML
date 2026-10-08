import React from 'react';
import { ModelComparisonRow } from '../../types/modelLab';
import { ArrowLeftRight, Star } from 'lucide-react';

interface SideBySideCompareProps {
  rows: ModelComparisonRow[];
  profileName: string;
}

export const SideBySideCompare: React.FC<SideBySideCompareProps> = ({
  rows,
  profileName,
}) => {
  return (
    <div className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-5 shadow-2xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-zinc-800">
        <div>
          <h4 className="font-bold text-white text-base flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5 text-[#E50914]" />
            <span>Side-by-Side Model Comparison (for {profileName})</span>
          </h4>
          <p className="text-xs text-zinc-400 mt-0.5">
            Observing distinct predicted ratings and ranking discrepancies between Item-KNN and Funk-SVD
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Item-KNN */}
        <div className="bg-zinc-900/60 rounded-xl border border-zinc-800/80 p-4">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
            <div>
              <span className="font-bold text-sm text-purple-400 uppercase tracking-wide">
                Item-KNN Model
              </span>
              <p className="text-[11px] text-zinc-400">
                Adjusted Cosine Similarity + Significance Shrinkage
              </p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-800">
              Memory-based
            </span>
          </div>

          <div className="space-y-2">
            {rows.map((row) => (
              <div
                key={`knn-${row.movie_id}`}
                className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800/60 hover:border-purple-500/40 transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="w-5 h-5 rounded-full bg-zinc-800 text-zinc-400 text-xs font-mono flex items-center justify-center flex-none">
                    #{row.rank}
                  </span>
                  <div className="truncate">
                    <h5 className="font-bold text-xs text-white truncate">
                      {row.title}
                    </h5>
                    <span className="text-[10px] text-zinc-500">
                      {(row.genres || []).slice(0, 2).join(', ')}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-right flex-none pl-3">
                  <span className="text-xs font-mono text-purple-400 font-bold flex items-center gap-1">
                    <Star className="w-3 h-3 fill-purple-400" />
                    {row.item_knn_score.toFixed(2)}
                  </span>
                  <span className="text-[11px] font-bold text-zinc-400 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">
                    {row.item_knn_match}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Funk-SVD */}
        <div className="bg-zinc-900/60 rounded-xl border border-zinc-800/80 p-4">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
            <div>
              <span className="font-bold text-sm text-[#E50914] uppercase tracking-wide">
                Funk-SVD Model
              </span>
              <p className="text-[11px] text-zinc-400">
                Biased Matrix Factorization + Online Fold-in
              </p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-red-950 text-red-300 border border-red-800">
              Latent Model
            </span>
          </div>

          <div className="space-y-2">
            {rows.map((row) => (
              <div
                key={`svd-${row.movie_id}`}
                className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-950/80 border border-zinc-800/60 hover:border-red-500/40 transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="w-5 h-5 rounded-full bg-zinc-800 text-zinc-400 text-xs font-mono flex items-center justify-center flex-none">
                    #{row.rank}
                  </span>
                  <div className="truncate">
                    <h5 className="font-bold text-xs text-white truncate">
                      {row.title}
                    </h5>
                    <span className="text-[10px] text-zinc-500">
                      {(row.genres || []).slice(0, 2).join(', ')}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-right flex-none pl-3">
                  <span className="text-xs font-mono text-[#E50914] font-bold flex items-center gap-1">
                    <Star className="w-3 h-3 fill-[#E50914]" />
                    {row.funk_svd_score.toFixed(2)}
                  </span>
                  <span className="text-[11px] font-bold text-zinc-400 bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">
                    {row.funk_svd_match}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
