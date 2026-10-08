import React, { useState, useEffect } from 'react';
import { ExplainabilityData } from '../../types/modelLab';
import { fetchExplainability } from '../../api/modelLab';
import { Calculator, Cpu, Sparkles } from 'lucide-react';

interface MathBreakdownProps {
  movieId: number;
  movieTitle: string;
  profileId: string;
  model: 'funk_svd' | 'item_knn';
}

export const MathBreakdown: React.FC<MathBreakdownProps> = ({
  movieId,
  movieTitle,
  profileId,
  model,
}) => {
  const [data, setData] = useState<ExplainabilityData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        const res = await fetchExplainability(profileId, movieId, model, movieTitle);
        if (active) setData(res);
      } catch (err) {
        console.error('Failed to load explainability:', err);
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [movieId, profileId, model, movieTitle]);

  if (loading) {
    return (
      <div className="p-4 bg-zinc-900 rounded-lg border border-zinc-800 text-xs text-zinc-400 flex items-center justify-center gap-2">
        <div className="w-4 h-4 border-2 border-[#E50914] border-t-transparent rounded-full animate-spin" />
        <span>Calculating mathematical explainability breakdown...</span>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="p-4 bg-zinc-900/90 rounded-lg border border-zinc-700/60 text-xs">
      <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
        <div className="flex items-center gap-2 font-bold text-white text-sm">
          <Calculator className="w-4 h-4 text-[#E50914]" />
          <span>Algorithmic Explainability Breakdown</span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-800 text-zinc-300 border border-zinc-700">
          Model: {model === 'funk_svd' ? 'Funk-SVD' : 'Item-KNN'}
        </span>
      </div>

      {model === 'funk_svd' && data.funk_svd && (
        <div className="mt-3 space-y-3">
          <div className="font-mono text-zinc-300 bg-zinc-950 p-2.5 rounded border border-zinc-800/80">
            <div className="text-[11px] text-zinc-400 mb-1">
              Biased Matrix Factorization Equation:
            </div>
            <div className="text-emerald-400 font-bold">
              r̂_ui = μ + b_u + b_i + (p_u · q_i)
            </div>
            <div className="text-zinc-400 mt-1">
              = {data.funk_svd.mu.toFixed(2)} (μ) + {data.funk_svd.user_bias.toFixed(2)} (b_u) + {data.funk_svd.item_bias.toFixed(2)} (b_i) + {data.funk_svd.dot_product.toFixed(2)} (latent)
            </div>
            <div className="text-white font-bold text-sm mt-1">
              = {data.funk_svd.predicted_score.toFixed(2)} ★ Predicted Rating
            </div>
          </div>

          <div>
            <div className="font-semibold text-zinc-300 mb-1.5 flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-zinc-400" />
              <span>Top Latent Factor Interactions (k=64 dimensions):</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.funk_svd.latent_breakdown.map((item) => (
                <div
                  key={item.factor_index}
                  className="bg-zinc-950/70 p-2 rounded border border-zinc-800 text-[11px]"
                >
                  <div className="text-zinc-500 font-mono">Factor {item.factor_index}</div>
                  <div className="flex justify-between text-zinc-400 text-[10px] mt-0.5">
                    <span>u: {item.user_val.toFixed(2)}</span>
                    <span>i: {item.item_val.toFixed(2)}</span>
                  </div>
                  <div className="text-emerald-400 font-bold text-right mt-0.5">
                    +{item.product.toFixed(3)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {model === 'item_knn' && data.item_knn && (
        <div className="mt-3 space-y-3">
          <div className="font-mono text-zinc-300 bg-zinc-950 p-2.5 rounded border border-zinc-800/80">
            <div className="text-[11px] text-zinc-400 mb-1">
              Adjusted Cosine Nearest Neighbors Formula (Furtado & Singh 2020):
            </div>
            <div className="text-purple-400 font-bold">
              r̂_ui = r̄_u + [ Σ s_ij (r_uj - r̄_u) ] / [ Σ |s_ij| ]
            </div>
            <div className="text-zinc-400 mt-1">
              User Mean (r̄_u): {data.item_knn.user_mean.toFixed(2)} ★
            </div>
            <div className="text-white font-bold text-sm mt-1">
              = {data.item_knn.predicted_score.toFixed(2)} ★ Predicted Rating
            </div>
          </div>

          <div>
            <div className="font-semibold text-zinc-300 mb-1.5 flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5 text-zinc-400" />
              <span>Top Neighbor Items Contributing to Prediction:</span>
            </div>
            <div className="space-y-1.5">
              {data.item_knn.neighbors.map((n) => (
                <div
                  key={n.movie_id}
                  className="flex items-center justify-between bg-zinc-950/70 px-3 py-1.5 rounded border border-zinc-800 text-[11px]"
                >
                  <span className="text-zinc-200 font-medium truncate max-w-[200px]">
                    {n.title}
                  </span>
                  <div className="flex items-center gap-3 text-zinc-400 font-mono">
                    <span>Similarity: {n.similarity.toFixed(3)}</span>
                    <span>Rated: {n.rating.toFixed(1)}★</span>
                    <span className="text-purple-400 font-bold">
                      {n.contribution >= 0 ? `+${n.contribution.toFixed(2)}` : n.contribution.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
