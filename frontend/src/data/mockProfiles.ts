import { Profile } from '../types/profile';

export const INITIAL_PROFILES: Profile[] = [
  {
    id: 'neel',
    name: 'Neel',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    bio: 'Action & Sci-Fi Enthusiast (MovieLens Cluster 1)',
    ratings_count: 62,
    is_cold_start: false,
    genres: ['Action', 'Sci-Fi', 'Adventure'],
    user_idx: 2955,
    color_accent: 'from-cyan-600 to-blue-700',
  },
  {
    id: 'nitin',
    name: 'Nitin',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
    bio: 'Drama & Romance Connoisseur (MovieLens Cluster 2)',
    ratings_count: 58,
    is_cold_start: false,
    genres: ['Drama', 'Romance'],
    user_idx: 2583,
    color_accent: 'from-purple-600 to-pink-700',
  },
  {
    id: 'mukesh',
    name: 'Mukesh',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
    bio: 'New Explorer (Cold Start Profile — Rate 6 to unlock)',
    ratings_count: 0,
    is_cold_start: true,
    genres: [],
    user_idx: null,
    color_accent: 'from-amber-600 to-emerald-700',
  },
];
