import React, { useState } from 'react';
import { Movie } from '../../types/movie';
import { MatchBadge } from '../common/Badge';
import { Play, Info, Sparkles } from 'lucide-react';
import { FallbackPoster } from '../common/FallbackPoster';

interface BillboardProps {
  movie: Movie | null;
  onOpenDetails: (movie: Movie) => void;
  activeProfileName: string;
}

export const Billboard: React.FC<BillboardProps> = ({
  movie,
  onOpenDetails,
  activeProfileName,
}) => {
  const [backdropError, setBackdropError] = useState(false);

  if (!movie) {
    return (
      <div className="relative h-[65vh] min-h-[480px] w-full bg-zinc-950 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-netflix-red border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const bgImage = movie.backdrop_path || movie.poster_path;

  return (
    <div className="relative h-[70vh] min-h-[520px] max-h-[750px] w-full overflow-hidden select-none">
      {/* Background Hero Image */}
      <div className="absolute inset-0">
        {bgImage && !backdropError ? (
          <img
            src={bgImage}
            alt={movie.title}
            onError={() => setBackdropError(true)}
            className="w-full h-full object-cover object-center filter brightness-90 scale-105"
          />
        ) : (
          <FallbackPoster
            title={movie.title}
            genres={movie.genres}
            aspectRatio="backdrop"
            className="w-full h-full"
          />
        )}

        {/* Cinematic Vignette Gradients */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-[#141414]/40 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent w-full md:w-3/4" />
        <div className="absolute inset-0 bg-radial-gradient from-transparent to-[#141414]/60" />
      </div>

      {/* Content Container */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex flex-col justify-end pb-16 md:pb-24">
        <div className="max-w-2xl">
          {/* Algorithm Badge */}
          <div className="flex items-center gap-2 mb-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#E50914]/90 text-white font-bold text-xs uppercase tracking-wider shadow-lg">
              <Sparkles className="w-3 h-3" />
              <span>#1 Match for {activeProfileName}</span>
            </span>
            {movie.match_score !== undefined && (
              <MatchBadge score={movie.match_score} />
            )}
          </div>

          {/* Title */}
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black text-white tracking-tight drop-shadow-2xl leading-none">
            {movie.title}
          </h1>

          {/* Genres & Year */}
          <div className="flex items-center gap-3 my-3 text-xs sm:text-sm text-zinc-300 font-medium">
            <span>{movie.year || '1999'}</span>
            <span>•</span>
            <span>{(movie.genres || []).join(' / ')}</span>
            {movie.runtime && (
              <>
                <span>•</span>
                <span>{movie.runtime}m</span>
              </>
            )}
          </div>

          {/* Synopsis */}
          <p className="text-sm sm:text-base text-zinc-300 line-clamp-3 leading-relaxed drop-shadow-md my-4 max-w-xl">
            {movie.synopsis || movie.overview || 'Explore this personalized recommendation selected for your taste profile.'}
          </p>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 mt-6">
            <button
              onClick={() => onOpenDetails(movie)}
              className="flex items-center gap-2 px-6 py-2.5 bg-white hover:bg-zinc-200 text-black font-bold rounded text-sm md:text-base transition-colors shadow-lg hover:scale-105 transform active:scale-95"
            >
              <Play className="w-5 h-5 fill-black" />
              <span>Play</span>
            </button>

            <button
              onClick={() => onOpenDetails(movie)}
              className="flex items-center gap-2 px-6 py-2.5 bg-zinc-700/80 hover:bg-zinc-600/90 text-white font-bold rounded text-sm md:text-base transition-colors shadow-lg backdrop-blur-sm border border-zinc-500/30 hover:scale-105 transform active:scale-95"
            >
              <Info className="w-5 h-5 text-white" />
              <span>More Info</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
