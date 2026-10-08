import React, { useState } from 'react';
import { Movie } from '../../types/movie';
import { StarRating } from '../common/StarRating';
import { FallbackPoster } from '../common/FallbackPoster';
import { GenreBadge } from '../common/Badge';

interface StarterMovieCardProps {
  movie: Movie;
  userRating?: number;
  onRate: (movieId: number, rating: number) => void;
}

export const StarterMovieCard: React.FC<StarterMovieCardProps> = ({
  movie,
  userRating = 0,
  onRate,
}) => {
  const [imageError, setImageError] = useState(false);
  const isRated = userRating > 0;

  return (
    <div
      className={`relative rounded-lg overflow-hidden bg-zinc-900 border transition-all duration-200 flex flex-col justify-between ${
        isRated
          ? 'border-emerald-500/80 shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500/50'
          : 'border-zinc-800 hover:border-zinc-700'
      }`}
    >
      {/* Poster Thumbnail */}
      <div className="relative aspect-[16/10] sm:aspect-[4/3] w-full overflow-hidden bg-zinc-950">
        {movie.poster_path && !imageError ? (
          <img
            src={movie.poster_path}
            alt={movie.title}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
            loading="lazy"
          />
        ) : (
          <FallbackPoster
            title={movie.title}
            genres={movie.genres}
            aspectRatio="backdrop"
            className="w-full h-full"
          />
        )}

        {isRated && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500 text-black shadow">
            {userRating} ★ Rated
          </div>
        )}
      </div>

      {/* Details & Rating Control */}
      <div className="p-3 flex-1 flex flex-col justify-between">
        <div>
          <h4 className="font-bold text-xs sm:text-sm text-white line-clamp-1">
            {movie.title}
          </h4>
          <div className="flex items-center gap-1 mt-1 flex-wrap">
            {movie.genres.slice(0, 2).map((g) => (
              <GenreBadge key={g} genre={g} className="text-[10px] py-0 px-1.5" />
            ))}
          </div>
        </div>

        <div className="mt-3 pt-2.5 border-t border-zinc-800 flex items-center justify-between">
          <span className="text-[10px] text-zinc-400 font-medium">Rate:</span>
          <StarRating
            initialRating={userRating}
            onRate={(stars) => onRate(movie.id || movie.movie_id, stars)}
            size="sm"
          />
        </div>
      </div>
    </div>
  );
};
