import { Movie, RecommendationRow } from '../types/movie';
import { apiFetch, ApiError } from './client';
import { getMockRowsForProfile, NEEL_RECOMMENDATIONS, NITIN_RECOMMENDATIONS } from '../data/mockRecommendations';
import { STARTER_MOVIES } from '../data/starterMovies';

export async function fetchPersonalizedRecommendations(
  profileId: string,
  model: 'funk_svd' | 'item_knn' = 'funk_svd',
  limit = 20
): Promise<Movie[]> {
  try {
    return await apiFetch<Movie[]>(
      `/profiles/${profileId}/recommendations?model=${model}&limit=${limit}`
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 403) {
      // Mukesh cold start restriction
      throw err;
    }
    return profileId === 'neel'
      ? NEEL_RECOMMENDATIONS
      : profileId === 'nitin'
      ? NITIN_RECOMMENDATIONS
      : STARTER_MOVIES.slice(0, 10);
  }
}

export async function fetchBillboardMovie(profileId: string): Promise<Movie> {
  try {
    return await apiFetch<Movie>(`/recommendations/billboard?profile_id=${profileId}`);
  } catch {
    if (profileId === 'neel') {
      return NEEL_RECOMMENDATIONS[0];
    } else if (profileId === 'nitin') {
      return NITIN_RECOMMENDATIONS[0];
    }
    return STARTER_MOVIES[0];
  }
}

export async function fetchBecauseYouLiked(profileId: string): Promise<{ base_movie: Movie; recommendations: Movie[] }> {
  try {
    return await apiFetch<{ base_movie: Movie; recommendations: Movie[] }>(
      `/recommendations/because-you-liked?profile_id=${profileId}`
    );
  } catch {
    const isNeel = profileId === 'neel';
    const baseMovie = isNeel ? STARTER_MOVIES[4] : STARTER_MOVIES[7]; // Terminator or Titanic
    const recommendations = isNeel
      ? STARTER_MOVIES.filter((m) => m.genres.includes('Action') || m.genres.includes('Sci-Fi')).slice(0, 10)
      : STARTER_MOVIES.filter((m) => m.genres.includes('Drama') || m.genres.includes('Romance')).slice(0, 10);
    return { base_movie: baseMovie, recommendations };
  }
}

export async function fetchAlsoWatched(movieId: number): Promise<Movie[]> {
  try {
    return await apiFetch<Movie[]>(`/recommendations/also-watched/${movieId}`);
  } catch {
    return STARTER_MOVIES.filter((m) => m.id !== movieId).slice(0, 10);
  }
}

export async function fetchAllBrowseRows(
  profileId: string,
  model: 'funk_svd' | 'item_knn' = 'funk_svd'
): Promise<RecommendationRow[]> {
  try {
    // Attempt real backend calls
    const [topPicks, becauseLiked] = await Promise.all([
      fetchPersonalizedRecommendations(profileId, model),
      fetchBecauseYouLiked(profileId),
    ]);

    const alsoWatched = await fetchAlsoWatched(topPicks[0]?.id || 2571);

    const actionMovies = STARTER_MOVIES.filter((m) => m.genres.includes('Action'));
    const sciFiMovies = STARTER_MOVIES.filter((m) => m.genres.includes('Sci-Fi'));
    const dramaMovies = STARTER_MOVIES.filter((m) => m.genres.includes('Drama'));

    return [
      {
        id: 'top-picks',
        title: `Top Picks for ${profileId === 'neel' ? 'Neel' : profileId === 'nitin' ? 'Nitin' : 'You'}`,
        subtitle: `Curated with ${model === 'funk_svd' ? 'Funk-SVD Matrix Factorization' : 'Item-KNN Adjusted Cosine'}`,
        type: 'top_picks',
        movies: topPicks,
      },
      {
        id: 'because-liked',
        title: `Because you liked ${becauseLiked.base_movie.title}`,
        subtitle: 'Item-KNN similarity with Adjusted Cosine & Shrinkage',
        type: 'because_you_liked',
        movies: becauseLiked.recommendations,
      },
      {
        id: 'also-watched',
        title: 'Users Also Watched',
        subtitle: 'Association Rules (Co-occurrence Lift)',
        type: 'also_watched',
        movies: alsoWatched,
      },
      {
        id: 'genre-action',
        title: 'Action & Adventure',
        type: 'genre',
        movies: actionMovies,
      },
      {
        id: 'genre-scifi',
        title: 'Sci-Fi Hits',
        type: 'genre',
        movies: sciFiMovies,
      },
      {
        id: 'genre-drama',
        title: 'Acclaimed Dramas',
        type: 'genre',
        movies: dramaMovies,
      },
    ];
  } catch {
    // Fallback to rich mock data
    return getMockRowsForProfile(profileId, model);
  }
}
