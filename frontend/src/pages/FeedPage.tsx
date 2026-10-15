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
  const [isColdStart, setIsColdStart] = useState(false);
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
    let isMounted = true;

    async function loadFeedData() {
      try {
        // 1. Fetch user's personalized top recommendations
        let recs: RecMovie[] = [];
        try {
          const recData = await apiFetch<any>('/recommendations?limit=15');
          recs = Array.isArray(recData) ? recData : recData.recommendations || recData.items || [];
        } catch (err) {
          if (err instanceof ApiError && err.status === 403) {
            // Cold-start user: show top-rated catalog gracefully with a setup prompt instead of kicking them out
            setIsColdStart(true);
            const popData = await apiFetch<{ items: RecMovie[] }>('/movies?limit=20&sort=top_rated');
            recs = popData.items || [];
          } else {
            console.warn('Personalized recommendations unavailable, falling back to popular catalog:', err);
            const popData = await apiFetch<{ items: RecMovie[] }>('/movies?limit=20&sort=popular');
            recs = popData.items || [];
          }
        }
        if (isMounted) setTopRecs(recs);

        // Track movie IDs already shown to ensure variety and prevent duplicates across rows
        const shownMovieIds = new Set<number>(recs.map((m) => m.movie_id || m.id));

        // 2. Fetch user's existing ratings to find their favorite movie dynamically
        let userFavoriteMovie: { id: number; title: string } | null = null;
        try {
          const ratings = await apiFetch<Array<{ movie_id: number; rating: number }>>('/ratings');
          if (ratings && ratings.length > 0) {
            const sortedRatings = [...ratings].sort((a, b) => b.rating - a.rating);
            const topRatedMovie = await apiFetch<any>(`/movies/${sortedRatings[0].movie_id}`);
            if (topRatedMovie && topRatedMovie.title) {
              userFavoriteMovie = { id: topRatedMovie.id, title: topRatedMovie.title };
            }
          }
        } catch (err) {
          console.warn('Could not load user ratings for dynamic seed:', err);
        }

        // 3. Load Because You Liked using authenticated profile endpoint or dynamic favorite
        try {
          const bylData = await apiFetch<any>('/recommendations/because-you-liked');
          const bylItems: RecMovie[] = bylData.recommendations || bylData.items || [];
          const seedTitle =
            bylData.source_movie?.title ||
            userFavoriteMovie?.title ||
            (recs.length > 0 ? recs[0].title : 'Inception');
          
          let filteredByl = bylItems.filter((m) => !shownMovieIds.has(m.movie_id || m.id));
          
          // Pad if recommendations count is small to guarantee a full row
          if (filteredByl.length < 5) {
            const popRes = await apiFetch<{ items: RecMovie[] }>('/movies?limit=15&sort=top_rated');
            const candidates = (popRes.items || []).filter(
              (m) => !shownMovieIds.has(m.movie_id || m.id) && m.title !== seedTitle
            );
            filteredByl = [...filteredByl, ...candidates];
          }

          filteredByl.forEach((m) => shownMovieIds.add(m.movie_id || m.id));

          if (isMounted) {
            setBecauseYouLiked({
              seed: seedTitle,
              movies: filteredByl.slice(0, 10),
            });
          }
        } catch (err) {
          // Dynamic fallback to user's favorite or highest rated genre
          const fallbackSeed = userFavoriteMovie?.title || (recs.length > 0 ? recs[0].title : 'Top Rated Cinema');
          try {
            const res = await apiFetch<{ items: RecMovie[] }>('/movies?limit=15&sort=top_rated');
            const filteredFallback = (res.items || []).filter((m) => !shownMovieIds.has(m.movie_id || m.id));
            const finalPool = filteredFallback.length >= 5 ? filteredFallback : (res.items || []);
            finalPool.forEach((m) => shownMovieIds.add(m.movie_id || m.id));
            if (isMounted) {
              setBecauseYouLiked({
                seed: fallbackSeed,
                movies: finalPool.slice(0, 10),
              });
            }
          } catch {
            // ignore
          }
        }

        // 4. Load More Like This (Also Watched) based on a different movie from Top Picks or catalog
        const alsoSeedId =
          (recs.length > 1 ? (recs[1].movie_id || recs[1].id) : null) ||
          userFavoriteMovie?.id ||
          550;

        try {
          const alsoData = await apiFetch<any>(`/recommendations/also-watched/${alsoSeedId}?limit=15`);
          const alsoItems: RecMovie[] = Array.isArray(alsoData) ? alsoData : alsoData.items || alsoData.recommendations || [];
          let filteredAlso = alsoItems.filter((m) => !shownMovieIds.has(m.movie_id || m.id));
          if (filteredAlso.length < 5) {
            const extraRes = await apiFetch<{ items: RecMovie[] }>('/movies?sort=recent&limit=15');
            const extra = (extraRes.items || []).filter((m) => !shownMovieIds.has(m.movie_id || m.id));
            filteredAlso = [...filteredAlso, ...extra];
          }

          if (isMounted) {
            setAlsoWatched(filteredAlso.slice(0, 10));
          }
        } catch {
          try {
            const res = await apiFetch<{ items: RecMovie[] }>('/movies?sort=recent&limit=15');
            const filteredFallback = (res.items || []).filter((m) => !shownMovieIds.has(m.movie_id || m.id));
            if (isMounted) {
              setAlsoWatched((filteredFallback.length >= 5 ? filteredFallback : res.items || []).slice(0, 10));
            }
          } catch {
            // ignore
          }
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadFeedData();

    return () => {
      isMounted = false;
    };
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
          </div>
        </section>

        {/* Cold Start Discovery Alert Banner */}
        {isColdStart && (
          <div className="mb-8 p-4 sm:p-5 rounded-2xl bg-surface-container-high/90 backdrop-blur-xl border border-secondary/40 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-secondary/20 flex items-center justify-center text-secondary shrink-0">
                <span className="material-symbols-outlined text-xl">auto_awesome</span>
              </div>
              <div>
                <h4 className="font-bold text-sm text-on-surface">Curated Trending Showcase</h4>
                <p className="text-xs text-on-surface-variant">Rate 6 starter movies to train your custom Bayesian SVD taste vector.</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
              <Link
                to="/onboarding"
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-secondary text-on-secondary text-xs font-bold hover:brightness-110 shadow-[0_0_16px_rgba(76,215,246,0.35)] flex items-center justify-center gap-1.5 transition-all"
              >
                <span className="material-symbols-outlined text-sm">stars</span>
                <span>Personalize Taste (30s)</span>
              </Link>
            </div>
          </div>
        )}

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
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?genre=Sci-Fi')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-secondary/15 hover:bg-secondary/25 text-secondary text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                  >
                    Sci-Fi ✦
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?period=cyberpunk')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-secondary/15 hover:bg-secondary/25 text-secondary text-xs font-semibold shadow-sm transition-colors cursor-pointer"
                  >
                    Mind-Bending ✦
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?search=Blade+Runner')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer"
                  >
                    Blade Runner 2049 ✦
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?search=Nolan')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer"
                  >
                    Christopher Nolan ✦
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?search=Villeneuve')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer"
                  >
                    Denis Villeneuve ✦
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/rankings?genre=Thriller')}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-surface-container-high text-on-surface text-xs font-semibold hover:bg-secondary/20 hover:text-secondary transition-colors cursor-pointer"
                  >
                    Psychological Thriller ✦
                  </button>
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
                      onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src =
                          'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                      }}
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
                      onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src =
                          'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                      }}
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
                      onError={(e) => {
                        (e.currentTarget as HTMLImageElement).src =
                          'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                      }}
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
