import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useProfile } from '../context/ProfileContext';
import { Profile } from '../types/profile';
import { Sparkles, ShieldAlert, Film } from 'lucide-react';

export const ProfilePickerPage: React.FC = () => {
  const { profiles, selectProfile, isMukeshUnlocked, userRatings } = useProfile();
  const navigate = useNavigate();

  const handleSelect = (profile: Profile) => {
    selectProfile(profile);

    if (profile.id === 'mukesh') {
      const currentCount = Object.keys(userRatings).length;
      if (!isMukeshUnlocked && currentCount < 6) {
        navigate('/onboarding');
        return;
      }
    }
    navigate('/browse');
  };

  return (
    <div className="min-h-screen w-full bg-[#141414] text-white flex flex-col justify-between p-6 sm:p-10 select-none">
      {/* Top Brand */}
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[#E50914] font-black text-3xl tracking-tighter uppercase drop-shadow">
            CineMatch
          </span>
          <span className="text-[11px] uppercase font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
            Furtado & Singh (2020)
          </span>
        </div>
      </header>

      {/* Main Profile Selection */}
      <main className="max-w-4xl mx-auto w-full text-center my-auto py-12">
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight mb-3">
          Who&apos;s watching?
        </h1>
        <p className="text-zinc-400 text-sm sm:text-base max-w-lg mx-auto mb-12">
          Choose a persona to explore personalized collaborative filtering models or test cold-start onboarding.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 sm:gap-6 md:gap-10">
          {profiles.map((profile) => {
            const isMukesh = profile.id === 'mukesh';
            const mukeshRatingsCount = Object.keys(userRatings).length;

            return (
              <div
                key={profile.id}
                onClick={() => handleSelect(profile)}
                data-testid={`profile-card-${profile.id}`}
                className="group flex flex-col items-center cursor-pointer transform transition-all duration-300 hover:scale-105"
              >
                {/* Avatar Box */}
                <div className="relative w-32 h-32 sm:w-36 sm:h-36 md:w-44 md:h-44 rounded-xl overflow-hidden border-2 border-transparent group-hover:border-white shadow-2xl transition-all">
                  <img
                    src={profile.avatar}
                    alt={profile.name}
                    className="w-full h-full object-cover group-hover:brightness-110 transition-all"
                  />

                  {/* Gradient Overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-30 transition-opacity" />

                  {/* Cold start / Persona Tag */}
                  {isMukesh ? (
                    <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500 text-black flex items-center gap-1 shadow">
                      <ShieldAlert className="w-3 h-3" />
                      <span>Cold Start</span>
                    </div>
                  ) : (
                    <div className="absolute top-2 right-2 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-zinc-900/90 text-zinc-300 border border-zinc-700">
                      Cluster {profile.id === 'neel' ? '1' : '2'}
                    </div>
                  )}

                  {/* Live ratings badge for Mukesh */}
                  {isMukesh && mukeshRatingsCount > 0 && (
                    <div className="absolute bottom-2 left-2 right-2 text-center text-[10px] font-mono bg-black/80 text-amber-300 py-0.5 rounded border border-amber-500/40">
                      {mukeshRatingsCount}/6 Rated
                    </div>
                  )}
                </div>

                {/* Profile Name & Details */}
                <h3 className="mt-4 text-lg md:text-xl font-bold text-zinc-300 group-hover:text-white transition-colors">
                  {profile.name}
                </h3>

                <p className="text-xs text-zinc-400 mt-1 max-w-[200px] leading-relaxed">
                  {profile.bio}
                </p>

                {/* Genre badges */}
                <div className="flex items-center gap-1.5 mt-2 flex-wrap justify-center">
                  {(profile.genres || []).map((g) => (
                    <span
                      key={g}
                      className="text-[10px] px-2 py-0.5 rounded bg-zinc-900 text-zinc-300 border border-zinc-800"
                    >
                      {g}
                    </span>
                  ))}
                  {isMukesh && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-amber-950/60 text-amber-400 border border-amber-800/60 flex items-center gap-1">
                      <Sparkles className="w-2.5 h-2.5" />
                      Rate 6 to Unlock
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {/* Footer Info */}
      <footer className="text-center text-xs text-zinc-600 pb-4 flex items-center justify-center gap-2">
        <Film className="w-4 h-4 text-zinc-500" />
        <span>MovieLens 1M Recommender System • Fast SGD Funk-SVD & Item-KNN Adjusted Cosine</span>
      </footer>
    </div>
  );
};
