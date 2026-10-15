import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api/client';

export interface MovieDetailTarget {
  id: number;
  movie_id?: number;
  tmdb_id?: number;
  title: string;
  year?: number;
  genres?: string[];
  vote_average?: number;
  vote_count?: number;
  poster_path?: string | null;
  backdrop_path?: string | null;
  overview?: string;
  synopsis?: string;
  director?: string;
  cast?: string[] | string;
  runtime?: number;
  trailer_key?: string | null;
  match_percentage?: number;
}

interface MovieDetailModalProps {
  movie: MovieDetailTarget | null;
  isOpen: boolean;
  onClose: () => void;
  onPlayTrailer?: (target: { id: number; title: string; trailer_key?: string | null }) => void;
  onToggleWatchlist?: (movie: MovieDetailTarget) => void;
  isInWatchlist?: boolean;
  onRateMovie?: (movieId: number, rating: number) => void;
  userRating?: number;
  isLoggedIn?: boolean;
}

export const MovieDetailModal: React.FC<MovieDetailModalProps> = ({
  movie,
  isOpen,
  onClose,
  onPlayTrailer,
  onToggleWatchlist,
  isInWatchlist = false,
  onRateMovie,
  userRating = 0,
  isLoggedIn = false,
}) => {
  const [details, setDetails] = useState<MovieDetailTarget | null>(movie);
  const [loading, setLoading] = useState(false);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [localRating, setLocalRating] = useState<number>(userRating);

  // Sync state when movie prop changes
  useEffect(() => {
    if (!movie) {
      setDetails(null);
      return;
    }

    setDetails(movie);
    setLocalRating(userRating);

    // If director or cast is missing, fetch full movie detail from backend
    const mid = movie.movie_id || movie.id;
    if (mid && (!movie.director || !movie.cast || !movie.overview)) {
      setLoading(true);
      apiFetch<MovieDetailTarget>(`/movies/${mid}`)
        .then((fullData) => {
          setDetails((prev) => (prev ? { ...prev, ...fullData } : fullData));
        })
        .catch((err) => {
          console.warn('Failed to load full movie details:', err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [movie, userRating]);

  // Keyboard shortcut: Escape to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !details) return null;

  const movieId = details.movie_id || details.id;

  const getPosterUrl = () => {
    if (details.poster_path && details.poster_path.startsWith('http')) return details.poster_path;
    if (details.poster_path && details.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${details.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${movieId}.jpg`;
  };

  const getBackdropUrl = () => {
    if (details.backdrop_path && details.backdrop_path.startsWith('http')) return details.backdrop_path;
    if (details.backdrop_path && details.backdrop_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/original${details.backdrop_path}`;
    }
    return getPosterUrl();
  };

  const castList: string[] = Array.isArray(details.cast)
    ? details.cast
    : typeof details.cast === 'string'
    ? (details.cast as string).split(',').map((s) => s.trim())
    : [];

  const handleStarClick = (stars: number) => {
    setLocalRating(stars);
    if (onRateMovie) {
      onRateMovie(movieId, stars);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-fadeIn"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="relative w-full max-w-3xl max-h-[92vh] overflow-y-auto rounded-2xl bg-[#141822] border border-outline-variant/40 shadow-2xl text-on-surface flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Hero Backdrop Header */}
        <div className="relative w-full h-56 sm:h-72 md:h-80 overflow-hidden shrink-0 bg-surface-container-lowest">
          <img
            src={getBackdropUrl()}
            alt={details.title}
            className="w-full h-full object-cover object-top"
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src =
                'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=1200&q=80';
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#141822] via-[#141822]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#141822]/80 via-transparent to-transparent" />

          {/* Close Button */}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="absolute top-4 right-4 z-20 w-10 h-10 rounded-full bg-surface-container-lowest/70 backdrop-blur-md border border-outline-variant/40 text-on-surface hover:text-primary hover:bg-surface-container-high transition-all flex items-center justify-center shadow-lg hover:scale-105 active:scale-95"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>

          {/* Floating Poster & Main Info over banner */}
          <div className="absolute bottom-4 left-4 right-4 flex items-end gap-4 sm:gap-6">
            <div className="relative w-24 sm:w-32 md:w-36 aspect-[2/3] shrink-0 rounded-xl overflow-hidden border-2 border-outline-variant/50 shadow-2xl bg-surface-container-lowest hidden xs:block">
              <img
                src={getPosterUrl()}
                alt={details.title}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).src =
                    'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                }}
              />
            </div>

            <div className="flex-1 flex flex-col gap-1.5 pb-1">
              <div className="flex flex-wrap items-center gap-2">
                {details.year && (
                  <span className="px-2 py-0.5 rounded-full bg-surface-container-high text-xs font-bold text-on-surface border border-outline-variant/30">
                    {details.year}
                  </span>
                )}
                {details.runtime && (
                  <span className="flex items-center gap-1 text-xs text-on-surface-variant font-medium">
                    <span className="material-symbols-outlined text-sm">schedule</span>
                    {details.runtime} min
                  </span>
                )}
                {details.vote_average !== undefined && (
                  <span className="flex items-center gap-1 text-xs font-bold text-tertiary">
                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                      star
                    </span>
                    {details.vote_average.toFixed(1)} / 10
                  </span>
                )}
                {loading && (
                  <span className="flex items-center gap-1 text-xs text-secondary animate-pulse">
                    <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                    Syncing...
                  </span>
                )}
              </div>

              <h2 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight drop-shadow-md">
                {details.title}
              </h2>

              {/* Genre Badges */}
              <div className="flex flex-wrap gap-1.5 pt-0.5">
                {(details.genres || []).map((genre) => (
                  <span
                    key={genre}
                    className="px-2.5 py-0.5 rounded-md bg-secondary/15 text-secondary text-[11px] font-bold uppercase tracking-wider"
                  >
                    {genre}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-7 flex flex-col gap-6">
          {/* Action Row: Watch Trailer, Watchlist, Star Rating */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-outline-variant/30">
            <div className="flex items-center gap-3">
              {onPlayTrailer && (
                <button
                  type="button"
                  onClick={() => onPlayTrailer({ id: movieId, title: details.title, trailer_key: details.trailer_key })}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary-container text-on-primary font-bold text-xs sm:text-sm shadow-[0_0_20px_rgba(128,131,255,0.4)] hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                >
                  <span className="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                    play_arrow
                  </span>
                  <span>Watch Trailer</span>
                </button>
              )}

              {onToggleWatchlist && (
                <button
                  type="button"
                  onClick={() => onToggleWatchlist(details)}
                  className={`px-4 py-2.5 rounded-xl text-xs sm:text-sm font-semibold border transition-all flex items-center gap-1.5 ${
                    isInWatchlist
                      ? 'bg-secondary/15 border-secondary text-secondary hover:bg-secondary/25'
                      : 'bg-surface-container-high border-outline-variant/40 text-on-surface hover:bg-surface-bright'
                  }`}
                >
                  <span
                    className="material-symbols-outlined text-lg"
                    style={{ fontVariationSettings: isInWatchlist ? "'FILL' 1" : "'FILL' 0" }}
                  >
                    {isInWatchlist ? 'bookmark_added' : 'bookmark_add'}
                  </span>
                  <span>{isInWatchlist ? 'In Watchlist' : 'Add to Watchlist'}</span>
                </button>
              )}
            </div>

            {/* Interactive Rating */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-on-surface-variant font-medium">Your Rating:</span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => {
                  const active = (hoverRating || localRating) >= star;
                  return (
                    <button
                      key={star}
                      type="button"
                      disabled={!isLoggedIn && !onRateMovie}
                      onMouseEnter={() => setHoverRating(star)}
                      onMouseLeave={() => setHoverRating(0)}
                      onClick={() => handleStarClick(star)}
                      className="p-0.5 text-on-surface-variant hover:text-tertiary transition-transform hover:scale-110 disabled:cursor-not-allowed"
                      title={isLoggedIn ? `Rate ${star} star(s)` : 'Sign in to rate'}
                    >
                      <span
                        className="material-symbols-outlined text-xl"
                        style={{
                          fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0",
                          color: active ? '#ffb703' : undefined,
                        }}
                      >
                        star
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Synopsis / Overview */}
          <div className="flex flex-col gap-2">
            <h3 className="text-xs font-bold text-outline uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm text-secondary">info</span>
              Overview
            </h3>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed">
              {details.overview || details.synopsis || 'No overview synopsis provided for this title.'}
            </p>
          </div>

          {/* Director & Cast Metadata */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-outline-variant/20">
            {/* Director */}
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-bold text-outline uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-secondary">movie_filter</span>
                Director
              </span>
              <p className="text-sm font-semibold text-on-surface">
                {details.director || 'Acclaimed Director'}
              </p>
            </div>

            {/* Cast Members */}
            <div className="flex flex-col gap-1.5">
              <span className="text-xs font-bold text-outline uppercase tracking-wider flex items-center gap-1.5">
                <span className="material-symbols-outlined text-sm text-secondary">group</span>
                Cast
              </span>
              {castList.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {castList.map((actor) => (
                    <span
                      key={actor}
                      className="px-2.5 py-1 rounded-lg bg-surface-container-high/70 border border-outline-variant/30 text-xs font-medium text-on-surface flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-xs text-outline">person</span>
                      {actor}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-on-surface-variant">Leading Ensemble Cast</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
