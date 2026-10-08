import React, { useState } from 'react';
import { Movie } from '../../types/movie';
import { MatchBadge, GenreBadge } from '../common/Badge';
import { FallbackPoster } from '../common/FallbackPoster';
import { Info, Star } from 'lucide-react';

interface MovieCardProps {
  movie: Movie;
  onSelect: (movie: Movie) => void;
  userRating?: number;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie, onSelect, userRating }) => {
  const [imageError, setImageError] = useState(false);

  return (
    <div
      onClick={() => onSelect(movie)}
      className="group relative flex-none w-[170px] sm:w-[200px] md:w-[220px] cursor-pointer select-none transition-all duration-300 transform hover:scale-105 hover:z-30 rounded-md overflow-hidden bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:shadow-2xl hover:shadow-black"
    >
      {/* Poster Image */}
      <div className="relative aspect-[2/3] w-full overflow-hidden bg-zinc-900">
        {movie.poster_path && !imageError ? (
          <img
            src={movie.poster_path}
            alt={movie.title}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:brightness-105"
            loading="lazy"
          />
        ) : (
          <FallbackPoster title={movie.title} genres={movie.genres} aspectRatio="poster" />
        )}

        {/* Top Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-1 items-start z-10">
          {movie.match_score !== undefined && (
            <MatchBadge score={movie.match_score} />
          )}
          {userRating !== undefined && (
            <span className="flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/90 text-black shadow">
              <Star className="w-3 h-3 fill-black text-black" />
              <span>{userRating}★</span>
            </span>
          )}
        </div>

        {/* Quick action overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3">
          <h4 className="font-bold text-sm text-white drop-shadow line-clamp-1">
            {movie.title}
          </h4>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            {(movie.genres || []).slice(0, 2).map((g) => (
              <GenreBadge key={g} genre={g} />
            ))}
          </div>
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-zinc-700/60">
            <span className="text-[11px] text-zinc-400">
              {movie.year || 'MovieLens'}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelect(movie);
              }}
              className="flex items-center gap-1 text-[11px] font-semibold text-white bg-zinc-800 hover:bg-zinc-700 px-2 py-0.5 rounded border border-zinc-600 transition-colors"
            >
              <Info className="w-3 h-3 text-[#E50914]" />
              <span>Details</span>
            </button>
          </div>
        </div>
      </div>

      {/* Static title footer for clarity */}
      <div className="p-2.5 bg-zinc-950/90 flex flex-col justify-between">
        <h4 className="font-semibold text-xs text-zinc-200 line-clamp-1 group-hover:text-white transition-colors">
          {movie.title}
        </h4>
        <div className="flex items-center justify-between mt-1 text-[11px] text-zinc-500">
          <span>{(movie.genres || [])[0] || 'Feature'}</span>
          {movie.predicted_rating && (
            <span className="text-zinc-400 font-mono">
              ★ {movie.predicted_rating.toFixed(1)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
