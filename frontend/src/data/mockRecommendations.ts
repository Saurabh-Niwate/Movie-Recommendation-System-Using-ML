import { Movie, RecommendationRow } from '../types/movie';
import { STARTER_MOVIES } from './starterMovies';

export const NEEL_RECOMMENDATIONS: Movie[] = [
  {
    id: 2571,
    movie_id: 2571,
    title: 'The Matrix (1999)',
    year: 1999,
    genres: ['Action', 'Sci-Fi'],
    poster_path: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.',
    director: 'Lana & Lilly Wachowski',
    cast: ['Keanu Reeves', 'Laurence Fishburne', 'Carrie-Anne Moss'],
    runtime: 136,
    predicted_rating: 4.88,
    match_score: 98,
    avg_rating: 4.3,
  },
  {
    id: 589,
    movie_id: 589,
    title: 'Terminator 2: Judgment Day (1991)',
    year: 1991,
    genres: ['Action', 'Sci-Fi', 'Thriller'],
    poster_path: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'A cyborg protects John Connor from a shape-shifting assassin.',
    director: 'James Cameron',
    cast: ['Arnold Schwarzenegger', 'Linda Hamilton', 'Edward Furlong'],
    runtime: 137,
    predicted_rating: 4.81,
    match_score: 96,
    avg_rating: 4.4,
  },
  {
    id: 1196,
    movie_id: 1196,
    title: 'Star Wars: Episode V - The Empire Strikes Back (1980)',
    year: 1980,
    genres: ['Action', 'Adventure', 'Sci-Fi'],
    poster_path: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'The Empire strikes back while Luke trains with master Yoda.',
    director: 'Irvin Kershner',
    cast: ['Mark Hamill', 'Harrison Ford', 'Carrie Fisher'],
    runtime: 124,
    predicted_rating: 4.79,
    match_score: 95,
    avg_rating: 4.6,
  },
  {
    id: 1240,
    movie_id: 1240,
    title: 'The Terminator (1984)',
    year: 1984,
    genres: ['Action', 'Sci-Fi'],
    poster_path: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'A human soldier is sent back in time to protect Sarah Connor.',
    director: 'James Cameron',
    cast: ['Arnold Schwarzenegger', 'Michael Biehn'],
    runtime: 107,
    predicted_rating: 4.72,
    match_score: 94,
    avg_rating: 4.2,
  },
  {
    id: 480,
    movie_id: 480,
    title: 'Jurassic Park (1993)',
    year: 1993,
    genres: ['Action', 'Adventure', 'Sci-Fi'],
    poster_path: 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'Cloned dinosaurs break loose on a remote island theme park.',
    director: 'Steven Spielberg',
    cast: ['Sam Neill', 'Laura Dern', 'Jeff Goldblum'],
    runtime: 127,
    predicted_rating: 4.65,
    match_score: 92,
    avg_rating: 4.2,
  },
  {
    id: 1200,
    movie_id: 1200,
    title: 'Aliens (1986)',
    year: 1986,
    genres: ['Action', 'Sci-Fi', 'Thriller'],
    poster_path: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'Ellen Ripley returns to the alien-infested moon with colonial marines.',
    director: 'James Cameron',
    cast: ['Sigourney Weaver', 'Michael Biehn', 'Paul Reiser'],
    runtime: 137,
    predicted_rating: 4.60,
    match_score: 91,
    avg_rating: 4.3,
  },
];

export const NITIN_RECOMMENDATIONS: Movie[] = [
  {
    id: 318,
    movie_id: 318,
    title: 'The Shawshank Redemption (1994)',
    year: 1994,
    genres: ['Drama'],
    poster_path: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'Over the course of several years, two convicts form a friendship, seeking consolation and redemption.',
    director: 'Frank Darabont',
    cast: ['Tim Robbins', 'Morgan Freeman'],
    runtime: 142,
    predicted_rating: 4.92,
    match_score: 99,
    avg_rating: 4.8,
  },
  {
    id: 1945,
    movie_id: 1945,
    title: 'Titanic (1997)',
    year: 1997,
    genres: ['Drama', 'Romance'],
    poster_path: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the Titanic.',
    director: 'James Cameron',
    cast: ['Leonardo DiCaprio', 'Kate Winslet'],
    runtime: 194,
    predicted_rating: 4.85,
    match_score: 97,
    avg_rating: 4.1,
  },
  {
    id: 912,
    movie_id: 912,
    title: 'Casablanca (1942)',
    year: 1942,
    genres: ['Drama', 'Romance', 'War'],
    poster_path: 'https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1518676590629-3dcbd9c5a5c9?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'A cynical American cafe owner decides whether to help his former lover escape Nazis in Casablanca.',
    director: 'Michael Curtiz',
    cast: ['Humphrey Bogart', 'Ingrid Bergman'],
    runtime: 102,
    predicted_rating: 4.80,
    match_score: 96,
    avg_rating: 4.6,
  },
  {
    id: 356,
    movie_id: 356,
    title: 'Forrest Gump (1994)',
    year: 1994,
    genres: ['Comedy', 'Drama', 'Romance'],
    poster_path: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'The presidency of Kennedy and Johnson, the Vietnam War and more unfold through the eyes of Forrest Gump.',
    director: 'Robert Zemeckis',
    cast: ['Tom Hanks', 'Robin Wright'],
    runtime: 142,
    predicted_rating: 4.75,
    match_score: 95,
    avg_rating: 4.5,
  },
  {
    id: 2396,
    movie_id: 2396,
    title: 'Shakespeare in Love (1998)',
    year: 1998,
    genres: ['Comedy', 'Romance'],
    poster_path: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'Young Shakespeare is inspired to write Romeo and Juliet by his passionate love affair.',
    director: 'John Madden',
    cast: ['Gwyneth Paltrow', 'Joseph Fiennes'],
    runtime: 123,
    predicted_rating: 4.68,
    match_score: 93,
    avg_rating: 4.1,
  },
  {
    id: 527,
    movie_id: 527,
    title: 'Schindler\'s List (1993)',
    year: 1993,
    genres: ['Drama', 'War'],
    poster_path: 'https://images.unsplash.com/photo-1519791883288-dc8bd696e667?auto=format&fit=crop&w=500&q=80',
    backdrop_path: 'https://images.unsplash.com/photo-1519791883288-dc8bd696e667?auto=format&fit=crop&w=1200&q=80',
    synopsis: 'Oskar Schindler protects his Jewish workforce during World War II.',
    director: 'Steven Spielberg',
    cast: ['Liam Neeson', 'Ralph Fiennes'],
    runtime: 195,
    predicted_rating: 4.64,
    match_score: 92,
    avg_rating: 4.7,
  },
];

export function getMockRowsForProfile(profileId: string, model: 'funk_svd' | 'item_knn' = 'funk_svd'): RecommendationRow[] {
  const isNeel = profileId === 'neel';
  const isNitin = profileId === 'nitin';
  
  const basePicks = isNeel ? NEEL_RECOMMENDATIONS : isNitin ? NITIN_RECOMMENDATIONS : STARTER_MOVIES.slice(0, 8);
  
  // Adjust scores slightly when toggling model so user sees real differences
  const topPicks = basePicks.map(m => {
    const scoreDiff = model === 'item_knn' ? -0.15 : 0;
    const newRating = Math.max(3.5, Math.min(5.0, (m.predicted_rating || 4.5) + scoreDiff));
    return {
      ...m,
      predicted_rating: Number(newRating.toFixed(2)),
      match_score: Math.round(newRating * 20),
    };
  });

  const becauseLikedTitle = isNeel ? 'The Terminator (1984)' : isNitin ? 'Titanic (1997)' : 'The Matrix (1999)';
  const becauseLikedMovies = isNeel
    ? STARTER_MOVIES.filter(m => m.genres.includes('Sci-Fi') || m.genres.includes('Action'))
    : isNitin
    ? STARTER_MOVIES.filter(m => m.genres.includes('Drama') || m.genres.includes('Romance'))
    : STARTER_MOVIES.slice(8, 16);

  const alsoWatchedMovies = STARTER_MOVIES.slice(12, 20);
  const actionMovies = STARTER_MOVIES.filter(m => m.genres.includes('Action'));
  const dramaMovies = STARTER_MOVIES.filter(m => m.genres.includes('Drama'));
  const sciFiMovies = STARTER_MOVIES.filter(m => m.genres.includes('Sci-Fi'));

  return [
    {
      id: 'top-picks',
      title: `Top Picks for ${isNeel ? 'Neel' : isNitin ? 'Nitin' : 'Mukesh'}`,
      subtitle: `Recommended using ${model === 'funk_svd' ? 'Funk-SVD Matrix Factorization' : 'Item-KNN Adjusted Cosine'}`,
      type: 'top_picks',
      movies: topPicks,
    },
    {
      id: 'because-liked',
      title: `Because you liked ${becauseLikedTitle}`,
      subtitle: 'Adjusted Cosine Nearest Neighbors with Significance Shrinkage',
      type: 'because_you_liked',
      movies: becauseLikedMovies,
    },
    {
      id: 'also-watched',
      title: 'Users Also Watched',
      subtitle: 'Association Rules (High Co-occurrence Lift)',
      type: 'also_watched',
      movies: alsoWatchedMovies,
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
}
