import { Movie } from '../types/movie';
import { apiFetch } from './client';
import { STARTER_MOVIES } from '../data/starterMovies';

export async function fetchStarterMovies(): Promise<Movie[]> {
  try {
    const res = await apiFetch<Movie[] | { items: Movie[] }>('/movies/starter');
    if (Array.isArray(res)) return res;
    if (res && Array.isArray((res as { items: Movie[] }).items)) return (res as { items: Movie[] }).items;
    return STARTER_MOVIES;
  } catch {
    return STARTER_MOVIES;
  }
}

export async function searchMovies(query: string): Promise<Movie[]> {
  if (!query.trim()) {
    return STARTER_MOVIES;
  }
  try {
    const res = await apiFetch<Movie[] | { items: Movie[] }>(`/movies/search?q=${encodeURIComponent(query)}`);
    if (Array.isArray(res)) return res;
    if (res && Array.isArray((res as { items: Movie[] }).items)) return (res as { items: Movie[] }).items;
    return [];
  } catch {
    const q = query.toLowerCase();
    return STARTER_MOVIES.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.genres.some((g) => g.toLowerCase().includes(q))
    );
  }
}

export async function fetchMovieDetails(movieId: number): Promise<Movie> {
  try {
    return await apiFetch<Movie>(`/movies/${movieId}`);
  } catch {
    const found = STARTER_MOVIES.find((m) => m.id === movieId || m.movie_id === movieId);
    if (found) return found;
    return {
      id: movieId,
      movie_id: movieId,
      title: `Movie #${movieId}`,
      genres: ['Drama'],
      synopsis: 'A captivating cinematic experience from the MovieLens catalog.',
      avg_rating: 4.0,
      predicted_rating: 4.2,
      match_score: 84,
    };
  }
}
