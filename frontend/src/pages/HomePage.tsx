import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { TrailerModal, TrailerMovieTarget } from '../components/modal/TrailerModal';
import { MovieDetailModal, MovieDetailTarget } from '../components/modal/MovieDetailModal';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface MovieItem {
  id: number;
  title: string;
  year?: number;
  genres: string[];
  vote_average: number;
  vote_count?: number;
  poster_path?: string | null;
  backdrop_path?: string | null;
  trailer_key?: string | null;
  overview?: string;
  director?: string;
  cast?: string[];
  runtime?: number;
}

export const HomePage: React.FC = () => {
  const { user } = useAuth();

  const [topRated, setTopRated] = useState<MovieItem[]>([]);
  const [quickRoll, setQuickRoll] = useState<MovieItem[]>([]);
  const [allMovies, setAllMovies] = useState<MovieItem[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeTrailer, setActiveTrailer] = useState<TrailerMovieTarget | null>(null);
  const [activeDetailMovie, setActiveDetailMovie] = useState<MovieDetailTarget | null>(null);

  const getPosterUrl = (m: MovieItem) => {
    if (m.poster_path && m.poster_path.startsWith('http')) return m.poster_path;
    if (m.poster_path && m.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${m.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${m.id}.jpg`;
  };

  useEffect(() => {
    // Fetch starter & top rated movies
    apiFetch<{ items: MovieItem[]; total: number }>('/movies?limit=60&sort=popular')
      .then((data) => {
        const items = data.items || [];
        setAllMovies(items);

        // Top rated 5
        const sortedTop = [...items].sort((a, b) => b.vote_average - a.vote_average);
        setTopRated(sortedTop.slice(0, 5));

        // Quick roll 5 random
        rollNewSelection(items);
      })
      .catch((err) => {
        console.error('Failed to load movies:', err);
      });
  }, []);

  const rollNewSelection = (pool: MovieItem[] = allMovies) => {
    if (!pool.length) return;
    const shuffled = [...pool].sort(() => 0.5 - Math.random());
    setQuickRoll(shuffled.slice(0, 5));
  };

  // Keyboard shortcut: ⌘K or Ctrl+K focuses search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        document.getElementById('movie-search')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Filtered catalog when search or genre is active
  const filteredMovies = useMemo(() => {
    if (!searchQuery && selectedGenre === 'all') return null;

    return allMovies.filter((m) => {
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

      return matchGenre && matchSearch;
    });
  }, [allMovies, searchQuery, selectedGenre]);

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative overflow-x-hidden selection:bg-secondary/30 selection:text-secondary">
      {/* Background Glows */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 min-h-screen pb-16">
        <div className="flex flex-col w-full max-w-7xl mx-auto">
          {/* Hero & Discovery Section */}
          <section className="relative w-full pt-6 pb-8 flex flex-col gap-6 text-center">
            <div className="max-w-4xl mx-auto flex flex-col items-center gap-3">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-secondary/10 border border-secondary/20 text-secondary text-xs uppercase tracking-widest font-semibold shadow-sm">
                <span className="material-symbols-outlined text-sm">auto_awesome</span>
                Curated Film Discovery
              </div>

              <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold text-on-surface tracking-tight leading-tight">
                Discover Cinematic Masterpieces
              </h1>
            </div>

            {/* Hero Search Bar */}
            <div className="w-full flex items-center justify-center mt-2">
              <div className="relative w-full md:max-w-2xl group">
                <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none text-outline group-focus-within:text-secondary transition-colors">
                  <span className="material-symbols-outlined text-lg">search</span>
                </div>
                <input
                  id="movie-search"
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search movies by title, director, or genre... (e.g. Inception, Dune)"
                  className="w-full pl-12 pr-20 py-3.5 rounded-full bg-surface-container/70 backdrop-blur-xl text-on-surface placeholder:text-outline text-sm transition-all border border-outline-variant/30 shadow-md focus:outline-none focus:bg-surface-container-high/90 focus:border-secondary focus:shadow-[0_0_24px_rgba(76,215,246,0.25)]"
                />
                <div className="absolute inset-y-0 right-3.5 flex items-center">
                  <kbd className="px-2 py-1 rounded bg-surface-container-highest/80 text-on-surface-variant text-xs tracking-widest shadow-sm">
                    ⌘K
                  </kbd>
                </div>
              </div>
            </div>

            {/* Genre Filter Pills */}
            <div className="w-full flex items-center justify-center flex-wrap gap-2 pt-1 text-xs sm:text-sm">
              {[
                { label: 'All Genres', value: 'all' },
                { label: 'Sci-Fi', value: 'Sci-Fi' },
                { label: 'Action', value: 'Action' },
                { label: 'Drama', value: 'Drama' },
                { label: 'Thriller', value: 'Thriller' },
                { label: 'Animation', value: 'Animation' },
                { label: 'Adventure', value: 'Adventure' },
                { label: 'Comedy', value: 'Comedy' },
                { label: 'Crime', value: 'Crime' },
              ].map((g) => (
                <button
                  key={g.value}
                  type="button"
                  onClick={() => setSelectedGenre(g.value)}
                  className={`px-4 py-1.5 rounded-full font-semibold transition-all ${
                    selectedGenre === g.value
                      ? 'bg-secondary/15 text-secondary shadow-[0_0_12px_rgba(76,215,246,0.25)] border border-secondary/30'
                      : 'bg-surface-container/60 hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface border border-transparent'
                  }`}
                >
                  {g.label}
                </button>
              ))}
            </div>
          </section>

          {/* Filtered Search Results (if active) */}
          {filteredMovies && (
            <section className="w-full mb-12 animate-fade-in">
              <div className="flex items-center justify-between pb-4 border-b border-outline-variant/30 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-on-surface">
                    Filter Results ({filteredMovies.length} titles)
                  </h2>
                </div>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setSelectedGenre('all');
                  }}
                  className="text-xs text-secondary hover:underline"
                >
                  Reset Filters
                </button>
              </div>

              {filteredMovies.length === 0 ? (
                <div className="p-12 text-center bg-surface-container/40 rounded-xl border border-outline-variant/20">
                  <span className="material-symbols-outlined text-4xl text-outline mb-2">search_off</span>
                  <p className="text-on-surface-variant text-sm">No titles found matching your search.</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
                  {filteredMovies.map((movie) => (
                    <div
                      key={movie.id}
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
                        {movie.year && (
                          <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full bg-surface-container-lowest/80 backdrop-blur-md text-[11px] font-bold text-on-surface shadow">
                            {movie.year}
                          </span>
                        )}
                        <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1">
                          {movie.genres.slice(0, 2).map((genre) => (
                            <span
                              key={genre}
                              className="px-2 py-0.5 rounded-md bg-secondary/15 text-secondary text-[10px] font-bold uppercase"
                            >
                              {genre}
                            </span>
                          ))}
                        </div>

                        {/* Trailer Hover Button */}
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveTrailer({ id: movie.id, title: movie.title, trailer_key: movie.trailer_key });
                            }}
                            className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-xs font-bold shadow-[0_0_16px_rgba(128,131,255,0.6)] flex items-center gap-1.5 hover:scale-105 transition-all"
                          >
                            <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                              play_arrow
                            </span>
                            Watch Trailer
                          </button>
                        </div>
                      </div>

                      <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                        <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                          {movie.title}
                        </h3>
                        <div className="flex items-center justify-between text-xs text-tertiary">
                          <span className="text-[11px] text-on-surface-variant font-medium">★ {movie.vote_average.toFixed(1)}</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveTrailer({ id: movie.id, title: movie.title, trailer_key: movie.trailer_key });
                            }}
                            className="text-[11px] text-secondary hover:underline"
                          >
                            Trailer
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Section 1: Quick Roll (Random Recommendations) */}
          <section className="w-full flex flex-col gap-6 mb-12">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/30 pb-4">
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-secondary text-xl">shuffle</span>
                  <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                    Quick Roll: Random Recommendations
                  </h2>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => rollNewSelection()}
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-surface-container-high hover:bg-surface-bright text-secondary text-xs sm:text-sm font-semibold border border-outline-variant/30 shadow-sm transition-all hover:scale-105 active:scale-95"
                >
                  <span className="material-symbols-outlined text-base">casino</span>
                  <span>Roll New Selection</span>
                </button>
                <span className="text-xs text-outline hidden md:inline">5 Curated Surprises</span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {quickRoll.map((movie) => (
                <div
                  key={movie.id}
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
                    {movie.year && (
                      <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full bg-surface-container-lowest/80 backdrop-blur-md text-[11px] font-bold text-on-surface shadow">
                        {movie.year}
                      </span>
                    )}
                    <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1">
                      {movie.genres.slice(0, 2).map((genre) => (
                        <span
                          key={genre}
                          className="px-2 py-0.5 rounded-md bg-secondary/15 text-secondary text-[10px] font-bold uppercase"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>

                    {/* Hover Trailer Button */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movie.id, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-xs font-bold shadow-[0_0_16px_rgba(128,131,255,0.6)] flex items-center gap-1.5 hover:scale-105 transition-all"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          play_arrow
                        </span>
                        Trailer
                      </button>
                    </div>
                  </div>

                  <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                    <div>
                      <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                        {movie.title}
                      </h3>
                      <p className="text-xs text-outline">{movie.genres[0] || 'Feature Film'}</p>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <span className="px-2 py-0.5 rounded-full bg-secondary/15 text-secondary text-[11px] font-semibold">
                        95% Match
                      </span>
                      <div className="flex items-center gap-0.5 text-tertiary text-xs font-bold">
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span>{movie.vote_average.toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Unlock Your Personalized Recommendations Banner */}
          {!user && (
            <div className="my-6 rounded-2xl bg-gradient-to-r from-surface-container via-surface-container-high to-surface-container border border-outline-variant/30 p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xl shadow-surface-container-lowest/80">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary-container/20 border border-primary/30 flex items-center justify-center text-primary shrink-0 shadow-[0_0_16px_rgba(128,131,255,0.25)]">
                  <span className="material-symbols-outlined text-2xl">local_movies</span>
                </div>
                <div className="flex flex-col gap-1">
                  <h3 className="text-lg font-bold text-on-surface">Unlock Your Personalized Recommendations</h3>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <Link
                  to="/auth?mode=signup"
                  className="px-5 py-2.5 rounded-full bg-gradient-to-r from-secondary-container via-primary-container to-secondary text-on-secondary-container font-bold text-xs sm:text-sm shadow-[0_0_20px_rgba(76,215,246,0.4)] hover:scale-105 active:scale-95 transition-all"
                >
                  Sign Up Free
                </Link>
              </div>
            </div>
          )}

          {/* Section 2: Top Rated Movies of All Time */}
          <section className="w-full flex flex-col gap-6 mb-12">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-outline-variant/30 pb-4">
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tertiary text-xl">emoji_events</span>
                  <h2 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
                    Top Rated Movies of All Time
                  </h2>
                </div>
              </div>
              <span className="text-xs text-outline hidden md:inline">Consensus Score &gt; 96%</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {topRated.map((movie) => (
                <div
                  key={movie.id}
                  onClick={() => setActiveDetailMovie(movie)}
                  className="group flex flex-col rounded-xl bg-surface-container/60 backdrop-blur-md overflow-hidden transition-all duration-300 hover:scale-[1.02] hover:bg-surface-container-high/90 hover:shadow-[0_12px_30px_rgba(0,0,0,0.7)] border border-transparent hover:border-tertiary/30 cursor-pointer"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden bg-surface-container-lowest">
                    <img
                      src={getPosterUrl(movie)}
                      alt={movie.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      loading="lazy"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>
                    {movie.year && (
                      <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-full bg-surface-container-lowest/80 backdrop-blur-md text-[11px] font-bold text-on-surface shadow">
                        {movie.year}
                      </span>
                    )}
                    <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1">
                      {movie.genres.slice(0, 2).map((genre) => (
                        <span
                          key={genre}
                          className="px-2 py-0.5 rounded-md bg-secondary/15 text-secondary text-[10px] font-bold uppercase"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>

                    {/* Hover Trailer Button */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40 backdrop-blur-[2px]">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveTrailer({ id: movie.id, title: movie.title, trailer_key: movie.trailer_key });
                        }}
                        className="px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-xs font-bold shadow-[0_0_16px_rgba(128,131,255,0.6)] flex items-center gap-1.5 hover:scale-105 transition-all"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          play_arrow
                        </span>
                        Trailer
                      </button>
                    </div>
                  </div>

                  <div className="p-3 flex flex-col justify-between flex-1 gap-1">
                    <div>
                      <h3 className="font-bold text-sm text-on-surface truncate" title={movie.title}>
                        {movie.title}
                      </h3>
                      <p className="text-xs text-outline">{movie.genres[0] || 'Cinema Classic'}</p>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <span className="px-2 py-0.5 rounded-full bg-secondary/15 text-secondary text-[11px] font-semibold">
                        98% Match
                      </span>
                      <div className="flex items-center gap-0.5 text-tertiary text-xs font-bold">
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                          star
                        </span>
                        <span>{movie.vote_average.toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>

      {/* Global Movie Detail Modal */}
      <MovieDetailModal
        movie={activeDetailMovie}
        isOpen={Boolean(activeDetailMovie)}
        onClose={() => setActiveDetailMovie(null)}
        onPlayTrailer={(t) => setActiveTrailer(t)}
        isLoggedIn={Boolean(user)}
      />

      {/* Global Trailer Video Modal */}
      <TrailerModal movie={activeTrailer} onClose={() => setActiveTrailer(null)} />
    </div>
  );
};
