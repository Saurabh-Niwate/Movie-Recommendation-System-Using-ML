import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface StarterMovie {
  id: number;
  title: string;
  year?: number;
  genres: string[];
  vote_average: number;
  poster_path?: string | null;
  director?: string;
}

export const OnboardingPage: React.FC = () => {
  const { refreshUser } = useAuth();
  const navigate = useNavigate();

  const [movies, setMovies] = useState<StarterMovie[]>([]);
  const [ratedMovies, setRatedMovies] = useState<Map<number, number>>(new Map());
  const [activeTab, setActiveTab] = useState<'movies' | 'vibes'>('movies');
  const [searchFilter, setSearchFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const MIN_REQUIRED = 6;

  const getPosterUrl = (m: StarterMovie) => {
    if (m.poster_path && m.poster_path.startsWith('http')) return m.poster_path;
    if (m.poster_path && m.poster_path.startsWith('/')) {
      return `https://image.tmdb.org/t/p/w500${m.poster_path}`;
    }
    return `https://image.tmdb.org/t/p/w500/${m.id}.jpg`;
  };

  useEffect(() => {
    // Fetch starter movies
    apiFetch<StarterMovie[]>('/movies/starter?limit=24')
      .then((items) => {
        setMovies(items || []);
      })
      .catch((err) => {
        console.error('Failed to load starter grid, falling back to catalog:', err);
        return apiFetch<{ items: StarterMovie[] }>('/movies?limit=24&sort=popular').then((res) => {
          setMovies(res.items || []);
        });
      })
      .finally(() => {
        setLoading(false);
      });

    // Check if user already has existing ratings
    apiFetch<Array<{ movie_id: number; rating: number }>>('/ratings')
      .then((existingRatings) => {
        if (existingRatings && existingRatings.length > 0) {
          const mapped = new Map<number, number>();
          existingRatings.forEach((r) => mapped.set(r.movie_id, r.rating));
          setRatedMovies(mapped);
        }
      })
      .catch(() => {});
  }, []);

  const totalRated = ratedMovies.size;
  const progressPercent = Math.min(100, Math.round((totalRated / MIN_REQUIRED) * 100));

  const toggleRating = async (movieId: number, stars: number = 5) => {
    const nextMap = new Map(ratedMovies);

    if (nextMap.has(movieId)) {
      nextMap.delete(movieId);
      setRatedMovies(nextMap);
    } else {
      nextMap.set(movieId, stars);
      setRatedMovies(nextMap);

      // Submit rating to backend to trigger online fold-in and update taste vector
      try {
        await apiFetch('/ratings', {
          method: 'POST',
          body: JSON.stringify({
            movie_id: movieId,
            rating: stars,
          }),
        });
      } catch (err) {
        console.warn('Rating background submission warning:', err);
      }
    }
  };

  const handleSynthesizeTaste = async () => {
    if (totalRated < MIN_REQUIRED) return;
    setSubmitting(true);

    try {
      await refreshUser();
      navigate('/feed', { replace: true });
    } catch (err) {
      navigate('/feed', { replace: true });
    } finally {
      setSubmitting(false);
    }
  };

  const filteredMovies = movies.filter((m) => {
    if (!searchFilter.trim()) return true;
    const term = searchFilter.toLowerCase();
    return (
      m.title.toLowerCase().includes(term) ||
      m.genres.some((g) => g.toLowerCase().includes(term))
    );
  });

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative selection:bg-secondary/30 selection:text-secondary pb-32">
      {/* Background radial glow */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute -top-[20%] right-[-10%] w-[55vw] h-[55vw] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute -bottom-[20%] left-[-10%] w-[50vw] h-[50vw] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        {/* Header Telemetry Block */}
        <section className="w-full pt-6 pb-8">
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-secondary animate-pulse"></span>
                <span className="text-xs font-bold uppercase tracking-widest text-secondary">
                  Welcome to CineMatch
                </span>
                <span className="text-outline text-xs">•</span>
                <span className="text-xs uppercase tracking-wider text-outline font-semibold">
                  Taste Profile Setup
                </span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-on-surface tracking-tight">
                Personalize Your{' '}
                <span className="bg-gradient-to-r from-primary via-secondary to-primary bg-clip-text text-transparent">
                  Taste Profile
                </span>
              </h1>
              <p className="text-sm sm:text-base text-on-surface-variant mt-2 max-w-2xl leading-relaxed">
                Select and rate at least {MIN_REQUIRED} films across your favorite genres to unlock your custom recommendations.
              </p>
            </div>

            {/* Circular Meter Status Pill */}
            <div className="bg-surface-container-high/60 backdrop-blur-md rounded-2xl p-4 shadow-lg border border-outline-variant/30 flex items-center gap-4 lg:self-center">
              <div className="relative w-12 h-12 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 36 36">
                  <path
                    className="text-surface-variant"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3.5"
                  />
                  <path
                    className="text-secondary transition-all duration-500 ease-out"
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="currentColor"
                    strokeDasharray={`${progressPercent}, 100`}
                    strokeLinecap="round"
                    strokeWidth="3.5"
                  />
                </svg>
                <span className="absolute font-extrabold text-sm text-on-surface">
                  {totalRated}
                </span>
              </div>
              <div>
                <div className="flex items-center gap-1.5 font-bold text-sm text-on-surface">
                  <span>{totalRated >= MIN_REQUIRED ? 'Taste Profile Ready' : 'Setup Progress'}</span>
                  <span className="material-symbols-outlined text-secondary text-base">tune</span>
                </div>
                <span className="text-xs text-outline font-medium">
                  {totalRated >= MIN_REQUIRED
                    ? 'Ready to unlock curated feed'
                    : `Need ${MIN_REQUIRED - totalRated} more selection${MIN_REQUIRED - totalRated === 1 ? '' : 's'}`}
                </span>
              </div>
            </div>
          </div>

          {/* Telemetry Strip */}
          <div className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-3 flex items-center justify-between border border-outline-variant/20">
              <span className="text-xs text-outline uppercase font-semibold">Total Picks</span>
              <span className="text-sm font-bold text-primary">{totalRated} / {MIN_REQUIRED}</span>
            </div>
            <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-3 flex items-center justify-between border border-outline-variant/20">
              <span className="text-xs text-outline uppercase font-semibold">Requirement</span>
              <span className="text-sm font-bold text-secondary">{progressPercent}% Met</span>
            </div>
            <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-3 flex items-center justify-between border border-outline-variant/20">
              <span className="text-xs text-outline uppercase font-semibold">Status</span>
              <span className={`text-sm font-bold ${totalRated >= MIN_REQUIRED ? 'text-secondary' : 'text-outline'}`}>
                {totalRated >= MIN_REQUIRED ? 'Ready' : 'Incomplete'}
              </span>
            </div>
            <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-3 flex items-center justify-between border border-outline-variant/20">
              <span className="text-xs text-outline uppercase font-semibold">Engine Status</span>
              <span className="text-sm font-bold text-primary">Live &amp; Calibrated</span>
            </div>
          </div>
        </section>

        {/* Control Row: Search & Filters */}
        <section className="sticky top-20 z-30 w-full py-3 bg-surface-container-lowest/85 backdrop-blur-xl border-y border-outline-variant/20 mb-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('movies')}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
                  activeTab === 'movies'
                    ? 'bg-primary-container text-on-primary-container shadow-md'
                    : 'bg-surface-container/60 text-on-surface-variant hover:text-on-surface'
                }`}
              >
                <span className="material-symbols-outlined text-base">movie</span>
                <span>Iconic Movies ({movies.length})</span>
              </button>
            </div>

            <div className="relative w-full sm:w-80">
              <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-outline text-lg pointer-events-none">
                search
              </span>
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Filter titles or genres..."
                className="w-full h-10 pl-10 pr-4 bg-surface-container text-on-surface placeholder:text-outline text-xs sm:text-sm rounded-xl outline-none focus:bg-surface-container-high focus:shadow-[0_0_12px_rgba(76,215,246,0.25)] border border-outline-variant/20"
              />
            </div>
          </div>
        </section>

        {/* Movies Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {loading ? (
            <div className="col-span-full py-12 text-center text-on-surface-variant flex flex-col items-center gap-2">
              <span className="material-symbols-outlined text-secondary text-3xl animate-spin">progress_activity</span>
              <span className="text-sm font-semibold">Loading starter cinema catalog...</span>
            </div>
          ) : filteredMovies.map((movie) => {
            const isRated = ratedMovies.has(movie.id);

            return (
              <div
                key={movie.id}
                onClick={() => toggleRating(movie.id, 5)}
                className={`group cursor-pointer relative rounded-xl overflow-hidden transition-all duration-300 transform hover:-translate-y-1 hover:shadow-2xl border ${
                  isRated
                    ? 'ring-2 ring-secondary bg-surface-container-highest shadow-[0_0_20px_rgba(76,215,246,0.35)] border-secondary'
                    : 'bg-surface-container-high/60 border-outline-variant/30 hover:border-outline'
                }`}
              >
                <div className="aspect-[2/3] w-full relative overflow-hidden bg-surface-container">
                  <img
                    src={getPosterUrl(movie)}
                    alt={movie.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-surface-container-lowest via-surface-container-lowest/30 to-transparent"></div>

                  {/* Checkmark or Add Indicator */}
                  <div
                    className={`absolute top-2.5 right-2.5 w-7 h-7 rounded-full backdrop-blur-md flex items-center justify-center transition-all duration-300 ${
                      isRated ? 'bg-secondary text-on-secondary font-bold shadow-md' : 'bg-surface-container-lowest/70 text-outline'
                    }`}
                  >
                    <span className="material-symbols-outlined text-base">
                      {isRated ? 'check' : 'add'}
                    </span>
                  </div>

                  {/* Title & Metadata Overlay */}
                  <div className="absolute bottom-2.5 left-2.5 right-2.5 flex flex-col">
                    <span className="text-[10px] font-bold text-secondary uppercase tracking-widest truncate">
                      {movie.genres[0] || 'Feature Film'}
                    </span>
                    <h3 className="font-bold text-xs sm:text-sm text-on-surface line-clamp-1">
                      {movie.title}
                    </h3>
                    <p className="text-[11px] text-on-surface-variant font-medium">
                      {movie.year || 'Classic'} • ★ {movie.vote_average.toFixed(1)}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {/* Floating Bottom Sticky Action Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 bg-surface-container-lowest/90 backdrop-blur-2xl border-t border-outline-variant/30 py-4 px-6 md:px-12 shadow-[0_-8px_30px_rgba(0,0,0,0.8)]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${
                totalRated >= MIN_REQUIRED ? 'bg-secondary animate-pulse' : 'bg-outline'
              }`}
            ></div>
            <div className="flex flex-col">
              <span className="text-xs font-bold text-on-surface">
                {totalRated} of {MIN_REQUIRED} mandatory ratings selected
              </span>
              <span className="text-[11px] text-on-surface-variant">
                {totalRated >= MIN_REQUIRED
                  ? 'Criteria satisfied — click to explore your personalized feed'
                  : `Please rate ${MIN_REQUIRED - totalRated} more film${MIN_REQUIRED - totalRated === 1 ? '' : 's'} to unlock recommendations`}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-all"
            >
              Back
            </button>
            <button
              type="button"
              disabled={totalRated < MIN_REQUIRED || submitting}
              onClick={handleSynthesizeTaste}
              className={`w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-xs sm:text-sm transition-all duration-300 flex items-center justify-center gap-2 ${
                totalRated >= MIN_REQUIRED
                  ? 'bg-gradient-to-r from-primary-container via-secondary-container to-secondary text-on-primary-container shadow-[0_0_28px_rgba(76,215,246,0.4)] hover:scale-105 active:scale-95 cursor-pointer'
                  : 'bg-surface-container text-outline opacity-60 cursor-not-allowed'
              }`}
            >
              {submitting ? (
                <>
                  <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  <span>Personalizing Feed...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-base">auto_awesome</span>
                  <span>Finish Setup &amp; Enter Feed</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
