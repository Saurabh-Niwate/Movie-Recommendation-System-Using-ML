import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { ModelProvider } from './context/ModelContext';
import { ProfileProvider } from './context/ProfileContext';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ProfilePickerPage } from './pages/ProfilePickerPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { BrowsePage } from './pages/BrowsePage';
import { ModelLabPage } from './pages/ModelLabPage';
import { ProtectedBrowseRoute } from './components/guards/ProtectedBrowseRoute';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <ToastProvider>
        <ModelProvider>
          <ProfileProvider>
            <Routes>
              {/* Default Redirect to Profile Picker */}
              <Route path="/" element={<Navigate to="/profiles" replace />} />

              {/* Profile Picker Screen */}
              <Route path="/profiles" element={<ProfilePickerPage />} />

              {/* Cold-start Onboarding Screen */}
              <Route path="/onboarding" element={<OnboardingPage />} />

              {/* Protected Browse Page */}
              <Route
                path="/browse"
                element={
                  <ProtectedBrowseRoute>
                    <BrowsePage />
                  </ProtectedBrowseRoute>
                }
              />

              {/* Model Lab Dashboard */}
              <Route path="/model-lab" element={<ModelLabPage />} />

              {/* Catch-all redirect */}
              <Route path="*" element={<Navigate to="/profiles" replace />} />
            </Routes>
          </ProfileProvider>
        </ModelProvider>
      </ToastProvider>
    </BrowserRouter>
  </ErrorBoundary>
);
};

export default App;
