import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, signOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const navItemClass = (path: string) => {
    return isActive(path)
      ? 'px-4 py-1.5 rounded-full transition-all bg-primary-container text-on-primary-container font-semibold shadow-[0_0_12px_rgba(128,131,255,0.35)] text-sm'
      : 'px-4 py-1.5 rounded-full font-medium text-sm text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/60 transition-all';
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/80 backdrop-blur-2xl shadow-[0_1px_12px_rgba(0,0,0,0.4)]">
      <div className="h-20 w-full px-4 sm:px-8 md:px-12 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-2 group shrink-0">
          <div className="flex items-baseline gap-1">
            <span className="font-extrabold text-lg text-on-surface tracking-tight">MVZ</span>
            <span className="font-bold text-[11px] text-secondary uppercase tracking-widest bg-surface-container-lowest/80 px-1 py-0.5 rounded">
              Recommender
            </span>
          </div>
        </Link>

        {/* Center Pill Navigation */}
        <div className="flex items-center justify-center">
          <nav className="flex items-center p-1 bg-surface-container-low/90 backdrop-blur-md rounded-full shadow-[inset_0_1px_4px_rgba(0,0,0,0.6)] border border-outline-variant/30">
            <Link to="/" className={navItemClass('/')}>
              Explore
            </Link>
            {user && (
              <Link to="/feed" className={navItemClass('/feed')}>
                Feed
              </Link>
            )}
            <Link to="/watchlist" className={navItemClass('/watchlist')}>
              Watchlist
            </Link>
            <Link to="/rankings" className={navItemClass('/rankings')}>
              Rankings
            </Link>
          </nav>
        </div>

        {/* Right Auth / Profile Controls */}
        <div className="flex items-center gap-3 shrink-0">
          {user ? (
            <div className="flex items-center gap-3">
              <Link
                to="/profile"
                className="relative flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-container hover:bg-surface-container-high transition-all border border-outline-variant/30"
              >
                <div className="relative w-7 h-7 rounded-full bg-primary-container text-on-primary-container font-bold text-xs flex items-center justify-center uppercase">
                  {(user.full_name || user.name || user.email || 'U').charAt(0)}
                  <span className="absolute bottom-0 right-0 w-2 h-2 rounded-full bg-secondary ring-2 ring-surface-container-lowest"></span>
                </div>
                <span className="text-xs font-semibold text-on-surface max-w-[120px] truncate hidden sm:inline">
                  {user.full_name || user.name || (user.email ? user.email.split('@')[0] : 'Curator')}
                </span>
              </Link>
              <button
                onClick={() => {
                  signOut();
                  navigate('/');
                }}
                className="px-3.5 py-1.5 rounded-full text-xs font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/60 transition-all border border-outline-variant/20"
                title="Sign out of account"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 sm:gap-3">
              <Link
                to="/auth?mode=signin"
                className="px-3.5 py-1.5 rounded-full text-xs sm:text-sm font-semibold text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/60 transition-all"
              >
                Sign In
              </Link>
              <Link
                to="/auth?mode=signup"
                className="px-4 py-1.5 rounded-full bg-gradient-to-r from-secondary-container via-primary-container to-secondary text-on-secondary-container font-bold text-xs sm:text-sm shadow-[0_0_16px_rgba(76,215,246,0.35)] hover:scale-105 active:scale-95 transition-all"
              >
                Sign Up Free
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
