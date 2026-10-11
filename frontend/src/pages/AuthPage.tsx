import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const AuthPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') === 'signup' ? 'signup' : 'signin';
  const [mode, setMode] = useState<'signin' | 'signup'>(initialMode);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { signIn, signUp, user } = useAuth();
  const navigate = useNavigate();

  // If already logged in, redirect appropriately
  useEffect(() => {
    if (user) {
      if (user.is_cold_start || user.ratings_count < 6) {
        navigate('/onboarding', { replace: true });
      } else {
        navigate('/feed', { replace: true });
      }
    }
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setLoading(true);

    try {
      if (mode === 'signin') {
        const loggedInUser = await signIn(email.trim(), password);
        if (loggedInUser.is_cold_start || loggedInUser.ratings_count < 6) {
          navigate('/onboarding', { replace: true });
        } else {
          navigate('/feed', { replace: true });
        }
      } else {
        const nameToUse = fullName.trim() || email.split('@')[0];
        await signUp(email.trim(), password, nameToUse);
        navigate('/onboarding', { replace: true });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed';
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-surface-container-lowest font-body-md text-on-surface antialiased min-h-screen relative overflow-x-hidden selection:bg-secondary/30 selection:text-secondary">
      {/* Background Ambient Glows */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute top-[-10%] right-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(128,131,255,0.12),transparent_70%)] blur-3xl"></div>
        <div className="absolute bottom-[-10%] left-[-5%] w-[600px] h-[600px] rounded-full bg-[radial-gradient(circle_at_center,rgba(76,215,246,0.08),transparent_70%)] blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-surface-container-lowest/80 backdrop-blur-2xl shadow-[0_1px_12px_rgba(0,0,0,0.4)]">
        <div className="h-20 w-full px-6 md:px-12 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-baseline gap-1">
            <span className="font-extrabold text-base text-on-surface tracking-tight">MVZ</span>
            <span className="font-bold text-xs text-secondary uppercase tracking-widest">Recommender</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm font-semibold text-on-surface-variant hover:text-on-surface transition-colors">
              Explore Catalog
            </Link>
          </div>
        </div>
      </header>

      {/* Main Glassmorphic Auth Card */}
      <main className="relative z-10 w-full pt-20 px-4 sm:px-6 min-h-screen pb-12 flex items-center justify-center">
        <div className="relative w-full max-w-xl mx-auto my-auto py-6 sm:py-8">
          <div className="pointer-events-none absolute -top-24 left-1/4 w-96 h-96 bg-primary-container/20 rounded-full blur-[100px] -z-10"></div>
          <div className="pointer-events-none absolute -bottom-20 right-1/4 w-[420px] h-[420px] bg-secondary-container/15 rounded-full blur-[110px] -z-10"></div>

          <div className="relative w-full rounded-2xl bg-surface-container-low/70 backdrop-blur-2xl shadow-[0_20px_60px_-15px_rgba(0,0,0,0.85)] border border-outline-variant/30 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-secondary/40 to-transparent"></div>

            <div className="w-full p-6 sm:p-10 flex flex-col justify-between bg-surface-container-lowest/80 backdrop-blur-xl">
              <div className="max-w-md w-full mx-auto space-y-6">
                {/* Switcher Pill Tabs */}
                <div className="flex items-center justify-between pb-2">
                  <div className="p-1 bg-surface-container-high/60 backdrop-blur-md rounded-full flex items-center w-full max-w-xs mx-auto border border-outline-variant/30">
                    <button
                      type="button"
                      onClick={() => {
                        setMode('signin');
                        setErrorMessage(null);
                      }}
                      className={`flex-1 py-1.5 px-4 rounded-full text-xs sm:text-sm font-semibold text-center transition-all ${
                        mode === 'signin'
                          ? 'bg-primary-container text-on-primary-container shadow-[0_0_12px_rgba(128,131,255,0.4)]'
                          : 'text-on-surface-variant hover:text-on-surface'
                      }`}
                    >
                      Sign In
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setMode('signup');
                        setErrorMessage(null);
                      }}
                      className={`flex-1 py-1.5 px-4 rounded-full text-xs sm:text-sm font-semibold text-center transition-all ${
                        mode === 'signup'
                          ? 'bg-primary-container text-on-primary-container shadow-[0_0_12px_rgba(128,131,255,0.4)]'
                          : 'text-on-surface-variant hover:text-on-surface'
                      }`}
                    >
                      Sign Up
                    </button>
                  </div>
                </div>

                {/* Title */}
                <div className="space-y-1 text-center">
                  <h1 className="text-2xl sm:text-3xl font-extrabold text-on-surface tracking-tight">
                    {mode === 'signin' ? 'Sign In to MVZ' : 'Create Free Account'}
                  </h1>
                </div>

                {/* Error Banner */}
                {errorMessage && (
                  <div className="p-3 rounded-lg bg-error-container/20 border border-error/40 text-error text-xs sm:text-sm flex items-center gap-2">
                    <span className="material-symbols-outlined text-base">error</span>
                    <span>{errorMessage}</span>
                  </div>
                )}

                {/* Form */}
                <form className="space-y-4" onSubmit={handleSubmit}>
                  {mode === 'signup' && (
                    <div className="space-y-1">
                      <label className="block text-xs font-semibold text-on-surface-variant" htmlFor="fullName">
                        Full Name
                      </label>
                      <div className="relative flex items-center rounded-xl bg-surface-container-high/50 border border-outline-variant/30 transition-all duration-200 group focus-within:bg-surface-container-high focus-within:border-secondary focus-within:shadow-[0_0_16px_rgba(76,215,246,0.2)]">
                        <div className="pl-4 flex items-center pointer-events-none text-outline group-focus-within:text-secondary">
                          <span className="material-symbols-outlined text-lg">person</span>
                        </div>
                        <input
                          id="fullName"
                          type="text"
                          required={mode === 'signup'}
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          placeholder="Alex Mercer"
                          className="w-full py-3 px-3 bg-transparent text-on-surface placeholder:text-outline/60 text-sm focus:outline-none"
                        />
                      </div>
                    </div>
                  )}

                  <div className="space-y-1">
                    <label className="block text-xs font-semibold text-on-surface-variant" htmlFor="email">
                      Email Address
                    </label>
                    <div className="relative flex items-center rounded-xl bg-surface-container-high/50 border border-outline-variant/30 transition-all duration-200 group focus-within:bg-surface-container-high focus-within:border-secondary focus-within:shadow-[0_0_16px_rgba(76,215,246,0.2)]">
                      <div className="pl-4 flex items-center pointer-events-none text-outline group-focus-within:text-secondary">
                        <span className="material-symbols-outlined text-lg">mail</span>
                      </div>
                      <input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="alex@cinema.io"
                        className="w-full py-3 px-3 bg-transparent text-on-surface placeholder:text-outline/60 text-sm focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <label className="block text-xs font-semibold text-on-surface-variant" htmlFor="password">
                        Password
                      </label>
                      {mode === 'signin' && (
                        <span className="text-xs text-secondary hover:text-secondary-fixed cursor-pointer transition-colors">
                          Forgot password?
                        </span>
                      )}
                    </div>
                    <div className="relative flex items-center rounded-xl bg-surface-container-high/50 border border-outline-variant/30 transition-all duration-200 group focus-within:bg-surface-container-high focus-within:border-secondary focus-within:shadow-[0_0_16px_rgba(76,215,246,0.2)]">
                      <div className="pl-4 flex items-center pointer-events-none text-outline group-focus-within:text-secondary">
                        <span className="material-symbols-outlined text-lg">lock</span>
                      </div>
                      <input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••••••"
                        className="w-full py-3 px-3 bg-transparent text-on-surface placeholder:text-outline/60 text-sm focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        aria-label="Toggle password visibility"
                        className="pr-4 flex items-center text-outline hover:text-on-surface transition-colors"
                      >
                        <span className="material-symbols-outlined text-lg">
                          {showPassword ? 'visibility_off' : 'visibility'}
                        </span>
                      </button>
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={loading}
                      className="relative w-full py-3 px-6 rounded-full bg-gradient-to-r from-primary-container via-inverse-primary to-primary-container text-on-primary font-bold text-sm tracking-tight shadow-[0_0_20px_rgba(128,131,255,0.4)] hover:shadow-[0_0_30px_rgba(128,131,255,0.6)] hover:brightness-110 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                      {loading ? (
                        <>
                          <span className="material-symbols-outlined text-lg animate-spin">progress_activity</span>
                          <span>Signing in...</span>
                        </>
                      ) : (
                        <span>{mode === 'signin' ? 'Sign In' : 'Create Account'}</span>
                      )}
                    </button>
                  </div>
                </form>

                {/* Footer Switcher */}
                <div className="space-y-3 pt-2 text-center">
                  <p className="text-xs text-on-surface-variant">
                    {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
                    <button
                      type="button"
                      onClick={() => {
                        setMode(mode === 'signin' ? 'signup' : 'signin');
                        setErrorMessage(null);
                      }}
                      className="text-primary font-semibold hover:underline"
                    >
                      {mode === 'signin' ? 'Sign Up for free' : 'Sign In'}
                    </button>
                  </p>

                  <div className="flex items-center justify-center gap-2 text-outline text-[11px]">
                    <span className="material-symbols-outlined text-[13px]">encrypted</span>
                    <span>256-bit Encrypted Session</span>
                    <span>•</span>
                    <span>Zero Ad Tracking</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
