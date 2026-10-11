import React, { useState, useEffect } from 'react';
import { Movie } from '../../types/movie';
import { useProfile } from '../../context/ProfileContext';
import { useModel } from '../../context/ModelContext';
import { MatchBadge, GenreBadge } from '../common/Badge';
import { StarRating } from '../common/StarRating';
import { FallbackPoster } from '../common/FallbackPoster';
import { MathBreakdown } from './MathBreakdown';
import { X, Play, Clock, Calendar, Calculator, Sparkles } from 'lucide-react';
import { fetchAlsoWatched } from '../../api/recommendations';

interface TitleDetailModalProps {
  movie: Movie | null;
  onClose: () => void;
  onSelectMovie: (movie: Movie) => void;
}

export const TitleDetailModal: React.FC<TitleDetailModalProps> = ({
  movie,
  onClose,
  onSelectMovie,
}) => {
  const { activeProfile, userRatings, rateMovie } = useProfile();
  const { selectedModel } = useModel();
  const [backdropError, setBackdropError] = useState(false);
  const [showMath, setShowMath] = useState(false);
  const [similarMovies, setSimilarMovies] = useState<Movie[]>([]);
  const [isSubmittingRating, setIsSubmittingRating] = useState(false);

  // Close on ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Load similar movies
  useEffect(() => {
    let mounted = true;
    if (movie) {
      fetchAlsoWatched(movie.id || movie.movie_id).then((movies) => {
        if (mounted) setSimilarMovies(movies.slice(0, 6));
      });
    }
    return () => {
      mounted = false;
    };
  }, [movie]);

  if (!movie) return null;

  const currentRating = userRatings[movie.id || movie.movie_id] || 0;
  const bgImage = movie.backdrop_path || movie.poster_path;

  const handleRate = async (stars: number) => {
    setIsSubmittingRating(true);
    await rateMovie(movie.id || movie.movie_id, stars);
    setIsSubmittingRating(false);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 md:p-6">
      {/* Modal Container */}
      <div
        className="relative w-full max-w-4xl bg-zinc-950 rounded-xl overflow-hidden border border-zinc-800 shadow-2xl transform transition-all my-8"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-20 w-9 h-9 rounded-full bg-black/70 hover:bg-black/90 text-white flex items-center justify-center transition-colors border border-zinc-700/60"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Banner inside modal */}
        <div className="relative h-64 sm:h-80 md:h-96 w-full overflow-hidden">
          {bgImage && !backdropError ? (
            <img
              src={bgImage}
              alt={movie.title}
              onError={() => setBackdropError(true)}
              className="w-full h-full object-cover object-center filter brightness-90"
            />
          ) : (
            <FallbackPoster
              title={movie.title}
              genres={movie.genres}
              aspectRatio="backdrop"
              className="w-full h-full"
            />
          )}

          <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent" />

          {/* Modal Title Overlay */}
          <div className="absolute bottom-6 left-6 right-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2 flex-wrap">
                {movie.match_score !== undefined && (
                  <MatchBadge score={movie.match_score} />
                )}
                {(movie.genres || []).map((g) => (
                  <GenreBadge key={g} genre={g} />
                ))}
              </div>
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-white tracking-tight drop-shadow-lg">
                {movie.title}
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => alert(`Starting playback for ${movie.title}`)}
                className="flex items-center gap-2 px-5 py-2 rounded-lg bg-white text-black font-bold text-sm hover:bg-zinc-200 transition-colors shadow"
              >
                <Play className="w-4 h-4 fill-black" />
                <span>Play</span>
              </button>
            </div>
          </div>
        </div>

        {/* Modal Body Content */}
        <div className="p-6 md:p-8 space-y-6">
          {/* Metadata & Interactive Rating Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-6 border-b border-zinc-800">
            {/* Left 2 cols: Synopsis & Details */}
            <div className="md:col-span-2 space-y-4">
              <div className="flex items-center gap-4 text-xs font-medium text-zinc-400">
                {movie.year && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{movie.year}</span>
                  </span>
                )}
                {movie.runtime && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{movie.runtime} min</span>
                  </span>
                )}
                {movie.avg_rating && (
                  <span className="text-amber-400 font-semibold">
                    Catalog Avg: {movie.avg_rating.toFixed(1)} ★
                  </span>
                )}
              </div>

              <p className="text-sm sm:text-base text-zinc-300 leading-relaxed">
                {movie.synopsis || movie.overview || 'A high-impact cinematic title from the MovieLens 1M catalog, indexed for real-time collaborative filtering recommendations.'}
              </p>

              {/* Cast & Director */}
              <div className="pt-2 text-xs text-zinc-400 space-y-1">
                {movie.director && (
                  <p>
                    <span className="text-zinc-500 font-semibold">Director:</span>{' '}
                    <span className="text-zinc-300">{movie.director}</span>
                  </p>
                )}
                {movie.cast && movie.cast.length > 0 && (
                  <p>
                    <span className="text-zinc-500 font-semibold">Starring:</span>{' '}
                    <span className="text-zinc-300">{movie.cast.join(', ')}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Right col: Interactive Rating & Fast Fold-in */}
            <div className="bg-zinc-900/80 p-5 rounded-xl border border-zinc-800 flex flex-col justify-between">
              <div>
                <div className="text-xs font-bold text-zinc-200 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>Your Rating</span>
                  {isSubmittingRating && (
                    <span className="text-[10px] text-amber-400 animate-pulse">
                      Updating preferences...
                    </span>
                  )}
                </div>

                <div className="my-2">
                  <StarRating
                    initialRating={currentRating}
                    onRate={handleRate}
                    size="lg"
                    showValue
                  />
                </div>

                <p className="text-[11px] text-zinc-400 mt-2 leading-relaxed">
                  Rating this movie instantly refines your recommendations and tailors future film suggestions.
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-800">
                <button
                  onClick={() => setShowMath(!showMath)}
                  className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 border border-zinc-700 transition-colors"
                >
                  <Calculator className="w-3.5 h-3.5 text-[#E50914]" />
                  <span>{showMath ? 'Hide Details' : 'View Recommendation Details'}</span>
                </button>
              </div>
            </div>
          </div>

          {/* Optional Math Breakdown Section */}
          {showMath && (
            <MathBreakdown
              movieId={movie.id || movie.movie_id}
              movieTitle={movie.title}
              profileId={activeProfile?.id || 'neel'}
              model={selectedModel}
            />
          )}

          {/* "More Like This" Section */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-4 h-4 text-[#E50914]" />
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                More Like This
              </h3>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {similarMovies.map((similar) => (
                <div
                  key={`similar-${similar.id || similar.movie_id}`}
                  onClick={() => onSelectMovie(similar)}
                  className="cursor-pointer group relative rounded bg-zinc-900 border border-zinc-800 hover:border-zinc-600 transition-all overflow-hidden"
                >
                  <div className="aspect-[2/3] w-full overflow-hidden bg-zinc-900">
                    {similar.poster_path ? (
                      <img
                        src={similar.poster_path}
                        alt={similar.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    ) : (
                      <FallbackPoster title={similar.title} genres={similar.genres || []} />
                    )}
                  </div>
                  <div className="p-2">
                    <h5 className="text-[11px] font-bold text-white line-clamp-1">
                      {similar.title}
                    </h5>
                    <p className="text-[10px] text-zinc-500 line-clamp-1">
                      {(similar.genres || [])[0] || 'Movie'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
