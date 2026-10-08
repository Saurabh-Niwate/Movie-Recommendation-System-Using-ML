import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { Profile } from '../types/profile';
import { INITIAL_PROFILES } from '../data/mockProfiles';
import { fetchProfiles } from '../api/profiles';
import { submitUserRating } from '../api/ratings';
import { useToast } from './ToastContext';

interface ProfileContextValue {
  profiles: Profile[];
  activeProfile: Profile | null;
  selectProfile: (profile: Profile) => void;
  ratingsCount: number;
  userRatings: Record<number, number>;
  rateMovie: (movieId: number, rating: number) => Promise<boolean>;
  isMukeshUnlocked: boolean;
  unlockMukesh: () => void;
  lastRatingTimestamp: number;
  isLoadingProfiles: boolean;
}

const ProfileContext = createContext<ProfileContextValue | undefined>(undefined);

export const ProfileProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { showToast } = useToast();
  const [profiles, setProfiles] = useState<Profile[]>(INITIAL_PROFILES);
  const [activeProfile, setActiveProfile] = useState<Profile | null>(() => {
    const saved = localStorage.getItem('cinematch_active_profile');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [userRatings, setUserRatings] = useState<Record<number, number>>(() => {
    const saved = localStorage.getItem('cinematch_user_ratings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return {};
      }
    }
    return {};
  });
  const [isMukeshUnlocked, setIsMukeshUnlocked] = useState<boolean>(() => {
    return localStorage.getItem('cinematch_mukesh_unlocked') === 'true';
  });
  const [lastRatingTimestamp, setLastRatingTimestamp] = useState<number>(Date.now());
  const [isLoadingProfiles, setIsLoadingProfiles] = useState<boolean>(false);

  // Load profiles from backend or fallback
  useEffect(() => {
    let mounted = true;
    async function load() {
      setIsLoadingProfiles(true);
      try {
        const fetched = await fetchProfiles();
        if (mounted && fetched.length > 0) {
          setProfiles(fetched);
          if (activeProfile) {
            const updated = fetched.find((p) => p.id === activeProfile.id);
            if (updated) {
              setActiveProfile((prev) => (prev ? { ...prev, ...updated } : updated));
            }
          }
        }
      } catch (err) {
        console.error('Failed to load profiles:', err);
      } finally {
        if (mounted) setIsLoadingProfiles(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  // Save active profile to localStorage
  useEffect(() => {
    if (activeProfile) {
      localStorage.setItem('cinematch_active_profile', JSON.stringify(activeProfile));
    } else {
      localStorage.removeItem('cinematch_active_profile');
    }
  }, [activeProfile]);

  // Save ratings to localStorage
  useEffect(() => {
    localStorage.setItem('cinematch_user_ratings', JSON.stringify(userRatings));
  }, [userRatings]);

  const selectProfile = useCallback((profile: Profile) => {
    setActiveProfile(profile);
  }, []);

  const unlockMukesh = useCallback(() => {
    setIsMukeshUnlocked(true);
    localStorage.setItem('cinematch_mukesh_unlocked', 'true');
    if (activeProfile && activeProfile.id === 'mukesh') {
      setActiveProfile((prev) => (prev ? { ...prev, is_cold_start: false } : null));
    }
    showToast('🎉 Recommendations unlocked for Mukesh! Browse now personalized.', 'success');
  }, [activeProfile, showToast]);

  const ratingsCount = activeProfile
    ? activeProfile.id === 'mukesh'
      ? Object.keys(userRatings).length
      : activeProfile.ratings_count + Object.keys(userRatings).length
    : 0;

  const rateMovie = useCallback(
    async (movieId: number, rating: number): Promise<boolean> => {
      if (!activeProfile) {
        showToast('Please select a profile first', 'error');
        return false;
      }

      try {
        setUserRatings((prev) => ({ ...prev, [movieId]: rating }));
        const res = await submitUserRating(activeProfile.id, movieId, rating);

        setLastRatingTimestamp(Date.now());

        const newRatingsCount =
          activeProfile.id === 'mukesh'
            ? Object.keys(userRatings).length + (userRatings[movieId] ? 0 : 1)
            : activeProfile.ratings_count + 1;

        if (activeProfile.id === 'mukesh' && (newRatingsCount >= 6 || res.unlocked)) {
          setIsMukeshUnlocked(true);
          localStorage.setItem('cinematch_mukesh_unlocked', 'true');
        }

        const foldInMs = res.fold_in_time_ms ? ` (${res.fold_in_time_ms}ms fold-in)` : '';
        showToast(`Rating of ${rating}★ recorded! Recommendations updated${foldInMs}`, 'success');
        return true;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to submit rating';
        showToast(`Rating failed: ${message}`, 'error');
        return false;
      }
    },
    [activeProfile, userRatings, showToast]
  );

  return (
    <ProfileContext.Provider
      value={{
        profiles,
        activeProfile,
        selectProfile,
        ratingsCount,
        userRatings,
        rateMovie,
        isMukeshUnlocked,
        unlockMukesh,
        lastRatingTimestamp,
        isLoadingProfiles,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
};

export function useProfile(): ProfileContextValue {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
}
