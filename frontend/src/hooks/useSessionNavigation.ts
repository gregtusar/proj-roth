import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

export const useSessionNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentSessionId } = useSelector((state: RootState) => state.chat);
  const lastSessionIdRef = useRef<string | null>(null);

  useEffect(() => {
    // When a new session is created and we're on /chat/new, navigate to the new session
    if (
      currentSessionId && 
      currentSessionId !== lastSessionIdRef.current &&
      (location.pathname === '/chat/new' || location.pathname === '/chat')
    ) {
      console.log('[useSessionNavigation] Navigating to new session:', currentSessionId);
      navigate(`/chat/${currentSessionId}`, { replace: true });
      lastSessionIdRef.current = currentSessionId;
    }
  }, [currentSessionId, location.pathname, navigate]);
};