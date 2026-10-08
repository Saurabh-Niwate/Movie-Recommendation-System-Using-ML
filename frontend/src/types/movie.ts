export interface Movie {
  id: number;
  movie_id: number;
  title: string;
  year?: number;
  genres: string[];
  poster_path?: string | null;
  backdrop_path?: string | null;
  synopsis?: string | null;
  overview?: string | null;
  cast?: string[];
  director?: string | null;
  runtime?: number | null;
  predicted_rating?: number;
  match_score?: number;
  avg_rating?: number;
  vote_count?: number;
}

export interface RecommendationRow {
  id: string;
  title: string;
  subtitle?: string;
  type: 'top_picks' | 'because_you_liked' | 'also_watched' | 'genre';
  movies: Movie[];
}
