import { apiFetch } from './client';

export interface WatchlistItem {
  id: number;
  movie_id: number;
  title: string;
  genres: string[];
  year?: number | null;
  poster_path?: string | null;
  backdrop_path?: string | null;
  avg_rating?: number | null;
  vote_count?: number | null;
  added_at?: string;
}

export async function fetchWatchlist(profileId: string): Promise<WatchlistItem[]> {
  try {
    return await apiFetch<WatchlistItem[]>(`/profiles/${profileId}/watchlist`);
  } catch {
    return [];
  }
}

export async function addToWatchlist(profileId: string, movieId: number): Promise<{ status: string }> {
  return await apiFetch<{ status: string }>(`/profiles/${profileId}/watchlist`, {
    method: 'POST',
    body: JSON.stringify({ movie_id: movieId }),
  });
}

export async function removeFromWatchlist(profileId: string, movieId: number): Promise<{ status: string }> {
  return await apiFetch<{ status: string }>(`/profiles/${profileId}/watchlist/${movieId}`, {
    method: 'DELETE',
  });
}
