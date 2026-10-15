import React, { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { TrailerModal, TrailerMovieTarget } from '../components/modal/TrailerModal';
import { MovieDetailModal, MovieDetailTarget } from '../components/modal/MovieDetailModal';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface WatchlistItem {
  id: number;
  movie_id?: number;
  title: string;
  year?: number;
  genres: string[];
  vote_average: number;
  poster_path?: string | null;
  backdrop_path?: string | null;
  trailer_key?: string | null;
  runtime?: number;
  director?: string;
  synopsis?: string;
  overview?: string;
  cast?: string[];
  added_at?: string;
}

export const WatchlistPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'highest' | 'newest' | 'year'>('highest');
  const [activeTrailer, setActiveTrailer] = useState<TrailerMovieTarget | null>(null);
  const [activeDetailMovie, setActiveDetailMovie] = useState<MovieDetailTarget | null>(null);
  const [loading, setLoading] = useState(true);

  const getPosterUrl = (m: WatchlistItem) => {
    const mid = m.movie_id || m.id;
    if (m.poster_path && m.poster_path.startsWith('http')) return m.poster_path;
    if (m.poster_path && m.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${m.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${mid}.jpg`;
  };

  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = () => {
    apiFetch<WatchlistItem[]>('/watchlist')
      .then((data) => {
        setItems(data || []);
      })
      .catch((err) => {
        console.error('Failed to load watchlist:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleRemove = async (movieId: number) => {
    // Optimistic removal
    setItems((prev) => prev.filter((item) => (item.movie_id || item.id) !== movieId));

    try {
      await apiFetch(`/watchlist/${movieId}`, {
        method: 'DELETE',
      });
    } catch (err) {
      console.error('Error removing from watchlist:', err);
      loadWatchlist(); // Rollback on error
    }
  };

  // Stats calculation
  const totalCount = items.length;
  const avgRating = totalCount
    ? (items.reduce((acc, it) => acc + (it.vote_average || 8.0), 0) / totalCount).toFixed(1)
    : '8.5';

  const filteredItems = useMemo(() => {
    let result = [...items];

    if (selectedFilter === 'top-rated') {
      result = result.filter((m) => m.vote_average >= 8.5);
    } else if (selectedFilter === 'scifi') {
      result = result.filter((m) =>
        m.genres?.some((g) => g.toLowerCase().includes('sci-fi'))
      );
    }

    if (sortBy === 'highest') {
      result.sort((a, b) => b.vote_average - a.vote_average);
    } else if (sortBy === 'year') {
      result.sort((a, b) => (b.year || 0) - (a.year || 0));
    }

    return result;
  }, [items, selectedFilter, sortBy]);

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative selection:bg-secondary/30 selection:text-secondary pb-24">
      {/* Background radial glow */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <div className="flex flex-col w-full mb-12">
          {/* Header Section */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-secondary/10 text-secondary text-xs uppercase tracking-wider font-bold shadow-[0_0_12px_rgba(76,215,246,0.2)]">
                  My List
                </span>
                <span className="text-outline text-xs uppercase tracking-widest font-semibold">
                  • {totalCount} Titles Saved
                </span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-on-surface tracking-tight">
                My Cinematic Watchlist
              </h1>
            </div>

            {/* View Controls & Sort Dropdown */}
            <div className="flex items-center gap-3 shrink-0 self-start md:self-auto">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="px-3.5 py-1.5 rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-xs font-semibold transition-all border border-outline-variant/30 flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-sm">arrow_back</span>
                <span>Back</span>
              </button>

              <div className="flex items-center p-1 bg-surface-container-low/80 backdrop-blur-md rounded-full border border-outline-variant/30">
                <button
                  type="button"
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-full transition-all ${
                    viewMode === 'grid'
                      ? 'bg-primary-container text-on-primary-container shadow-[0_0_12px_rgba(128,131,255,0.4)]'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                  title="Grid View"
                >
                  <span className="material-symbols-outlined text-base leading-none block">grid_view</span>
                </button>
                <button
                  type="button"
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-full transition-all ${
                    viewMode === 'list'
                      ? 'bg-primary-container text-on-primary-container shadow-[0_0_12px_rgba(128,131,255,0.4)]'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                  title="List View"
                >
                  <span className="material-symbols-outlined text-base leading-none block">view_agenda</span>
                </button>
              </div>

              {/* Sort Selector */}
              <div className="flex items-center gap-1 px-4 py-2 rounded-full bg-surface-container-high/60 backdrop-blur-md text-on-surface text-xs font-semibold border border-outline-variant/30">
                <span className="material-symbols-outlined text-sm text-secondary">sort</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-transparent outline-none cursor-pointer text-on-surface"
                >
                  <option value="highest" className="bg-surface-container-high">Highest Rated</option>
                  <option value="year" className="bg-surface-container-high">Release Year</option>
                </select>
              </div>
            </div>
          </div>

          {/* Telemetry Stats Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            <div className="p-4 rounded-xl bg-surface-container-low/70 backdrop-blur-xl border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant mb-1">
                <span className="text-xs uppercase tracking-wider text-outline font-semibold">Total Saved</span>
                <span className="material-symbols-outlined text-secondary text-lg">bookmark</span>
              </div>
              <span className="text-2xl font-bold text-on-surface">{totalCount} Films</span>
              <div className="w-full bg-surface-container-high rounded-full h-1 mt-2 overflow-hidden">
                <div className="bg-gradient-to-r from-secondary to-primary h-full w-[80%] rounded-full shadow-[0_0_8px_rgba(76,215,246,0.6)]"></div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface-container-low/70 backdrop-blur-xl border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant mb-1">
                <span className="text-xs uppercase tracking-wider text-outline font-semibold">Avg Rating</span>
                <span className="material-symbols-outlined text-tertiary text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                  star
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-tertiary to-primary">
                  {avgRating} ★
                </span>
                <span className="text-xs text-tertiary font-semibold">Highly rated</span>
              </div>
              <div className="w-full bg-surface-container-high rounded-full h-1 mt-2 overflow-hidden">
                <div className="bg-tertiary h-full w-[88%] rounded-full"></div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-surface-container-low/70 backdrop-blur-xl border border-outline-variant/20 flex flex-col justify-between">
              <div className="flex items-center justify-between text-on-surface-variant mb-1">
                <span className="text-xs uppercase tracking-wider text-outline font-semibold">Ready to Stream</span>
                <span className="material-symbols-outlined text-primary text-lg">play_circle</span>
              </div>
              <span className="text-2xl font-bold text-on-surface">{totalCount} Ready</span>
              <div className="w-full bg-surface-container-high rounded-full h-1 mt-2 overflow-hidden">
                <div className="bg-primary-container h-full w-[100%] rounded-full"></div>
              </div>
            </div>
          </div>

          {/* Filter Pills Rail */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none mb-6">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                selectedFilter === 'all'
                  ? 'bg-secondary/15 text-secondary shadow-[0_0_12px_rgba(76,215,246,0.2)] border border-secondary/30'
                  : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => setSelectedFilter('top-rated')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                selectedFilter === 'top-rated'
                  ? 'bg-secondary/15 text-secondary shadow-[0_0_12px_rgba(76,215,246,0.2)] border border-secondary/30'
                  : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Top Rated (★ 8.5+)
            </button>
            <button
              onClick={() => setSelectedFilter('scifi')}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                selectedFilter === 'scifi'
                  ? 'bg-secondary/15 text-secondary shadow-[0_0_12px_rgba(76,215,246,0.2)] border border-secondary/30'
                  : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
              }`}
            >
              Sci-Fi &amp; Cyberpunk
            </button>
          </div>

          {/* Empty State */}
          {filteredItems.length === 0 && !loading && (
            <div className="py-20 px-8 text-center bg-surface-container-low/50 backdrop-blur-xl rounded-2xl border border-outline-variant/30 flex flex-col items-center gap-4">
              <span className="material-symbols-outlined text-6xl text-outline">bookmark_border</span>
              <h2 className="text-xl font-bold text-on-surface">Your Watchlist is Empty</h2>
              <p className="text-sm text-on-surface-variant max-w-md">
                Browse our curated recommendations or explore the top rated list to save films for later viewing.
              </p>
              <div className="flex items-center gap-4 pt-2">
                <Link
                  to="/"
                  className="px-6 py-2.5 rounded-full bg-primary-container text-on-primary-container font-semibold text-xs sm:text-sm hover:brightness-110 transition-all shadow-md"
                >
                  Explore Catalog
                </Link>
                {user && (
                  <Link
                    to="/feed"
                    className="px-6 py-2.5 rounded-full bg-surface-container-high text-on-surface font-semibold text-xs sm:text-sm hover:bg-surface-bright transition-all"
                  >
                    View Your Feed
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* Grid View of Watchlist */}
          {viewMode === 'grid' && filteredItems.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredItems.map((movie) => {
                const movieId = movie.movie_id || movie.id;

                return (
                  <div
                    key={movieId}
                    onClick={() => setActiveDetailMovie(movie)}
                    className="group relative rounded-2xl bg-surface-container-low/80 backdrop-blur-xl overflow-hidden shadow-lg hover:shadow-[0_16px_36px_-10px_rgba(128,131,255,0.3)] transition-all duration-300 flex flex-col border border-outline-variant/30 hover:border-secondary/30 cursor-pointer"
                  >
                    <div className="relative w-full aspect-[2/3] overflow-hidden bg-surface-container">
                      <img
                        src={getPosterUrl(movie)}
                        alt={movie.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out"
                        loading="lazy"
                        onError={(e) => {
                          (e.currentTarget as HTMLImageElement).src =
                            'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>

                      {/* Top Badges */}
                      <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container-lowest/80 backdrop-blur-md shadow-[0_0_14px_rgba(76,215,246,0.3)]">
                        <span className="material-symbols-outlined text-secondary text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span className="text-xs font-bold text-secondary">
                          ★ {(movie.vote_average || 8.0).toFixed(1)}
                        </span>
                      </div>

                      {/* Remove Button */}
                      <div className="absolute top-3 right-3 flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemove(movieId);
                          }}
                          className="p-1.5 rounded-full bg-surface-container-lowest/70 backdrop-blur-md text-outline hover:text-error hover:bg-error-container/40 transition-all shadow"
                          title="Remove from Watchlist"
                        >
                          <span className="material-symbols-outlined text-sm leading-none block">close</span>
                        </button>
                      </div>

                      {/* Floating Trailer Button on Hover */}
                      <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-surface-container-lowest/40 backdrop-blur-[2px]">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveTrailer({ id: movieId, title: movie.title, trailer_key: movie.trailer_key });
                          }}
                          className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-xs font-bold shadow-[0_0_20px_rgba(128,131,255,0.6)] transform translate-y-2 group-hover:translate-y-0 transition-transform"
                        >
                          <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
                            play_arrow
                          </span>
                          <span>Watch Trailer</span>
                        </button>
                      </div>

                      {/* Quality & Formats bottom tag */}
                      <div className="absolute bottom-2 left-3 right-3 flex items-center justify-between text-outline text-[10px]">
                        <div className="flex items-center gap-1">
                          <span className="px-1.5 py-0.5 rounded bg-surface-container-highest/80 text-on-surface-variant font-mono">
                            4K
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-surface-container-highest/80 text-on-surface-variant font-mono">
                            IMAX
                          </span>
                        </div>
                        <span className="text-on-surface-variant font-medium">2h 15m</span>
                      </div>
                    </div>

                    {/* Metadata Body */}
                    <div className="p-4 flex-1 flex flex-col justify-between">
                      <div>
                        <div className="flex items-baseline justify-between gap-2 mb-1">
                          <h3 className="font-bold text-sm text-on-surface tracking-tight truncate">
                            {movie.title}
                          </h3>
                          <span className="text-xs text-outline shrink-0">{movie.year || '2024'}</span>
                        </div>
                        <p className="text-xs text-on-surface-variant truncate mb-2">
                          {(movie.genres || []).slice(0, 2).join(' / ') || 'Cinema'}
                        </p>
                      </div>

                      {/* Stream Options + Rating Action */}
                      <div className="pt-2 flex items-center justify-between border-t border-outline-variant/20 -mx-4 -mb-4 px-4 py-2 bg-surface-container-high/40">
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <span className="uppercase text-outline font-semibold">Stream on</span>
                          <span className="px-2 py-0.5 rounded bg-[#4b0082]/40 text-[#d8b4fe] font-bold">MAX</span>
                        </div>
                        <div className="flex items-center gap-1 text-tertiary text-xs font-bold">
                          <span>★</span>
                          <span>{(movie.vote_average || 8.0).toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* List View of Watchlist */}
          {viewMode === 'list' && filteredItems.length > 0 && (
            <div className="space-y-3">
              {filteredItems.map((movie) => {
                const movieId = movie.movie_id || movie.id;

                return (
                  <div
                    key={movieId}
                    onClick={() => setActiveDetailMovie(movie)}
                    className="flex items-center justify-between gap-4 p-4 rounded-xl bg-surface-container-low/70 backdrop-blur-md border border-outline-variant/20 hover:border-secondary/30 transition-all cursor-pointer"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="w-12 h-16 rounded-lg overflow-hidden bg-surface-container shrink-0">
                        <img
                          src={getPosterUrl(movie)}
                          alt={movie.title}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.currentTarget as HTMLImageElement).src =
                              'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80';
                          }}
                        />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-bold text-sm text-on-surface truncate">{movie.title}</h3>
                        <p className="text-xs text-on-surface-variant">
                          {movie.year || '2024'} • {(movie.genres || []).slice(0, 2).join(', ')}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movieId, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="px-3 py-1.5 rounded-lg bg-primary-container text-on-primary-container text-xs font-semibold flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-sm">play_arrow</span>
                        Trailer
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemove(movieId);
                        }}
                        className="p-1.5 rounded-lg text-outline hover:text-error hover:bg-error-container/30 transition-colors"
                      >
                        <span className="material-symbols-outlined text-base">delete</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>

      {/* Movie Detail Modal */}
      <MovieDetailModal
        movie={activeDetailMovie}
        isOpen={Boolean(activeDetailMovie)}
        onClose={() => setActiveDetailMovie(null)}
        onPlayTrailer={(t) => setActiveTrailer(t)}
        onToggleWatchlist={(m) => handleRemove(m.movie_id || m.id)}
        isLoggedIn={Boolean(user)}
      />

      {/* Global Trailer Video Modal */}
      <TrailerModal movie={activeTrailer} onClose={() => setActiveTrailer(null)} />
    </div>
  );
};
