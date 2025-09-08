import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Box, Typography } from '@mui/material';
import { RootState, AppDispatch } from '../../store';
import { loadSession, clearMessages } from '../../store/chatSlice';
import { useSessionNavigation } from '../../hooks/useSessionNavigation';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ModelSelector, { AVAILABLE_MODELS } from './ModelSelector';
import wsService from '../../services/websocket';

const Container = styled<'div', { $isDarkMode: boolean }>('div', ({ $isDarkMode }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  width: '100%',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#ffffff',
  transition: 'background-color 0.3s ease',
}));

const ChatArea = styled('div', {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
});

const ChatContainer: React.FC = () => {
  const { sessionId } = useParams();
  const dispatch = useDispatch<AppDispatch>();
  const { currentSessionId } = useSelector((state: RootState) => state.chat);
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const lastLoadedSessionRef = useRef<string | null>(null);
  
  // Model selection state - default to Fast model
  const [selectedModel, setSelectedModel] = useState<string>(
    localStorage.getItem('defaultModel') || AVAILABLE_MODELS[0].id
  );

  // Use the session navigation hook to handle navigation when sessions are created
  useSessionNavigation();
  
  // Handle model change
  const handleModelChange = (modelId: string) => {
    setSelectedModel(modelId);
    // Store as default preference
    localStorage.setItem('defaultModel', modelId);
    
    // If we have an active session, update it
    if (currentSessionId) {
      // TODO: Update session model in backend
      wsService.updateSessionModel(currentSessionId, modelId);
    }
  };

  useEffect(() => {
    console.log('[ChatContainer] Route changed to:', sessionId, 'Current sessionId:', currentSessionId, 'Last loaded:', lastLoadedSessionRef.current);
    
    if (!sessionId || sessionId === 'new') {
      // Clear for new chat only if we don't have a current session
      // This prevents clearing when a session is being created
      if (!currentSessionId) {
        dispatch(clearMessages());
        wsService.setActiveSession(null);
        lastLoadedSessionRef.current = null;
      }
    } else if (sessionId !== lastLoadedSessionRef.current) {
      // Only load if we haven't already loaded this session
      console.log('[ChatContainer] Loading session (not previously loaded):', sessionId);
      lastLoadedSessionRef.current = sessionId;
      
      // Notify WebSocket service that we're loading
      wsService.setLoadingSession(true);
      wsService.setActiveSession(null); // Clear active session during load
      
      // Load the session
      dispatch(loadSession(sessionId))
        .unwrap()
        .then(() => {
          // After loading is complete, update WebSocket service
          wsService.setLoadingSession(false);
          wsService.setActiveSession(sessionId);
        })
        .catch((error) => {
          console.error('[ChatContainer] Failed to load session:', error);
          wsService.setLoadingSession(false);
          lastLoadedSessionRef.current = null; // Reset on error
        });
    } else {
      console.log('[ChatContainer] Already loaded this session, skipping:', sessionId);
      // Make sure WebSocket knows the active session
      wsService.setActiveSession(sessionId);
    }
  }, [sessionId, dispatch, currentSessionId]); // Include currentSessionId to track state

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Scroll when messages change
  const { messages } = useSelector((state: RootState) => state.chat);
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Container $isDarkMode={isDarkMode}>
      <Box 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          padding: '12px 24px',
          borderBottom: '1px solid',
          borderColor: isDarkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
          backgroundColor: isDarkMode ? '#2a2a2a' : '#f5f5f5'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Model:
          </Typography>
          <ModelSelector 
            value={selectedModel}
            onChange={handleModelChange}
            disabled={false}
            showDescription={false}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          {sessionId && sessionId !== 'new' ? `Session: ${sessionId.slice(0, 8)}...` : 'New Chat'}
        </Typography>
      </Box>
      <ChatArea>
        <MessageList />
        <div ref={messagesEndRef} />
        <MessageInput modelId={selectedModel} />
      </ChatArea>
    </Container>
  );
};

export default ChatContainer;