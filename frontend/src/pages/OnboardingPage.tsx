import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProfile } from '../context/ProfileContext';
import { Movie } from '../types/movie';
import { fetchStarterMovies, searchMovies } from '../api/movies';
import { RatingCounter } from '../components/onboarding/RatingCounter';
import { StarterMovieCard } from '../components/onboarding/StarterMovieCard';
import { UnlockButton } from '../components/onboarding/UnlockButton';
import { Search, ArrowLeft, BookOpen, AlertCircle } from 'lucide-react';

export const OnboardingPage: React.FC = () => {
  const { activeProfile, userRatings, rateMovie, unlockMukesh } = useProfile();
  const [movies, setMovies] = useState<Movie[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const navigate = useNavigate();

  // Load starter movies
  useEffect(() => {
    let mounted = true;
    fetchStarterMovies().then((data) => {
      if (mounted) setMovies(data);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Search handler
  useEffect(() => {
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await searchMovies(searchQuery);
        setMovies(results);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const ratedCount = Object.keys(userRatings).length;

  const handleRate = async (movieId: number, stars: number) => {
    await rateMovie(movieId, stars);
  };

  const handleUnlock = async () => {
    if (ratedCount < 6) return;
    setIsUnlocking(true);
    // Simulate minor delay for dramatic fold-in effect
    setTimeout(() => {
      unlockMukesh();
      setIsUnlocking(false);
      navigate('/browse');
    }, 600);
  };

  return (
    <div className="min-h-screen w-full bg-[#141414] text-white flex flex-col justify-between">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-[#141414]/95 backdrop-blur-md border-b border-zinc-800/80 px-4 sm:px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/profiles')}
              className="p-2 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white transition-colors border border-zinc-800"
              title="Return to Profile Picker"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[#E50914] font-black text-2xl tracking-tighter uppercase">
                  CineMatch
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">
                  Mukesh Cold-Start
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-zinc-400 font-mono hidden sm:inline">
              Furtado & Singh Rule: ≥ 6 ratings
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-8 flex-1 w-full space-y-8">
        {/* Banner with research citation */}
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <BookOpen className="w-6 h-6 text-[#E50914] flex-none mt-1" />
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white">
                Furtado & Singh (2020) Cold-Start Onboarding
              </h2>
              <p className="text-xs sm:text-sm text-zinc-300 mt-1 max-w-2xl leading-relaxed">
                <em>
                  &quot;For the user to get the recommendation he has to rate at least 6 movies. If he is a new user and has not rated any movies then he is expected to search for a random movie or any movie of his interest in the search box and rate at least 6 movies. Only then the &apos;Generate Recommendation&apos; button will be enabled.&quot;
                </em>
              </p>
            </div>
          </div>
        </div>

        {/* Visual Progress Counter & Unlock Button */}
        <div className="space-y-6">
          <RatingCounter count={ratedCount} target={6} />
          <UnlockButton
            ratingsCount={ratedCount}
            requiredCount={6}
            onUnlock={handleUnlock}
            isLoading={isUnlocking}
          />
        </div>

        {/* Search Bar */}
        <div className="max-w-xl mx-auto">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <input
              type="text"
              placeholder="Search MovieLens catalog by title or genre (e.g. Matrix, Terminator, Drama)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-700/80 rounded-xl pl-12 pr-4 py-3.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-[#E50914] focus:ring-1 focus:ring-[#E50914] transition-all shadow-inner"
            />
            {isSearching && (
              <div className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-[#E50914] border-t-transparent rounded-full animate-spin" />
            )}
          </div>
        </div>

        {/* Curated 24 Starter Movies Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-lg text-white">
              {searchQuery ? `Search Results for "${searchQuery}"` : '24 Curated Starter Movies Across Diverse Genres'}
            </h3>
            <span className="text-xs text-zinc-500 font-mono">
              {movies.length} titles available
            </span>
          </div>

          {movies.length === 0 ? (
            <div className="py-16 text-center text-zinc-500 bg-zinc-900/40 rounded-xl border border-zinc-800">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-zinc-600" />
              <p>No movies found matching &quot;{searchQuery}&quot;.</p>
              <button
                onClick={() => setSearchQuery('')}
                className="mt-3 text-xs text-[#E50914] hover:underline"
              >
                Reset search to curated starter movies
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {movies.map((movie) => (
                <StarterMovieCard
                  key={movie.id || movie.movie_id}
                  movie={movie}
                  userRating={userRatings[movie.id || movie.movie_id]}
                  onRate={handleRate}
                />
              ))}
            </div>
          )}
        </div>

        {/* Bottom Unlock Button for convenience */}
        <div className="py-8">
          <UnlockButton
            ratingsCount={ratedCount}
            requiredCount={6}
            onUnlock={handleUnlock}
            isLoading={isUnlocking}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 py-6 text-center text-xs text-zinc-500">
        Active Profile: {activeProfile?.name || 'Mukesh'} • CineMatch Recommender System
      </footer>
    </div>
  );
};
