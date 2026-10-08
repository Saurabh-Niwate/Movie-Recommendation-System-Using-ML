import React, { useState } from 'react';
import { ModelComparisonRow } from '../../types/modelLab';
import { MathBreakdown } from '../modal/MathBreakdown';
import { BookOpen } from 'lucide-react';

interface ExplainabilityCardProps {
  rows: ModelComparisonRow[];
  profileId: string;
}

export const ExplainabilityCard: React.FC<ExplainabilityCardProps> = ({
  rows,
  profileId,
}) => {
  const [selectedMovieId, setSelectedMovieId] = useState<number>(rows[0]?.movie_id || 2571);
  const [activeModel, setActiveModel] = useState<'funk_svd' | 'item_knn'>('funk_svd');

  const selectedMovie = rows.find((r) => r.movie_id === selectedMovieId) || rows[0];

  if (!selectedMovie) return null;

  return (
    <div className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-5 shadow-2xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 pb-3 border-b border-zinc-800">
        <div>
          <h4 className="font-bold text-white text-base flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-[#E50914]" />
            <span>Mathematical Explainability Deep Dive</span>
          </h4>
          <p className="text-xs text-zinc-400 mt-0.5">
            Inspect the exact mathematical computations driving recommendations
          </p>
        </div>

        {/* Algorithm Switcher */}
        <div className="flex items-center gap-2 bg-zinc-900 p-1 rounded-lg border border-zinc-800">
          <button
            onClick={() => setActiveModel('funk_svd')}
            className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
              activeModel === 'funk_svd'
                ? 'bg-[#E50914] text-white shadow'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Funk-SVD Biases & Latents
          </button>
          <button
            onClick={() => setActiveModel('item_knn')}
            className={`px-3 py-1 rounded text-xs font-semibold transition-colors ${
              activeModel === 'item_knn'
                ? 'bg-purple-600 text-white shadow'
                : 'text-zinc-400 hover:text-white'
            }`}
          >
            Item-KNN Cosine Neighbors
          </button>
        </div>
      </div>

      {/* Select Movie to inspect */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-zinc-400 mb-2">
          Select Movie to Inspect:
        </label>
        <div className="flex gap-2 overflow-x-auto pb-2 hide-scrollbar">
          {rows.map((row) => (
            <button
              key={row.movie_id}
              onClick={() => setSelectedMovieId(row.movie_id)}
              className={`flex-none px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                row.movie_id === selectedMovieId
                  ? 'bg-zinc-800 border-white text-white shadow'
                  : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:border-zinc-700 hover:text-zinc-200'
              }`}
            >
              {row.title}
            </button>
          ))}
        </div>
      </div>

      {/* Render Math Breakdown for Selected Movie */}
      <MathBreakdown
        movieId={selectedMovie.movie_id}
        movieTitle={selectedMovie.title}
        profileId={profileId}
        model={activeModel}
      />
    </div>
  );
};
