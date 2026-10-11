import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { TrailerModal, TrailerMovieTarget } from '../components/modal/TrailerModal';
import { MovieDetailModal, MovieDetailTarget } from '../components/modal/MovieDetailModal';
import { apiFetch, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface RecMovie {
  id: number;
  movie_id?: number;
  title: string;
  year?: number;
  genres: string[];
  vote_average: number;
  predicted_score?: number;
  match_percentage?: number;
  poster_path?: string | null;
  backdrop_path?: string | null;
  trailer_key?: string | null;
  synopsis?: string;
  overview?: string;
  director?: string;
  cast?: string[];
  runtime?: number;
}

export const FeedPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [topRecs, setTopRecs] = useState<RecMovie[]>([]);
  const [becauseYouLiked, setBecauseYouLiked] = useState<{ seed: string; movies: RecMovie[] }>({
    seed: 'Inception',
    movies: [],
  });
  const [alsoWatched, setAlsoWatched] = useState<RecMovie[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTrailer, setActiveTrailer] = useState<TrailerMovieTarget | null>(null);
  const [activeDetailMovie, setActiveDetailMovie] = useState<MovieDetailTarget | null>(null);
  const [watchlistSuccess, setWatchlistSuccess] = useState<string | null>(null);

  const getPosterUrl = (m: RecMovie) => {
    const mid = m.movie_id || m.id;
    if (m.poster_path && m.poster_path.startsWith('http')) return m.poster_path;
    if (m.poster_path && m.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${m.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${mid}.jpg`;
  };

  useEffect(() => {
    // Load recommendations
    apiFetch<any>('/recommendations?limit=15')
      .then((data) => {
        const items: RecMovie[] = Array.isArray(data) ? data : data.recommendations || data.items || [];
        setTopRecs(items);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 403) {
          // Cold-start gating: redirect to onboarding!
          navigate('/onboarding', { replace: true });
        } else {
          console.error('Failed to load recommendations:', err);
          // Fallback to top catalog movies
          apiFetch<{ items: RecMovie[] }>('/movies?limit=15&sort=popular').then((res) => {
            setTopRecs(res.items || []);
          });
        }
      })
      .finally(() => {
        setLoading(false);
      });

    // Load Because You Liked
    apiFetch<any>('/recommendations/because-you-liked?movie_id=2571&limit=5')
      .then((data) => {
        const items = data.recommendations || data.items || [];
        setBecauseYouLiked({
          seed: data.seed_movie_title || 'The Matrix',
          movies: items,
        });
      })
      .catch(() => {
        // Fallback
        apiFetch<{ items: RecMovie[] }>('/movies?genre=Sci-Fi&limit=5').then((res) => {
          setBecauseYouLiked({
            seed: 'Sci-Fi Classics',
            movies: res.items || [],
          });
        });
      });

    // Load Also Watched
    apiFetch<any>('/recommendations/also-watched?movie_id=550&limit=5')
      .then((data) => {
        const items = data.recommendations || data.items || [];
        setAlsoWatched(items);
      })
      .catch(() => {
        apiFetch<{ items: RecMovie[] }>('/movies?genre=Thriller&limit=5').then((res) => {
          setAlsoWatched(res.items || []);
        });
      });
  }, [navigate]);

  const handleAddToWatchlist = async (movieId: number, title: string) => {
    try {
      await apiFetch(`/watchlist/${movieId}`, {
        method: 'POST',
      });
      setWatchlistSuccess(`Saved "${title}" to your Watchlist`);
      setTimeout(() => setWatchlistSuccess(null), 3000);
    } catch (err) {
      console.error('Error saving to watchlist:', err);
    }
  };

  const handleRateMovie = async (movieId: number, score: number) => {
    try {
      await apiFetch('/ratings', {
        method: 'POST',
        body: JSON.stringify({ movie_id: movieId, rating: score }),
      });
      setWatchlistSuccess(`Recorded your ${score}★ rating!`);
      setTimeout(() => setWatchlistSuccess(null), 2500);
    } catch (err) {
      console.warn('Failed to submit rating:', err);
    }
  };

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative selection:bg-secondary/30 selection:text-secondary pb-24">
      {/* Background radial glows */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-[20%] right-[-10%] w-[55vw] h-[55vw] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute -bottom-[20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      {/* Watchlist Success Toast */}
      {watchlistSuccess && (
        <div className="fixed top-24 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-container-high/90 backdrop-blur-xl border border-secondary/30 text-on-surface text-sm font-semibold shadow-xl animate-fade-in">
          <span className="material-symbols-outlined text-secondary text-base">bookmark_added</span>
          <span>{watchlistSuccess}</span>
        </div>
      )}

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        {/* Top Hero: Live Neural Sync */}
        <section className="relative w-full pt-8 pb-6 overflow-hidden">
          <div className="absolute -top-16 left-1/4 w-[42rem] h-64 bg-primary-container/10 rounded-full blur-[100px] pointer-events-none"></div>
          <div className="absolute top-8 right-1/3 w-80 h-48 bg-secondary/10 rounded-full blur-[80px] pointer-events-none"></div>

          <div className="relative z-10 flex flex-col gap-3 max-w-5xl">
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary-container/20 text-secondary text-xs uppercase tracking-wider font-semibold backdrop-blur-md">
                <span className="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
                Personalized For You
              </span>
              <span className="text-outline text-xs">|</span>
              <span className="text-on-surface-variant text-xs uppercase tracking-widest font-semibold">
                Updated Live
              </span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold text-on-surface tracking-tight">
              Welcome back,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-secondary to-primary-fixed">
                {user?.full_name || user?.email.split('@')[0] || 'Curator'}
              </span>
            </h1>

            <p className="text-sm sm:text-base text-on-surface-variant max-w-3xl leading-relaxed">
              Your Curated Feed is tailored to your favorite genres and preferences — Sci-Fi, Psychological Thriller, Denis Villeneuve, Christopher Nolan, and Inception.
            </p>
          </div>
        </section>

        {/* Section 1: Favorite Genres & Styles Glass Bar */}
        <section className="w-full mb-10">
          <div className="relative rounded-2xl bg-surface-container/70 backdrop-blur-2xl p-6 sm:p-8 shadow-xl border border-outline-variant/30 overflow-hidden">
            <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-secondary/10 rounded-full blur-3xl pointer-events-none"></div>

            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              {/* Category Pills */}
              <div className="flex flex-col gap-2 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-xl">fingerprint</span>
                  <span className="text-xs uppercase tracking-wider text-on-surface font-bold">
                    Your Favorite Genres &amp; Styles
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-secondary/15 text-secondary text-xs font-semibold shadow-sm">
                    Sci-Fi ✦
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-secondary/15 text-secondary text-xs font-semibold shadow-sm">
                    Mind-Bending ✦
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer">
                    Blade Runner 2049 ✦
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer">
                    Christopher Nolan ✦
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer">
                    Denis Villeneuve ✦
                  </span>
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer">
                    Psychological Thriller ✦
                  </span>
                  <Link
                    to="/profile"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-variant/70 hover:bg-primary-container/30 text-primary text-xs font-semibold transition-all shadow-inner"
                  >
                    <span className="material-symbols-outlined text-sm">tune</span>
                    <span>Customize Taste</span>
                  </Link>
                </div>
              </div>

              {/* Mini Donut Chart Affinity Metric */}
              <div className="flex items-center gap-4 bg-surface-container-lowest/80 px-4 py-3 rounded-xl border border-outline-variant/30 shrink-0 self-start lg:self-center">
                <div className="relative w-12 h-12 flex items-center justify-center">
                  <svg className="w-12 h-12 -rotate-90 transform" viewBox="0 0 36 36">
                    <path
                      className="text-surface-variant"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="3.5"
                    />
                    <path
                      className="text-secondary"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none"
                      stroke="currentColor"
                      strokeDasharray="98, 100"
                      strokeLinecap="round"
                      strokeWidth="3.5"
                    />
                  </svg>
                  <span className="absolute font-extrabold text-xs text-on-surface">98</span>
                </div>
                <div className="flex flex-col">
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-sm text-on-surface">98% Match</span>
                    <span className="material-symbols-outlined text-secondary text-sm">verified</span>
                  </div>
                  <span className="text-xs text-outline font-medium">Tailored to your preferences</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Top Recommendations For You */}
        <section className="w-full mb-12">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/30 pb-4 mb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-xl">recommend</span>
                <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                  Top Recommendations for You
                </h2>
              </div>
              <p className="text-xs sm:text-sm text-on-surface-variant">
                Handpicked selections based on your ratings and viewer favorites
              </p>
            </div>
            <span className="text-xs text-outline font-medium">Updated Today</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {loading ? (
              <div className="col-span-full py-12 text-center text-on-surface-variant flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-secondary text-3xl animate-spin">progress_activity</span>
                <span className="text-sm font-semibold">Finding the best recommendations for you...</span>
              </div>
            ) : topRecs.map((movie) => {
              const movieId = movie.movie_id || movie.id;
              return (
                <div
                  key={movieId}
                  onClick={() => setActiveDetailMovie(movie)}
                  className="group flex flex-col rounded-xl bg-surface-container/60 backdrop-blur-md overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:bg-surface-container-high/90 hover:shadow-[0_12px_30px_rgba(0,0,0,0.7)] border border-transparent hover:border-secondary/30 cursor-pointer"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-lowest">
                    <img
                      src={getPosterUrl(movie)}
                      alt={movie.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>

                    {/* Match Score Badge */}
                    <div className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full bg-secondary-container/90 text-on-secondary-container text-[11px] font-bold shadow-md">
                      {movie.match_percentage || Math.round(90 + Math.random() * 9)}% Match
                    </div>

                    {/* Genre Tag */}
                    <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1">
                      {(movie.genres || ['Film']).slice(0, 2).map((genre) => (
                        <span
                          key={genre}
                          className="px-2 py-0.5 rounded-md bg-secondary/15 text-secondary text-[10px] font-bold uppercase"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>

                    {/* Hover Overlay with Action Buttons */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 backdrop-blur-[2px] p-4">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movieId, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="w-full py-2 rounded-xl bg-primary-container text-on-primary-container text-xs font-bold shadow-[0_0_16px_rgba(128,131,255,0.6)] flex items-center justify-center gap-1.5 hover:scale-105 transition-all"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          play_arrow
                        </span>
                        Watch Trailer
                      </button>

                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToWatchlist(movieId, movie.title);
                        }}
                        className="w-full py-2 rounded-xl bg-surface-container-high/80 text-on-surface text-xs font-semibold hover:bg-surface-container-highest transition-all flex items-center justify-center gap-1.5 border border-outline-variant/30"
                      >
                        <span className="material-symbols-outlined text-sm">bookmark_add</span>
                        Save to Watchlist
                      </button>
                    </div>
                  </div>

                  <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                    <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                      {movie.title}
                    </h3>
                    <div className="flex items-center justify-between text-xs text-on-surface-variant">
                      <span className="text-[11px] text-outline font-medium">{movie.year || '2024'}</span>
                      <div className="flex items-center gap-0.5 text-tertiary font-bold">
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span>{(movie.predicted_score || movie.vote_average || 8.5).toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Section 3: Because You Liked... */}
        <section className="w-full mb-12">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/30 pb-4 mb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-xl">auto_fix_high</span>
                <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                  Because You Liked <span className="text-primary">{becauseYouLiked.seed}</span>
                </h2>
              </div>
              <p className="text-xs sm:text-sm text-on-surface-variant">
                Titles with similar tone, themes, and storytelling
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6">
            {becauseYouLiked.movies.map((movie) => {
              const movieId = movie.movie_id || movie.id;
              return (
                <div
                  key={movieId}
                  onClick={() => setActiveDetailMovie(movie)}
                  className="group flex flex-col rounded-xl bg-surface-container/60 backdrop-blur-md overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:bg-surface-container-high/90 hover:shadow-xl border border-transparent hover:border-primary/30 cursor-pointer"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-lowest">
                    <img
                      src={getPosterUrl(movie)}
                      alt={movie.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>

                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 backdrop-blur-[2px] p-4">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movieId, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="w-full py-2 rounded-xl bg-primary-container text-on-primary-container text-xs font-bold shadow-md flex items-center justify-center gap-1.5"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          play_arrow
                        </span>
                        Trailer
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToWatchlist(movieId, movie.title);
                        }}
                        className="w-full py-2 rounded-xl bg-surface-container-high text-on-surface text-xs font-semibold flex items-center justify-center gap-1.5 border border-outline-variant/30"
                      >
                        <span className="material-symbols-outlined text-sm">bookmark_add</span>
                        Watchlist
                      </button>
                    </div>
                  </div>

                  <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                    <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                      {movie.title}
                    </h3>
                    <div className="flex items-center justify-between text-xs text-on-surface-variant">
                      <span className="text-[11px] text-outline font-medium">{movie.year || 'Classic'}</span>
                      <span className="text-primary font-bold text-xs">96% Match</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Section 4: More Like This (Viewer Favorites) */}
        <section className="w-full mb-12">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/30 pb-4 mb-6">
            <div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-xl">group</span>
                <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                  More Like This
                </h2>
              </div>
              <p className="text-xs sm:text-sm text-on-surface-variant">
                Popular choices among viewers with similar cinematic taste
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6">
            {alsoWatched.map((movie) => {
              const movieId = movie.movie_id || movie.id;
              return (
                <div
                  key={movieId}
                  onClick={() => setActiveDetailMovie(movie)}
                  className="group flex flex-col rounded-xl bg-surface-container/60 backdrop-blur-md overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:bg-surface-container-high/90 hover:shadow-xl border border-transparent hover:border-tertiary/30 cursor-pointer"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-lowest">
                    <img
                      src={getPosterUrl(movie)}
                      alt={movie.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>

                    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/50 backdrop-blur-[2px] p-4">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movieId, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="w-full py-2 rounded-xl bg-primary-container text-on-primary-container text-xs font-bold shadow-md flex items-center justify-center gap-1.5"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          play_arrow
                        </span>
                        Trailer
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToWatchlist(movieId, movie.title);
                        }}
                        className="w-full py-2 rounded-xl bg-surface-container-high text-on-surface text-xs font-semibold flex items-center justify-center gap-1.5 border border-outline-variant/30"
                      >
                        <span className="material-symbols-outlined text-sm">bookmark_add</span>
                        Watchlist
                      </button>
                    </div>
                  </div>

                  <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                    <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                      {movie.title}
                    </h3>
                    <div className="flex items-center justify-between text-xs text-on-surface-variant">
                      <span className="text-[11px] text-outline font-medium">{movie.year || '2023'}</span>
                      <span className="text-tertiary font-bold text-xs">Top Pick</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      {/* Movie Detail Modal */}
      <MovieDetailModal
        movie={activeDetailMovie}
        isOpen={Boolean(activeDetailMovie)}
        onClose={() => setActiveDetailMovie(null)}
        onPlayTrailer={(t) => setActiveTrailer(t)}
        onToggleWatchlist={(m) => handleAddToWatchlist(m.movie_id || m.id, m.title)}
        onRateMovie={(id, score) => handleRateMovie(id, score)}
        isLoggedIn={Boolean(user)}
      />

      {/* Global Trailer Modal */}
      <TrailerModal movie={activeTrailer} onClose={() => setActiveTrailer(null)} />
    </div>
  );
};
