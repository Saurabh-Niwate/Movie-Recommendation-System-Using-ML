import React, { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useProfile } from '../../context/ProfileContext';

interface ProtectedBrowseRouteProps {
  children: ReactNode;
}

export const ProtectedBrowseRoute: React.FC<ProtectedBrowseRouteProps> = ({ children }) => {
  const { activeProfile, ratingsCount, isMukeshUnlocked } = useProfile();

  // If no profile selected, go to profile picker
  if (!activeProfile) {
    return <Navigate to="/profiles" replace />;
  }

  // If Mukesh and not unlocked and ratings count < 6, guard and redirect to onboarding!
  if (
    activeProfile.id === 'mukesh' &&
    !isMukeshUnlocked &&
    ratingsCount < 6
  ) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
};
