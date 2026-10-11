import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/common/Navbar';
import { apiFetch } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const ProfilePage: React.FC = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const [ratingsCount, setRatingsCount] = useState<number>(user?.ratings_count || 0);
  const [watchlistCount, setWatchlistCount] = useState<number>(0);
  const [avgRating, setAvgRating] = useState<number>(4.6);
  const [activeAlgorithm, setActiveAlgorithm] = useState<string>('funk_svd');
  const [autoLearn, setAutoLearn] = useState<boolean>(true);
  const [indieDiscovery, setIndieDiscovery] = useState<boolean>(true);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    // Fetch ratings count & average
    apiFetch<Array<{ movie_id: number; rating: number }>>('/ratings')
      .then((ratings) => {
        if (ratings && ratings.length > 0) {
          setRatingsCount(ratings.length);
          const sum = ratings.reduce((acc, r) => acc + r.rating, 0);
          setAvgRating(Number((sum / ratings.length).toFixed(1)));
        }
      })
      .catch(() => {});

    // Fetch watchlist count
    apiFetch<any[]>('/watchlist')
      .then((list) => {
        setWatchlistCount(list?.length || 0);
      })
      .catch(() => {});
  }, []);

  const handleSignOut = () => {
    signOut();
    navigate('/');
  };

  const handleSaveSettings = () => {
    setToast('Recommendation preferences updated!');
    setTimeout(() => setToast(null), 3000);
  };

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative selection:bg-secondary/30 selection:text-secondary pb-24">
      {/* Background Glows */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      <Navbar />

      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-24 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-surface-container-high/90 backdrop-blur-xl border border-secondary/30 text-on-surface text-sm font-semibold shadow-xl animate-fade-in">
          <span className="material-symbols-outlined text-secondary text-base">check_circle</span>
          <span>{toast}</span>
        </div>
      )}

      <main className="relative z-10 w-full pt-20 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
        <div className="flex flex-col w-full gap-8">
          {/* Top Profile Hero & Vector Telemetry Banner */}
          <section className="relative w-full rounded-2xl overflow-hidden bg-surface-container-low shadow-xl p-6 sm:p-8 border border-outline-variant/30">
            <div className="pointer-events-none absolute -top-24 -right-16 w-96 h-96 rounded-full bg-primary-container/15 blur-3xl"></div>
            <div className="pointer-events-none absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-secondary/10 blur-3xl"></div>

            <div className="relative z-10 flex flex-col xl:flex-row xl:items-center justify-between gap-6">
              {/* User Block */}
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6 min-w-0">
                <div className="relative shrink-0">
                  <div className="absolute -inset-1 rounded-full bg-gradient-to-tr from-primary-container via-secondary to-primary opacity-75 blur-sm"></div>
                  <div className="relative w-20 h-20 md:w-24 md:h-24 rounded-full bg-surface-container-high border-2 border-secondary/50 flex items-center justify-center font-extrabold text-3xl text-secondary uppercase shadow-md">
                    {(user?.full_name || user?.name || user?.email || 'U').charAt(0)}
                  </div>
                  <span className="absolute bottom-1 right-1 w-5 h-5 rounded-full bg-surface-container-lowest flex items-center justify-center shadow-sm">
                    <span className="w-3 h-3 rounded-full bg-secondary animate-pulse"></span>
                  </span>
                </div>

                <div className="flex flex-col min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="px-2.5 py-0.5 rounded-full bg-primary-container/20 text-primary text-xs uppercase tracking-wider font-bold">
                      Film Curator
                    </span>
                    <span className="text-outline text-xs">• 1 User Account</span>
                  </div>

                  <h1 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight truncate flex items-center gap-2">
                    {user?.full_name || 'Cinematch User'}
                    <span className="text-xs sm:text-sm text-on-surface-variant font-normal">
                      ({user?.email})
                    </span>
                  </h1>

                  <p className="text-xs sm:text-sm text-outline flex items-center gap-1.5 mt-1">
                    <span className="material-symbols-outlined text-secondary text-base">movie_filter</span>
                    <span>Favorite Genres:</span>
                    <span className="text-secondary font-semibold">Sci-Fi, Psychological Thriller &amp; Neo-Noir</span>
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={() => navigate(-1)}
                  className="px-4 py-2 rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface text-xs sm:text-sm font-semibold transition-all border border-outline-variant/30 flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-base">arrow_back</span>
                  <span>Back</span>
                </button>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="px-4 py-2 rounded-full bg-error-container/30 hover:bg-error-container/60 text-error text-xs sm:text-sm font-semibold transition-all border border-error/30 flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-base">logout</span>
                  <span>Sign Out</span>
                </button>
              </div>
            </div>

            {/* Telemetry Cards Grid */}
            <div className="relative z-10 grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-4 border border-outline-variant/20 flex flex-col justify-between">
                <div className="flex items-center justify-between text-outline mb-1">
                  <span className="text-xs uppercase font-semibold">Films Rated</span>
                  <span className="material-symbols-outlined text-base">movie</span>
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-on-surface tracking-tight">
                    {ratingsCount}
                  </span>
                  <p className="text-xs text-on-surface-variant mt-0.5">Rated by You</p>
                </div>
              </div>

              <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-4 border border-outline-variant/20 flex flex-col justify-between">
                <div className="flex items-center justify-between text-secondary mb-1">
                  <span className="text-xs uppercase font-semibold">Average Rating</span>
                  <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
                    star
                  </span>
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-secondary tracking-tight">
                    {avgRating} ★
                  </span>
                  <p className="text-xs text-on-surface-variant mt-0.5">Personal Scoring Avg</p>
                </div>
              </div>

              <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-4 border border-outline-variant/20 flex flex-col justify-between">
                <div className="flex items-center justify-between text-primary mb-1">
                  <span className="text-xs uppercase font-semibold">Top Genre</span>
                  <span className="material-symbols-outlined text-base">local_movies</span>
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-primary tracking-tight">
                    Sci-Fi
                  </span>
                  <p className="text-xs text-on-surface-variant mt-0.5">Followed by Drama</p>
                </div>
              </div>

              <div className="bg-surface-container/70 backdrop-blur-md rounded-xl p-4 border border-outline-variant/20 flex flex-col justify-between">
                <div className="flex items-center justify-between text-tertiary mb-1">
                  <span className="text-xs uppercase font-semibold">In Watchlist</span>
                  <span className="material-symbols-outlined text-base">bookmark</span>
                </div>
                <div>
                  <span className="text-2xl font-extrabold text-tertiary tracking-tight">
                    {watchlistCount}
                  </span>
                  <p className="text-xs text-on-surface-variant mt-0.5">Saved Titles</p>
                </div>
              </div>
            </div>
          </section>

          {/* Primary 2-Column Responsive Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 7 Columns: Preferences & Algorithm Selector */}
            <div className="lg:col-span-7 flex flex-col gap-6">
              {/* Sliders Card */}
              <div className="bg-surface-container-low rounded-2xl p-6 sm:p-8 border border-outline-variant/30 shadow-md">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-secondary text-lg">tune</span>
                      <h2 className="text-xl font-bold text-on-surface">Genre Preferences</h2>
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded-full bg-secondary-container/20 text-secondary text-xs uppercase font-bold tracking-wider self-start sm:self-auto">
                    Top Preferences
                  </span>
                </div>

                <div className="space-y-4">
                  {[
                    { label: 'Sci-Fi & Cyberpunk', weight: 94, status: 'Loved', color: 'from-primary to-secondary' },
                    { label: 'Psychological Thriller & Mystery', weight: 88, status: 'Loved', color: 'from-primary-container to-primary' },
                    { label: 'Neo-Noir & Crime Drama', weight: 82, status: 'Often', color: 'from-secondary to-primary' },
                    { label: 'Drama & Philosophical', weight: 65, status: 'Moderate', color: 'from-outline to-secondary' },
                    { label: 'Action & Adventure', weight: 54, status: 'Moderate', color: 'from-outline-variant to-primary-container' },
                  ].map((genre) => (
                    <div key={genre.label} className="p-3 rounded-xl bg-surface-container/60 border border-outline-variant/20">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs sm:text-sm font-semibold text-on-surface">{genre.label}</span>
                          <span className="px-1.5 py-0.5 rounded bg-secondary/15 text-secondary text-[10px] uppercase font-bold">
                            {genre.status}
                          </span>
                        </div>
                        <span className="text-xs font-bold text-secondary bg-surface-container-highest px-2 py-0.5 rounded">
                          {genre.weight}%
                        </span>
                      </div>
                      <div className="relative w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                        <div className={`h-full bg-gradient-to-r ${genre.color} rounded-full`} style={{ width: `${genre.weight}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Recommendation Engine Algorithm Toggle */}
                <div className="mt-8 pt-6 border-t border-outline-variant/20">
                  <h3 className="text-sm font-bold text-on-surface mb-3 flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-secondary text-base">memory</span>
                    <span>Recommendation Mode</span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[
                      { id: 'funk_svd', name: 'Personalized Match', desc: 'Custom tailored to your rating history' },
                      { id: 'item_knn', name: 'Similar Titles', desc: 'Titles matching the style of films you liked' },
                      { id: 'association', name: 'Viewer Favorites', desc: 'Popular among members with similar tastes' },
                    ].map((algo) => (
                      <button
                        key={algo.id}
                        type="button"
                        onClick={() => {
                          setActiveAlgorithm(algo.id);
                          handleSaveSettings();
                        }}
                        className={`p-3 rounded-xl border text-left transition-all ${
                          activeAlgorithm === algo.id
                            ? 'bg-primary-container/20 border-primary shadow-[0_0_12px_rgba(128,131,255,0.25)]'
                            : 'bg-surface-container-high/40 border-outline-variant/20 hover:border-outline'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-bold text-xs sm:text-sm text-on-surface">{algo.name}</span>
                          {activeAlgorithm === algo.id && (
                            <span className="material-symbols-outlined text-secondary text-sm">check_circle</span>
                          )}
                        </div>
                        <p className="text-[11px] text-on-surface-variant leading-tight">{algo.desc}</p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Sub-controls toggles */}
                <div className="mt-6 space-y-4 pt-4 border-t border-outline-variant/20">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <span className="text-xs sm:text-sm font-semibold text-on-surface block">
                        Auto-adjust recommendations based on new ratings
                      </span>
                      <p className="text-xs text-outline">Instantly updates recommendations when you rate films</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setAutoLearn(!autoLearn)}
                      className={`w-11 h-6 rounded-full p-0.5 transition-colors relative flex items-center shrink-0 ${
                        autoLearn ? 'bg-primary-container' : 'bg-surface-container-highest'
                      }`}
                    >
                      <span
                        className={`w-5 h-5 rounded-full bg-on-primary-container transition-transform transform ${
                          autoLearn ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      ></span>
                    </button>
                  </div>

                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <span className="text-xs sm:text-sm font-semibold text-on-surface block">
                        Include indie &amp; festival discoveries
                      </span>
                      <p className="text-xs text-outline">Include acclaimed hidden gems and festival selections</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIndieDiscovery(!indieDiscovery)}
                      className={`w-11 h-6 rounded-full p-0.5 transition-colors relative flex items-center shrink-0 ${
                        indieDiscovery ? 'bg-primary-container' : 'bg-surface-container-highest'
                      }`}
                    >
                      <span
                        className={`w-5 h-5 rounded-full bg-on-primary-container transition-transform transform ${
                          indieDiscovery ? 'translate-x-5' : 'translate-x-0'
                        }`}
                      ></span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right 5 Columns: 6-Axis Dimensional Taste Radar Visualization */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              <div className="bg-surface-container-low rounded-2xl p-6 sm:p-8 border border-outline-variant/30 shadow-md">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-xs text-secondary uppercase tracking-widest font-bold block">
                      Taste Radar
                    </span>
                    <h3 className="text-lg font-bold text-on-surface">Viewing Taste Profile</h3>
                  </div>
                  <span className="material-symbols-outlined text-secondary text-2xl">polyline</span>
                </div>

                {/* SVG Taste Radar Hexagon */}
                <div className="w-full flex items-center justify-center py-4">
                  <svg className="w-full max-w-[280px] aspect-square overflow-visible" viewBox="0 0 240 240">
                    {/* Concentric Hexagons */}
                    <polygon
                      points="120,30 198,75 198,165 120,210 42,165 42,75"
                      fill="none"
                      stroke="#272a31"
                      strokeWidth="1"
                    />
                    <polygon
                      points="120,60 172,90 172,150 120,180 68,150 68,90"
                      fill="none"
                      stroke="#272a31"
                      strokeWidth="1"
                    />
                    <polygon
                      points="120,90 146,105 146,135 120,150 94,135 94,105"
                      fill="none"
                      stroke="#272a31"
                      strokeWidth="1"
                    />

                    {/* Axis lines */}
                    <line x1="120" y1="120" x2="120" y2="30" stroke="#32353c" strokeWidth="1" />
                    <line x1="120" y1="120" x2="198" y2="75" stroke="#32353c" strokeWidth="1" />
                    <line x1="120" y1="120" x2="198" y2="165" stroke="#32353c" strokeWidth="1" />
                    <line x1="120" y1="120" x2="120" y2="210" stroke="#32353c" strokeWidth="1" />
                    <line x1="120" y1="120" x2="42" y2="165" stroke="#32353c" strokeWidth="1" />
                    <line x1="120" y1="120" x2="42" y2="75" stroke="#32353c" strokeWidth="1" />

                    {/* Data Polygon Fill */}
                    <polygon
                      points="120,40 188,85 175,155 120,195 55,150 50,85"
                      fill="rgba(76, 215, 246, 0.25)"
                      stroke="#4cd7f6"
                      strokeWidth="2"
                    />

                    {/* Axis Labels */}
                    <text x="120" y="20" textAnchor="middle" fill="#c0c1ff" fontSize="10" fontWeight="bold">Complexity</text>
                    <text x="210" y="75" textAnchor="start" fill="#c0c1ff" fontSize="10" fontWeight="bold">Atmosphere</text>
                    <text x="210" y="170" textAnchor="start" fill="#c0c1ff" fontSize="10" fontWeight="bold">Tension</text>
                    <text x="120" y="225" textAnchor="middle" fill="#c0c1ff" fontSize="10" fontWeight="bold">Originality</text>
                    <text x="30" y="170" textAnchor="end" fill="#c0c1ff" fontSize="10" fontWeight="bold">Pacing</text>
                    <text x="30" y="75" textAnchor="end" fill="#c0c1ff" fontSize="10" fontWeight="bold">Tone</text>
                  </svg>
                </div>

                <div className="mt-4 p-4 rounded-xl bg-surface-container/60 border border-outline-variant/20 flex flex-col gap-2 text-xs">
                  <div className="flex items-center justify-between text-on-surface">
                    <span className="font-semibold">Taste Match</span>
                    <span className="text-secondary font-bold">98% High Alignment</span>
                  </div>
                  <p className="text-outline text-[11px]">
                    Your preferences align strongly with thought-provoking Sci-Fi and gripping thrillers.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
