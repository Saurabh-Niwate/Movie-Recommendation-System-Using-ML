import React from 'react';
import { ModelMetrics } from '../../types/modelLab';
import { Trophy, Award } from 'lucide-react';

interface LeaderboardTableProps {
  metrics: ModelMetrics[];
}

export const LeaderboardTable: React.FC<LeaderboardTableProps> = ({ metrics }) => {
  // Find best values for highlights
  const bestNdcg = Math.max(...metrics.map((m) => m.ndcg_10));
  const bestRmse = Math.min(...metrics.map((m) => m.rmse));
  const bestMae = Math.min(...metrics.map((m) => m.mae));
  const bestCoverage = Math.max(...metrics.map((m) => m.coverage_10));

  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-950/80 shadow-2xl">
      <table className="w-full text-left text-xs sm:text-sm">
        <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[11px] tracking-wider border-b border-zinc-800">
          <tr>
            <th className="py-3.5 px-4 font-semibold">Model Architecture</th>
            <th className="py-3.5 px-4 font-semibold text-right">NDCG@10</th>
            <th className="py-3.5 px-4 font-semibold text-right">RMSE</th>
            <th className="py-3.5 px-4 font-semibold text-right">MAE</th>
            <th className="py-3.5 px-4 font-semibold text-right">Precision@10</th>
            <th className="py-3.5 px-4 font-semibold text-right">Recall@10</th>
            <th className="py-3.5 px-4 font-semibold text-right">Coverage@10</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-800/80">
          {metrics.map((m) => {
            const isWinner = m.ndcg_10 === bestNdcg;
            return (
              <tr
                key={m.model_name}
                className={`hover:bg-zinc-900/50 transition-colors ${
                  isWinner ? 'bg-[#E50914]/5' : ''
                }`}
              >
                <td className="py-4 px-4">
                  <div className="flex items-center gap-2">
                    {isWinner ? (
                      <Trophy className="w-4 h-4 text-amber-400 flex-none" />
                    ) : (
                      <Award className="w-4 h-4 text-zinc-600 flex-none" />
                    )}
                    <div>
                      <div className="font-bold text-white flex items-center gap-2">
                        <span>{m.display_name}</span>
                        {isWinner && (
                          <span className="text-[10px] font-mono uppercase bg-amber-400/20 text-amber-300 px-1.5 py-0.5 rounded border border-amber-400/30">
                            Leader
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-zinc-400 mt-0.5 line-clamp-1">
                        {m.description}
                      </div>
                    </div>
                  </div>
                </td>

                {/* NDCG@10 */}
                <td className="py-4 px-4 text-right font-mono font-medium">
                  <span
                    className={
                      m.ndcg_10 === bestNdcg
                        ? 'text-emerald-400 font-bold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30'
                        : 'text-zinc-300'
                    }
                  >
                    {m.ndcg_10.toFixed(4)}
                  </span>
                </td>

                {/* RMSE */}
                <td className="py-4 px-4 text-right font-mono font-medium">
                  <span
                    className={
                      m.rmse === bestRmse
                        ? 'text-emerald-400 font-bold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30'
                        : 'text-zinc-300'
                    }
                  >
                    {m.rmse.toFixed(4)}
                  </span>
                </td>

                {/* MAE */}
                <td className="py-4 px-4 text-right font-mono font-medium">
                  <span
                    className={
                      m.mae === bestMae
                        ? 'text-emerald-400 font-bold bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-500/30'
                        : 'text-zinc-300'
                    }
                  >
                    {m.mae.toFixed(4)}
                  </span>
                </td>

                {/* Precision@10 */}
                <td className="py-4 px-4 text-right font-mono text-zinc-300">
                  {m.precision_10.toFixed(4)}
                </td>

                {/* Recall@10 */}
                <td className="py-4 px-4 text-right font-mono text-zinc-300">
                  {m.recall_10.toFixed(4)}
                </td>

                {/* Coverage@10 */}
                <td className="py-4 px-4 text-right font-mono font-medium">
                  <span
                    className={
                      m.coverage_10 === bestCoverage
                        ? 'text-emerald-400 font-bold'
                        : 'text-zinc-300'
                    }
                  >
                    {(m.coverage_10 * 100).toFixed(1)}%
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
