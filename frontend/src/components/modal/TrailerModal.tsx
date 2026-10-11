import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../api/client';

export interface TrailerMovieTarget {
  id: number;
  title: string;
  trailer_key?: string | null;
}

interface TrailerModalProps {
  movie: TrailerMovieTarget | null;
  onClose: () => void;
}

export const TrailerModal: React.FC<TrailerModalProps> = ({ movie, onClose }) => {
  const [trailerKey, setTrailerKey] = useState<string | null>(movie?.trailer_key || null);
  const [loading, setLoading] = useState<boolean>(!movie?.trailer_key);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!movie) {
      setTrailerKey(null);
      return;
    }

    if (movie.trailer_key) {
      setTrailerKey(movie.trailer_key);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    apiFetch<{ key: string; embed_url: string }>(`/movies/${movie.id}/trailer`)
      .then((data) => {
        if (data && data.key) {
          setTrailerKey(data.key);
        } else {
          setError('No official trailer video found.');
        }
      })
      .catch(() => {
        // Fallback default trailer or search
        setError('Trailer currently unavailable.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [movie]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!movie) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-4xl bg-surface-container-low rounded-2xl border border-outline-variant/30 overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant/20 bg-surface-container-lowest/80">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-secondary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
              play_circle
            </span>
            <h3 className="font-bold text-on-surface text-base truncate max-w-md">
              {movie.title} — Official Trailer
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-outline hover:text-on-surface hover:bg-surface-container-high transition-colors"
            title="Close Trailer"
          >
            <span className="material-symbols-outlined text-lg leading-none block">close</span>
          </button>
        </div>

        {/* Video Container */}
        <div className="relative w-full aspect-video bg-black flex items-center justify-center">
          {loading && (
            <div className="flex flex-col items-center gap-3 text-secondary">
              <span className="material-symbols-outlined text-4xl animate-spin">progress_activity</span>
              <span className="text-sm font-semibold tracking-wider text-on-surface-variant">Connecting to TMDB / YouTube Stream...</span>
            </div>
          )}

          {!loading && trailerKey && (
            <iframe
              src={`https://www.youtube.com/embed/${trailerKey}?autoplay=1&rel=0&modestbranding=1`}
              title={`${movie.title} Trailer`}
              className="w-full h-full border-0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
            />
          )}

          {!loading && !trailerKey && (
            <div className="flex flex-col items-center gap-4 text-center px-6">
              <span className="material-symbols-outlined text-tertiary text-5xl">smart_display</span>
              <p className="text-on-surface-variant text-sm max-w-md">
                {error || 'No direct YouTube embed available for this title.'}
              </p>
              <a
                href={`https://www.youtube.com/results?search_query=${encodeURIComponent(movie.title + ' official trailer')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-5 py-2.5 rounded-full bg-primary-container text-on-primary-container font-semibold text-sm hover:brightness-110 transition-all flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-lg">open_in_new</span>
                Search on YouTube
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
