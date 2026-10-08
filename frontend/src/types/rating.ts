export interface RatingSubmission {
  movie_id: number;
  rating: number;
}

export interface RatingResponse {
  status: string;
  ratings_count: number;
  unlocked: boolean;
  fold_in_time_ms?: number;
  message?: string;
}

export interface RatingRecord {
  movie_id: number;
  rating: number;
  rated_at?: string;
}
