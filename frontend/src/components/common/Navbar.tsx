import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useProfile } from '../../context/ProfileContext';
import { useModel } from '../../context/ModelContext';
import { Cpu, ChevronDown, User, Sparkles, Layers } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { activeProfile, profiles, selectProfile } = useProfile();
  const { selectedModel, toggleModel } = useModel();
  const [isScrolled, setIsScrolled] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-40 transition-colors duration-300 ${
        isScrolled ? 'bg-[#141414]/95 backdrop-blur-md shadow-xl' : 'bg-gradient-to-b from-black/80 via-black/40 to-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Left Navigation */}
        <div className="flex items-center gap-8">
          <Link to="/browse" className="flex items-center gap-2 group">
            <span className="text-[#E50914] font-black text-2xl tracking-tighter uppercase drop-shadow-md group-hover:scale-105 transition-transform">
              CineMatch
            </span>
            <span className="hidden sm:inline-block text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
              RecSys
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6 text-sm font-medium">
            <Link
              to="/browse"
              className={`transition-colors hover:text-white ${
                location.pathname === '/browse' ? 'text-white font-bold' : 'text-zinc-400'
              }`}
            >
              Browse
            </Link>
            <Link
              to="/model-lab"
              className={`flex items-center gap-1.5 transition-colors hover:text-white ${
                location.pathname === '/model-lab' ? 'text-white font-bold' : 'text-zinc-400'
              }`}
            >
              <Cpu className="w-4 h-4 text-[#E50914]" />
              <span>Model Lab</span>
            </Link>
          </div>
        </div>

        {/* Right Section: Model Pill & Profile Dropdown */}
        <div className="flex items-center gap-4">
          {/* Active Model Indicator Pill */}
          <div className="relative">
            <button
              onClick={() => setShowModelMenu(!showModelMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/90 hover:bg-zinc-800 border border-zinc-700/80 text-xs font-semibold text-zinc-200 transition-all shadow-inner"
              title="Click to toggle recommendation algorithm"
            >
              <Layers className="w-3.5 h-3.5 text-[#E50914]" />
              <span className="hidden sm:inline text-zinc-400">Algorithm:</span>
              <span className="text-white">
                {selectedModel === 'funk_svd' ? 'Funk-SVD' : 'Item-KNN'}
              </span>
              <ChevronDown className="w-3 h-3 text-zinc-400" />
            </button>

            {showModelMenu && (
              <div
                className="absolute right-0 mt-2 w-64 bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl py-2 z-50"
                onMouseLeave={() => setShowModelMenu(false)}
              >
                <div className="px-3 py-1.5 border-b border-zinc-800 text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                  Active RecSys Model
                </div>
                <button
                  onClick={() => {
                    if (selectedModel !== 'funk_svd') toggleModel();
                    setShowModelMenu(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-zinc-800 transition-colors ${
                    selectedModel === 'funk_svd' ? 'text-white bg-zinc-800/60 font-semibold' : 'text-zinc-400'
                  }`}
                >
                  <div>
                    <div className="font-bold text-white">Funk-SVD</div>
                    <div className="text-[10px] text-zinc-500">Biased SGD + Closed-Form Fold-In</div>
                  </div>
                  {selectedModel === 'funk_svd' && <Sparkles className="w-3.5 h-3.5 text-[#E50914]" />}
                </button>
                <button
                  onClick={() => {
                    if (selectedModel !== 'item_knn') toggleModel();
                    setShowModelMenu(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-zinc-800 transition-colors ${
                    selectedModel === 'item_knn' ? 'text-white bg-zinc-800/60 font-semibold' : 'text-zinc-400'
                  }`}
                >
                  <div>
                    <div className="font-bold text-white">Item-KNN</div>
                    <div className="text-[10px] text-zinc-500">Adjusted Cosine & Shrinkage</div>
                  </div>
                  {selectedModel === 'item_knn' && <Sparkles className="w-3.5 h-3.5 text-[#E50914]" />}
                </button>
                <div className="pt-1 mt-1 border-t border-zinc-800 px-3">
                  <Link
                    to="/model-lab"
                    onClick={() => setShowModelMenu(false)}
                    className="text-[11px] text-[#E50914] hover:underline flex items-center gap-1 py-1"
                  >
                    Compare in Model Lab →
                  </Link>
                </div>
              </div>
            )}
          </div>

          {/* Profile Switcher */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 group p-1 rounded-md hover:bg-zinc-800/50 transition-colors"
            >
              {activeProfile ? (
                <div className="relative">
                  <img
                    src={activeProfile.avatar}
                    alt={activeProfile.name}
                    className="w-8 h-8 rounded object-cover border border-zinc-700"
                  />
                  {activeProfile.is_cold_start && (
                    <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-500 border border-zinc-900" />
                  )}
                </div>
              ) : (
                <div className="w-8 h-8 rounded bg-zinc-800 flex items-center justify-center text-zinc-400">
                  <User className="w-4 h-4" />
                </div>
              )}
              <span className="hidden sm:inline text-xs font-medium text-zinc-200">
                {activeProfile ? activeProfile.name : 'Select Profile'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-zinc-400 group-hover:text-white transition-colors" />
            </button>

            {showProfileMenu && (
              <div
                className="absolute right-0 mt-2 w-56 bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl py-2 z-50"
                onMouseLeave={() => setShowProfileMenu(false)}
              >
                <div className="px-3 py-1.5 border-b border-zinc-800 text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                  Switch Profiles
                </div>
                {profiles.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      selectProfile(p);
                      setShowProfileMenu(false);
                      if (p.id === 'mukesh' && p.is_cold_start && p.ratings_count < 6) {
                        navigate('/onboarding');
                      } else {
                        navigate('/browse');
                      }
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center gap-2.5 hover:bg-zinc-800 transition-colors ${
                      activeProfile?.id === p.id ? 'bg-zinc-800/70 text-white font-semibold' : 'text-zinc-300'
                    }`}
                  >
                    <img
                      src={p.avatar}
                      alt={p.name}
                      className="w-6 h-6 rounded object-cover"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="truncate">{p.name}</div>
                      <div className="text-[10px] text-zinc-500 truncate">
                        {p.id === 'mukesh'
                          ? 'Cold Start Profile'
                          : (p.genres || []).slice(0, 2).join(', ')}
                      </div>
                    </div>
                  </button>
                ))}
                <div className="pt-2 mt-1 border-t border-zinc-800 px-3">
                  <button
                    onClick={() => {
                      setShowProfileMenu(false);
                      navigate('/profiles');
                    }}
                    className="w-full text-left text-xs text-zinc-400 hover:text-white py-1 flex items-center gap-1.5"
                  >
                    <User className="w-3.5 h-3.5" />
                    <span>Who&apos;s Watching?</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};
