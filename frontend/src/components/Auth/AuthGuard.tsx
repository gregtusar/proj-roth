import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { Spinner } from 'baseui/spinner';
import { styled } from 'baseui';

const LoadingContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100vh',
  width: '100vw',
});

interface AuthGuardProps {
  children: React.ReactNode;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useSelector(
    (state: RootState) => state.auth
  );
  const location = useLocation();

  if (isLoading) {
    return (
      <LoadingContainer>
        <Spinner $size={96} />
      </LoadingContainer>
    );
  }

  if (!isAuthenticated) {
    // Save the attempted location to redirect back after login
    const redirectTo = location.pathname + location.search;
    return <Navigate to="/login" state={{ from: redirectTo }} replace />;
  }

  return <>{children}</>;
};

export default AuthGuard;