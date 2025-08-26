import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { RootState, AppDispatch } from '../../store';
import { loadSession, clearMessages } from '../../store/chatSlice';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import wsService from '../../services/websocket';

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  width: '100%',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#ffffff',
  transition: 'background-color 0.3s ease',
}));

const Header = styled('div', {
  padding: '16px 24px',
  borderBottom: '1px solid #e0e0e0',
  backgroundColor: '#ffffff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
});

const Title = styled('h2', {
  margin: 0,
  fontSize: '18px',
  fontWeight: 600,
});

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

  useEffect(() => {
    console.log('[ChatContainer] Route changed to:', sessionId, 'Current session:', currentSessionId);
    
    if (!sessionId || sessionId === 'new') {
      // Clear for new chat
      dispatch(clearMessages());
      wsService.setActiveSession(null);
    } else if (sessionId !== currentSessionId) {
      // Only load if it's a different session to prevent duplicate loads
      console.log('[ChatContainer] Loading different session:', sessionId);
      
      // Notify WebSocket service that we're loading
      wsService.setLoadingSession(true);
      wsService.clearMessageQueue();
      
      // Load the session
      dispatch(loadSession(sessionId)).then(() => {
        // After loading is complete, update WebSocket service
        wsService.setLoadingSession(false);
        wsService.setActiveSession(sessionId);
      });
    } else {
      console.log('[ChatContainer] Same session, skipping load:', sessionId);
    }
  }, [sessionId, dispatch, currentSessionId]); // Dependencies

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
      <ChatArea>
        <MessageList />
        <div ref={messagesEndRef} />
        <MessageInput />
      </ChatArea>
    </Container>
  );
};

export default ChatContainer;