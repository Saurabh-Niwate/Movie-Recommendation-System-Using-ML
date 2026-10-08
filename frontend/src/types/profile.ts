export interface Profile {
  id: string;
  name: string;
  avatar: string;
  bio: string;
  ratings_count: number;
  is_cold_start: boolean;
  genres: string[];
  user_idx?: number | null;
  color_accent: string;
}
