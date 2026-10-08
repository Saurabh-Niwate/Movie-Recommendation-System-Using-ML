import React from 'react';
import { Film } from 'lucide-react';

interface FallbackPosterProps {
  title: string;
  genres?: string[];
  className?: string;
  aspectRatio?: 'poster' | 'backdrop';
}

export const FallbackPoster: React.FC<FallbackPosterProps> = ({
  title,
  genres = [],
  className = '',
  aspectRatio = 'poster',
}) => {
  return (
    <div
      className={`relative w-full h-full flex flex-col justify-between p-4 bg-gradient-to-br from-zinc-800 via-zinc-900 to-black text-white overflow-hidden border border-zinc-800 select-none ${className}`}
      style={{
        aspectRatio: aspectRatio === 'poster' ? '2/3' : '16/9',
      }}
    >
      <div className="flex items-center justify-between opacity-50">
        <Film className="w-5 h-5 text-netflix-red" />
        <span className="text-[10px] uppercase font-mono tracking-wider text-zinc-400">
          CineMatch
        </span>
      </div>

      <div className="my-auto text-center py-2">
        <h4 className="font-bold text-sm md:text-base leading-tight drop-shadow line-clamp-2">
          {title}
        </h4>
        {genres.length > 0 && (
          <p className="text-[11px] text-zinc-400 mt-1 line-clamp-1">
            {genres.slice(0, 2).join(' • ')}
          </p>
        )}
      </div>

      <div className="flex items-center justify-center opacity-30 text-[9px] uppercase tracking-widest text-zinc-500">
        MovieLens 1M
      </div>
    </div>
  );
};
