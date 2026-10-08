import React, { useRef } from 'react';
import { RecommendationRow, Movie } from '../../types/movie';
import { MovieCard } from './MovieCard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface MovieCarouselProps {
  row: RecommendationRow;
  onSelectMovie: (movie: Movie) => void;
  userRatings?: Record<number, number>;
}

export const MovieCarousel: React.FC<MovieCarouselProps> = ({
  row,
  onSelectMovie,
  userRatings = {},
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (scrollRef.current) {
      const { scrollLeft, clientWidth } = scrollRef.current;
      const scrollAmount = clientWidth * 0.75;
      scrollRef.current.scrollTo({
        left: direction === 'left' ? scrollLeft - scrollAmount : scrollLeft + scrollAmount,
        behavior: 'smooth',
      });
    }
  };

  if (!row.movies || row.movies.length === 0) {
    return null;
  }

  return (
    <div className="relative py-4 group/row">
      {/* Row Header */}
      <div className="px-4 md:px-8 mb-2 flex items-baseline justify-between">
        <div>
          <h3 className="text-lg md:text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <span>{row.title}</span>
          </h3>
          {row.subtitle && (
            <p className="text-xs text-zinc-400 mt-0.5 font-medium">
              {row.subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Horizontal Scroll Area */}
      <div className="relative">
        {/* Left Arrow */}
        <button
          onClick={() => scroll('left')}
          className="absolute left-0 top-0 bottom-0 z-30 w-10 md:w-12 bg-black/60 hover:bg-black/90 text-white opacity-0 group-hover/row:opacity-100 transition-all flex items-center justify-center backdrop-blur-sm"
          aria-label="Scroll left"
        >
          <ChevronLeft className="w-6 h-6 hover:scale-125 transition-transform" />
        </button>

        <div
          ref={scrollRef}
          className="flex gap-3 md:gap-4 overflow-x-auto hide-scrollbar px-4 md:px-8 py-2 scroll-smooth"
        >
          {row.movies.map((movie) => (
            <MovieCard
              key={`${row.id}-${movie.id || movie.movie_id}`}
              movie={movie}
              onSelect={onSelectMovie}
              userRating={userRatings[movie.id || movie.movie_id]}
            />
          ))}
        </div>

        {/* Right Arrow */}
        <button
          onClick={() => scroll('right')}
          className="absolute right-0 top-0 bottom-0 z-30 w-10 md:w-12 bg-black/60 hover:bg-black/90 text-white opacity-0 group-hover/row:opacity-100 transition-all flex items-center justify-center backdrop-blur-sm"
          aria-label="Scroll right"
        >
          <ChevronRight className="w-6 h-6 hover:scale-125 transition-transform" />
        </button>
      </div>
    </div>
  );
};
