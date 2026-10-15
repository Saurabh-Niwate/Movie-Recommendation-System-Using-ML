import React, { useEffect, useState, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { TrailerModal, TrailerMovieTarget } from '../components/modal/TrailerModal';
import { MovieDetailModal, MovieDetailTarget } from '../components/modal/MovieDetailModal';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface RankedMovie {
  id: number;
  title: string;
  year?: number;
  genres: string[];
  vote_average: number;
  vote_count?: number;
  poster_path?: string | null;
  backdrop_path?: string | null;
  trailer_key?: string | null;
  director?: string;
  user_rating?: number;
  synopsis?: string;
  overview?: string;
  cast?: string[];
  runtime?: number;
}

export const RankingsPage: React.FC = () => {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [movies, setMovies] = useState<RankedMovie[]>([]);
  const [userRatings, setUserRatings] = useState<Map<number, number>>(new Map());
  const [selectedPeriod, setSelectedPeriod] = useState<string>(searchParams.get('period') || 'all-time');
  const [selectedGenre, setSelectedGenre] = useState<string>(searchParams.get('genre') || 'all');
  const [searchQuery, setSearchQuery] = useState<string>(searchParams.get('search') || '');
  const [activeTrailer, setActiveTrailer] = useState<TrailerMovieTarget | null>(null);
  const [activeDetailMovie, setActiveDetailMovie] = useState<MovieDetailTarget | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [toast, setToast] = useState<string | null>(null);

  const getPosterUrl = (m: RankedMovie) => {
    if (m.poster_path && m.poster_path.startsWith('http')) return m.poster_path;
    if (m.poster_path && m.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${m.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${m.id}.jpg`;
  };

  useEffect(() => {
    // Load top rated catalog (fetch full catalog for rich filtering)
    apiFetch<{ items: RankedMovie[] }>('/movies?limit=120&sort=top_rated')
      .then((data) => {
        const sorted = (data.items || []).sort((a, b) => b.vote_average - a.vote_average);
        setMovies(sorted);
      })
      .catch((err) => {
        console.error('Failed to load rankings:', err);
      })
      .finally(() => {
        setLoading(false);
      });

    // If authenticated, load existing ratings
    if (user) {
      apiFetch<Array<{ movie_id: number; rating: number }>>('/ratings')
        .then((ratings) => {
          const map = new Map<number, number>();
          (ratings || []).forEach((r) => map.set(r.movie_id, r.rating));
          setUserRatings(map);
        })
        .catch(() => {});
    }
  }, [user]);

  const handleRateMovie = async (movieId: number, title: string, stars: number) => {
    if (!user) {
      setToast('Please sign in to submit ratings.');
      setTimeout(() => setToast(null), 3000);
      return;
    }

    const nextMap = new Map(userRatings);
    nextMap.set(movieId, stars);
    setUserRatings(nextMap);

    try {
      await apiFetch('/ratings', {
        method: 'POST',
        body: JSON.stringify({ movie_id: movieId, rating: stars }),
      });
      setToast(`Rated "${title}" ${stars}★ — Updated user profile`);
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      console.warn('Rating submission error:', err);
    }
  };

  const handleAddToWatchlist = async (movieId: number, title: string) => {
    if (!user) {
      setToast('Please sign in to use your watchlist.');
      setTimeout(() => setToast(null), 3000);
      return;
    }

    try {
      await apiFetch(`/watchlist/${movieId}`, { method: 'POST' });
      setToast(`Added "${title}" to your Watchlist`);
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      console.warn('Watchlist error:', err);
    }
  };

  // Filtered and searched movies with active period support
  const filteredRankings = useMemo(() => {
    let result = movies.filter((m) => {
      const matchGenre =
        selectedGenre === 'all' ||
        (selectedGenre.toLowerCase() === 'sci-fi'
          ? m.genres.some((g) => {
              const lower = g.toLowerCase();
              return lower.includes('sci') || lower.includes('science');
            })
          : m.genres.some((g) => g.toLowerCase().includes(selectedGenre.toLowerCase())));

      const term = searchQuery.trim().toLowerCase();
      const matchSearch =
        !term ||
        m.title.toLowerCase().includes(term) ||
        (m.director && m.director.toLowerCase().includes(term)) ||
        m.genres.some((g) => g.toLowerCase().includes(term));

      if (!matchGenre || !matchSearch) return false;

      if (selectedPeriod === 'cyberpunk') {
        return m.genres.some((g) => {
          const l = g.toLowerCase();
          return l.includes('sci') || l.includes('action') || l.includes('thriller');
        });
      }
      return true;
    });

    // Apply period sorting & prioritization
    if (selectedPeriod === 'anticipated') {
      // Sort newest releases first (2024, 2023, 2022...)
      return [...result].sort((a, b) => (b.year || 0) - (a.year || 0));
    }
    if (selectedPeriod === 'trending') {
      // Sort by vote count / popularity volume
      return [...result].sort((a, b) => (b.vote_count || 0) - (a.vote_count || 0));
    }
    // 'all-time' or default: sort by vote_average descending
    return [...result].sort((a, b) => b.vote_average - a.vote_average);
  }, [movies, selectedPeriod, selectedGenre, searchQuery]);

  const topPodium = filteredRankings.slice(0, 3);
  const remainingRankings = filteredRankings.slice(3);

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative selection:bg-secondary/30 selection:text-secondary pb-24">
      {/* Background radial glows */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      {/* Floating Notification Toast */}
      {toast && (
        <div className="fixed top-24 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-container-high/90 backdrop-blur-xl border border-secondary/30 text-on-surface text-sm font-semibold shadow-xl animate-fade-in">
          <span className="material-symbols-outlined text-secondary text-base">info</span>
          <span>{toast}</span>
        </div>
      )}

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <div className="flex flex-col w-full gap-8">
          {/* Header & Controls Section */}
          <section className="relative w-full flex flex-col gap-6 pt-6">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div className="flex flex-col gap-1 max-w-3xl">
                <div className="flex items-center gap-1.5">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface-container-high/80 text-secondary text-xs uppercase tracking-widest font-bold shadow-[0_0_12px_rgba(76,215,246,0.25)]">
                    <span className="material-symbols-outlined text-xs">stars</span>
                    Global Leaderboard
                  </span>
                </div>
                <h1 className="text-3xl sm:text-5xl font-extrabold text-on-surface tracking-tight">
                  Top Rated Movies
                </h1>
              </div>
            </div>

            {/* Period Tabs & Search Input */}
            <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 p-2 rounded-2xl bg-surface-container-low/90 backdrop-blur-lg border border-outline-variant/30">
              <div className="flex items-center gap-1 overflow-x-auto pb-1 lg:pb-0">
                {[
                  { label: 'All Time Legendary', value: 'all-time' },
                  { label: 'Trending This Month', value: 'trending' },
                  { label: 'Anticipated 2024–2025', value: 'anticipated' },
                  { label: 'Hidden Cyberpunk Gems', value: 'cyberpunk' },
                ].map((period) => (
                  <button
                    key={period.value}
                    type="button"
                    onClick={() => setSelectedPeriod(period.value)}
                    className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all whitespace-nowrap ${
                      selectedPeriod === period.value
                        ? 'bg-primary-container text-on-primary-container shadow-[0_0_12px_rgba(128,131,255,0.35)]'
                        : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/60'
                    }`}
                  >
                    {period.label}
                  </button>
                ))}
              </div>

              <div className="relative w-full lg:w-80 shrink-0">
                <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-base pointer-events-none">
                  search
                </span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search title, director, theme..."
                  className="w-full pl-9 pr-4 py-2 rounded-xl bg-surface-container-highest/60 text-on-surface placeholder:text-outline text-xs sm:text-sm focus:outline-none focus:bg-surface-container-high focus:shadow-[0_0_14px_rgba(76,215,246,0.3)] transition-all border border-outline-variant/20"
                />
              </div>
            </div>

            {/* Genre Filter Pills */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <span className="text-xs font-bold text-outline uppercase tracking-wider mr-2 hidden sm:inline">
                Filter By:
              </span>
              {[
                { label: 'All Genres', value: 'all' },
                { label: 'Sci-Fi', value: 'Sci-Fi' },
                { label: 'Action', value: 'Action' },
                { label: 'Drama', value: 'Drama' },
                { label: 'Psychological Thriller', value: 'Thriller' },
                { label: 'Animation', value: 'Animation' },
                { label: 'Adventure', value: 'Adventure' },
              ].map((g) => (
                <button
                  key={g.value}
                  type="button"
                  onClick={() => setSelectedGenre(g.value)}
                  className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                    selectedGenre === g.value
                      ? 'bg-secondary/15 text-secondary shadow-[0_0_10px_rgba(76,215,246,0.2)] border border-secondary/30'
                      : 'bg-surface-container-high/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container-highest border border-transparent'
                  }`}
                >
                  {g.label}
                </button>
              ))}
            </div>
          </section>

          {/* Podium / Top 3 Featured Spotlight Bento */}
          {topPodium.length > 0 && (
            <section className="relative w-full">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                {/* Rank #1: Big Banner */}
                {topPodium[0] && (
                  <div
                    onClick={() => setActiveDetailMovie(topPodium[0])}
                    className="lg:col-span-7 relative group rounded-2xl overflow-hidden bg-surface-container-low shadow-xl flex flex-col justify-end min-h-[440px] border border-outline-variant/30 cursor-pointer"
                  >
                    <div
                      className="absolute inset-0 bg-cover bg-center transition-transform duration-700 ease-out group-hover:scale-105"
                      style={{
                        backgroundImage: `url('${topPodium[0].backdrop_path || getPosterUrl(topPodium[0])}')`,
                      }}
                    ></div>
                    <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/80 to-transparent"></div>
                    <div className="absolute inset-0 bg-gradient-to-r from-surface-container-lowest/90 via-surface-container-lowest/40 to-transparent"></div>

                    {/* Top Badge Bar */}
                    <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20">
                      <div className="flex items-center gap-2">
                        <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-tertiary-container text-on-tertiary-container font-extrabold text-base shadow-[0_0_16px_rgba(255,185,95,0.4)]">
                          #1
                        </span>
                        <span className="px-3 py-1 rounded-full bg-surface-container-high/80 backdrop-blur-md text-tertiary text-xs uppercase tracking-widest font-bold flex items-center gap-1 shadow-sm">
                          <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                            workspace_premium
                          </span>
                          Top Pick
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToWatchlist(topPodium[0].id, topPodium[0].title);
                        }}
                        className="w-10 h-10 rounded-full bg-surface-container-high/70 backdrop-blur-md text-on-surface hover:text-secondary hover:bg-surface-container-highest transition-all flex items-center justify-center shadow-sm"
                        title="Add to Watchlist"
                      >
                        <span className="material-symbols-outlined text-lg">bookmark_add</span>
                      </button>
                    </div>

                    {/* Content Foreground */}
                    <div className="relative z-20 p-6 sm:p-8 flex flex-col gap-4">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-surface-container-highest/80 text-on-surface-variant text-xs uppercase font-semibold">
                          {topPodium[0].year || '2024'}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-secondary/15 text-secondary text-xs uppercase font-semibold">
                          {topPodium[0].genres.slice(0, 2).join(' / ') || 'Masterpiece'}
                        </span>
                      </div>

                      <div className="flex flex-col gap-1">
                        <h2 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight group-hover:text-primary transition-colors">
                          {topPodium[0].title}
                        </h2>
                        <span className="text-xs sm:text-sm text-on-surface-variant">
                          Directed by {topPodium[0].director || 'Auteur Visionary'} • Master Benchmark
                        </span>
                      </div>

                      {/* Key Metrics Trio */}
                      <div className="grid grid-cols-3 gap-3 pt-1">
                        <div className="flex flex-col p-3 rounded-xl bg-surface-container-high/60 backdrop-blur-md shadow-sm">
                          <span className="text-[10px] text-outline uppercase font-semibold">Consensus</span>
                          <span className="text-base text-tertiary font-bold">9.9 /10</span>
                        </div>
                        <div className="flex flex-col p-3 rounded-xl bg-surface-container-high/60 backdrop-blur-md shadow-sm">
                          <span className="text-[10px] text-outline uppercase font-semibold">Score</span>
                          <span className="text-base text-secondary font-bold">
                            {topPodium[0].vote_average.toFixed(1)} /10
                          </span>
                        </div>
                        <div className="flex flex-col p-3 rounded-xl bg-surface-container-high/60 backdrop-blur-md shadow-sm">
                          <span className="text-[10px] text-outline uppercase font-semibold">Curator Status</span>
                          <span className="text-base text-primary font-bold">Verified ✦</span>
                        </div>
                      </div>

                      {/* Action Bar */}
                      <div className="flex items-center justify-between pt-2">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveTrailer({ id: topPodium[0].id, title: topPodium[0].title, trailer_key: topPodium[0].trailer_key });
                          }}
                          className="px-5 py-2.5 rounded-xl bg-primary-container text-on-primary-container text-xs sm:text-sm font-bold hover:brightness-110 shadow-[0_0_16px_rgba(128,131,255,0.4)] flex items-center gap-2 transition-all"
                        >
                          <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
                            play_circle
                          </span>
                          <span>Watch Trailer</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Rank #2 & #3 Split Panel */}
                <div className="lg:col-span-5 flex flex-col gap-6 justify-between">
                  {topPodium.slice(1, 3).map((item, idx) => (
                    <div
                      key={item.id}
                      onClick={() => setActiveDetailMovie(item)}
                      className="relative group rounded-2xl overflow-hidden bg-surface-container-low shadow-lg flex flex-col justify-end p-6 min-h-[205px] border border-outline-variant/30 cursor-pointer"
                    >
                      <div
                        className="absolute inset-0 bg-cover bg-center transition-transform duration-700 ease-out group-hover:scale-105"
                        style={{
                          backgroundImage: `url('${item.backdrop_path || getPosterUrl(item)}')`,
                        }}
                      ></div>
                      <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/85 to-transparent"></div>

                      <div className="relative z-10 flex flex-col gap-2">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-surface-container-highest text-on-surface font-extrabold text-sm shadow">
                            #{idx + 2}
                          </span>
                          <div className="flex items-center gap-1 bg-surface-container-high/80 px-2.5 py-0.5 rounded-full">
                            <span className="material-symbols-outlined text-xs text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>
                              star
                            </span>
                            <span className="text-xs font-bold text-on-surface">{item.vote_average.toFixed(1)}</span>
                          </div>
                        </div>

                        <div>
                          <h3 className="text-lg font-bold text-on-surface group-hover:text-secondary transition-colors truncate">
                            {item.title}
                          </h3>
                          <span className="text-xs text-on-surface-variant">
                            {item.year || '2023'} • {item.genres.slice(0, 2).join(' / ')}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 pt-1">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveTrailer({ id: item.id, title: item.title, trailer_key: item.trailer_key });
                            }}
                            className="px-3.5 py-1.5 rounded-lg bg-primary-container text-on-primary-container text-xs font-semibold flex items-center gap-1 shadow-sm"
                          >
                            <span className="material-symbols-outlined text-sm">play_arrow</span>
                            Trailer
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleAddToWatchlist(item.id, item.title);
                            }}
                            className="px-3.5 py-1.5 rounded-lg bg-surface-container text-on-surface text-xs font-semibold hover:bg-surface-container-high transition-colors"
                          >
                            + Watchlist
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Full Leaderboard Table / Rows */}
          <section className="w-full">
            <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30 mb-6">
              <h2 className="text-xl font-bold text-on-surface">Complete Rankings Table</h2>
              <span className="text-xs text-outline">{filteredRankings.length} Titles Indexed</span>
            </div>

            <div className="space-y-3">
              {loading ? (
                <div className="py-12 text-center text-on-surface-variant flex flex-col items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-3xl animate-spin">progress_activity</span>
                  <span className="text-sm font-semibold">Calculating global ratings leaderboard...</span>
                </div>
              ) : remainingRankings.map((movie, idx) => {
                const rankNum = idx + 4;
                const userScore = userRatings.get(movie.id) || 0;

                return (
                  <div
                    key={movie.id}
                    onClick={() => setActiveDetailMovie(movie)}
                    className="group flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-surface-container-low/70 hover:bg-surface-container-high/90 backdrop-blur-md border border-outline-variant/20 hover:border-secondary/30 transition-all duration-200 cursor-pointer"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <span className="font-extrabold text-base text-outline w-8 text-center shrink-0">
                        #{rankNum}
                      </span>

                      <div className="w-12 h-16 rounded-lg overflow-hidden bg-surface-container-lowest shrink-0 shadow">
                        <img
                          src={getPosterUrl(movie)}
                          alt={movie.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>

                      <div className="flex flex-col min-w-0">
                        <h3 className="font-bold text-sm text-on-surface truncate group-hover:text-primary transition-colors">
                          {movie.title}
                        </h3>
                        <div className="flex items-center gap-2 text-xs text-on-surface-variant">
                          <span>{movie.year || 'Classic'}</span>
                          <span>•</span>
                          <span className="truncate">{movie.genres.slice(0, 2).join(', ')}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 sm:gap-6 self-end sm:self-auto shrink-0">
                      {/* Interactive Star Rating */}
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            key={star}
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRateMovie(movie.id, movie.title, star);
                            }}
                            className="text-tertiary hover:scale-125 transition-transform"
                            title={`Rate ${star} Stars`}
                          >
                            <span
                              className="material-symbols-outlined text-lg"
                              style={{
                                fontVariationSettings: star <= userScore ? "'FILL' 1" : "'FILL' 0",
                              }}
                            >
                              star
                            </span>
                          </button>
                        ))}
                      </div>

                      {/* Global Rating Score */}
                      <div className="flex items-center gap-1 text-xs font-bold text-tertiary bg-surface-container px-2.5 py-1 rounded-lg">
                        <span>★</span>
                        <span>{movie.vote_average.toFixed(1)}</span>
                      </div>

                      {/* Trailer Button */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movie.id, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="px-3 py-1.5 rounded-lg bg-surface-container-highest hover:bg-primary-container hover:text-on-primary-container text-xs font-semibold transition-all flex items-center gap-1 text-on-surface"
                      >
                        <span className="material-symbols-outlined text-sm">play_arrow</span>
                        <span className="hidden sm:inline">Trailer</span>
                      </button>

                      {/* Save to Watchlist */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToWatchlist(movie.id, movie.title);
                        }}
                        className="p-1.5 rounded-lg text-outline hover:text-secondary hover:bg-surface-container transition-colors"
                        title="Add to Watchlist"
                      >
                        <span className="material-symbols-outlined text-lg">bookmark_add</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </div>
      </main>

      {/* Movie Detail Modal */}
      <MovieDetailModal
        movie={activeDetailMovie}
        isOpen={Boolean(activeDetailMovie)}
        onClose={() => setActiveDetailMovie(null)}
        onPlayTrailer={(t) => setActiveTrailer(t)}
        onToggleWatchlist={(m) => handleAddToWatchlist(m.movie_id || m.id, m.title)}
        onRateMovie={(id, score) => {
          const target = movies.find((m) => m.id === id);
          handleRateMovie(id, target?.title || 'Film', score);
        }}
        isLoggedIn={Boolean(user)}
      />

      {/* Global Trailer Video Modal */}
      <TrailerModal movie={activeTrailer} onClose={() => setActiveTrailer(null)} />
    </div>
  );
};
