import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from './store';
import { refreshToken } from './store/authSlice';
import { loadChatSessions } from './store/chatSlice';
import wsService from './services/websocket';
import { logVersionInfo } from './config/version';

// Components
import AuthGuard from './components/Auth/AuthGuard';
import GoogleSignIn from './components/Auth/GoogleSignIn';
import MainLayout from './components/Layout/MainLayout';
import ChatContainer from './components/Chat/ChatContainer';
import ListManager from './components/ListManager/ListManager';
import StreetMap from './components/StreetMap/StreetMap';
import Settings from './components/Settings/Settings';

function App() {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    // Log version info on app startup
    logVersionInfo();
    
    // Initialize dark mode preference
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
      document.documentElement.classList.add('dark-mode');
    }
    
    // Try to refresh token on app load
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    
    if (token && refresh) {
      dispatch(refreshToken());
    }
  }, [dispatch]);

  useEffect(() => {
    // Connect WebSocket and load sessions when authenticated
    if (isAuthenticated) {
      wsService.connect();
      // Load user's chat sessions on app startup
      dispatch(loadChatSessions());
    } else {
      wsService.disconnect();
    }

    return () => {
      wsService.disconnect();
    };
  }, [isAuthenticated, dispatch]);

  return (
    <Routes>
      <Route path="/login" element={<GoogleSignIn />} />
      <Route
        path="/"
        element={
          <AuthGuard>
            <MainLayout />
          </AuthGuard>
        }
      >
        <Route index element={<ChatContainer />} />
        <Route path="chat" element={<ChatContainer />} />
        <Route path="chat/:sessionId" element={<ChatContainer />} />
        <Route path="lists" element={<ListManager />} />
        <Route path="street-map" element={<StreetMap />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;