import React, { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from './store';
import { refreshToken } from './store/authSlice';
import wsService from './services/websocket';

// Components
import AuthGuard from './components/Auth/AuthGuard';
import GoogleSignIn from './components/Auth/GoogleSignIn';
import MainLayout from './components/Layout/MainLayout';
import ChatContainer from './components/Chat/ChatContainer';
import ListManager from './components/ListManager/ListManager';

function App() {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    // Try to refresh token on app load
    const token = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    
    if (token && refresh) {
      dispatch(refreshToken());
    }
  }, [dispatch]);

  useEffect(() => {
    // Connect WebSocket when authenticated
    if (isAuthenticated) {
      wsService.connect();
    } else {
      wsService.disconnect();
    }

    return () => {
      wsService.disconnect();
    };
  }, [isAuthenticated]);

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
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;