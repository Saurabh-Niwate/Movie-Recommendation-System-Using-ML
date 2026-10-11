import React, { useState, useEffect, useCallback } from 'react';
import { useProfile } from '../context/ProfileContext';
import { useModel } from '../context/ModelContext';
import { Movie, RecommendationRow } from '../types/movie';
import { fetchBillboardMovie, fetchAllBrowseRows } from '../api/recommendations';
import { Navbar } from '../components/common/Navbar';
import { Billboard } from '../components/browse/Billboard';
import { MovieCarousel } from '../components/browse/MovieCarousel';
import { TitleDetailModal } from '../components/modal/TitleDetailModal';

export const BrowsePage: React.FC = () => {
  const { activeProfile, lastRatingTimestamp, userRatings } = useProfile();
  const { selectedModel } = useModel();

  const [billboardMovie, setBillboardMovie] = useState<Movie | null>(null);
  const [rows, setRows] = useState<RecommendationRow[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const profileId = activeProfile?.id || 'neel';

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [hero, browseRows] = await Promise.all([
        fetchBillboardMovie(profileId),
        fetchAllBrowseRows(profileId, selectedModel),
      ]);
      setBillboardMovie(hero);
      setRows(browseRows);
    } catch (err) {
      console.error('Failed to load browse data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [profileId, selectedModel]);

  // Refetch when profile, model, or rating timestamp changes!
  useEffect(() => {
    loadData();
  }, [loadData, lastRatingTimestamp]);

  return (
    <div className="min-h-screen bg-[#141414] text-white flex flex-col justify-between selection:bg-[#E50914] selection:text-white">
      {/* Top Sticky Navigation */}
      <Navbar />

      {/* Main Browse Experience */}
      <main className="flex-1 pb-20">
        {/* Billboard Hero Section */}
        <Billboard
          movie={billboardMovie}
          onOpenDetails={(movie) => setSelectedMovie(movie)}
          activeProfileName={activeProfile?.name || 'You'}
        />

        {/* Recommendation Rows */}
        <div className="relative -mt-16 md:-mt-24 z-20 space-y-6">
          {isLoading && rows.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3">
              <div className="w-10 h-10 border-4 border-[#E50914] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-zinc-400 font-medium">
                Generating your personalized recommendations...
              </span>
            </div>
          ) : (
            rows.map((row) => (
              <MovieCarousel
                key={`${row.id}-${selectedModel}`}
                row={row}
                onSelectMovie={(movie) => setSelectedMovie(movie)}
                userRatings={userRatings}
              />
            ))
          )}
        </div>
      </main>

      {/* Title Detail Modal */}
      {selectedMovie && (
        <TitleDetailModal
          movie={selectedMovie}
          onClose={() => setSelectedMovie(null)}
          onSelectMovie={(movie) => setSelectedMovie(movie)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 py-10 px-4 sm:px-8 text-center text-xs text-zinc-500 space-y-2">
        <p>CineMatch • Personalized Film Discovery &amp; Recommendations</p>
        <p className="text-[11px] text-zinc-600">
          Powered by real-time viewer preferences &amp; authentic media
        </p>
      </footer>
    </div>
  );
};
