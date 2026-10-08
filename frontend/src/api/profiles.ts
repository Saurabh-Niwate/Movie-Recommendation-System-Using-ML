import { Profile } from '../types/profile';
import { apiFetch, ApiError } from './client';
import { INITIAL_PROFILES } from '../data/mockProfiles';

function normalizeProfile(p: Partial<Profile> & { id: string }): Profile {
  const fallback = INITIAL_PROFILES.find((ip) => ip.id === p.id);
  return {
    id: p.id,
    name: p.name || fallback?.name || p.id,
    avatar: p.avatar || fallback?.avatar || '',
    bio: p.bio || fallback?.bio || '',
    ratings_count: p.ratings_count ?? fallback?.ratings_count ?? 0,
    is_cold_start: p.is_cold_start ?? fallback?.is_cold_start ?? false,
    genres: Array.isArray(p.genres) ? p.genres : fallback?.genres || [],
    user_idx: p.user_idx !== undefined ? p.user_idx : fallback?.user_idx,
    color_accent: p.color_accent || fallback?.color_accent || 'from-zinc-700 to-zinc-900',
  };
}

export async function fetchProfiles(): Promise<Profile[]> {
  try {
    const data = await apiFetch<Profile[]>('/profiles');
    if (Array.isArray(data) && data.length > 0) {
      return data.map(normalizeProfile);
    }
    return INITIAL_PROFILES;
  } catch (err) {
    if (err instanceof ApiError && err.status === 503) {
      console.warn('Backend unavailable, using pre-seeded profiles.');
      return INITIAL_PROFILES;
    }
    // Return initial profiles on any fallback
    return INITIAL_PROFILES;
  }
}

export async function fetchProfileById(id: string): Promise<Profile> {
  try {
    const data = await apiFetch<Profile>(`/profiles/${id}`);
    return normalizeProfile(data);
  } catch (err) {
    const found = INITIAL_PROFILES.find((p) => p.id === id);
    if (found) return found;
    throw err;
  }
}

