import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// 7 Pure Stitch Pages
import { HomePage } from './pages/HomePage'; // Screen 06: Pre-SignIn Home & Movie Discovery
import { AuthPage } from './pages/AuthPage'; // Screen 03: SignUp / SignIn
import { OnboardingPage } from './pages/OnboardingPage'; // Screen 05: Taste Onboarding & Personalization
import { FeedPage } from './pages/FeedPage'; // Screen 02: Post-SignIn Curated Feed
import { RankingsPage } from './pages/RankingsPage'; // Screen 04: Global Rankings & Ratings
import { WatchlistPage } from './pages/WatchlistPage'; // Screen 01: Watchlist
import { ProfilePage } from './pages/ProfilePage'; // Screen 07: Profile & Vector Settings

const PrivateRoute: React.FC<{ element: React.ReactElement }> = ({ element }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-surface-container-lowest flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-secondary">
          <span className="material-symbols-outlined text-4xl animate-spin">progress_activity</span>
          <span className="text-xs uppercase tracking-widest font-bold text-on-surface-variant">
            Initializing Session...
          </span>
        </div>
      </div>
    );
  }

  return user ? element : <Navigate to="/auth" replace />;
};

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 1. Pre-SignIn Home (Screen 06) */}
      <Route path="/" element={<HomePage />} />

      {/* 2. Authentication (Screen 03) */}
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/login" element={<Navigate to="/auth" replace />} />

      {/* 3. Taste Onboarding (Screen 05) */}
      <Route path="/onboarding" element={<PrivateRoute element={<OnboardingPage />} />} />

      {/* 4. Curated Neural Feed (Screen 02) */}
      <Route path="/feed" element={<PrivateRoute element={<FeedPage />} />} />
      <Route path="/browse" element={<Navigate to="/feed" replace />} />

      {/* 5. Global Leaderboard / Rankings (Screen 04) */}
      <Route path="/rankings" element={<RankingsPage />} />

      {/* 6. Watchlist (Screen 01) */}
      <Route path="/watchlist" element={<PrivateRoute element={<WatchlistPage />} />} />

      {/* 7. Profile & Taste Vectors (Screen 07) */}
      <Route path="/profile" element={<PrivateRoute element={<ProfilePage />} />} />

      {/* Fallback to Home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <AppRoutes />
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
