import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { RootState, AppDispatch } from '../../store';
import { loadSession, clearMessages } from '../../store/chatSlice';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

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
    } else {
      // Always load the session when navigating to a specific session ID
      // Don't check if it's the same - just load it to ensure we have the latest data
      console.log('[ChatContainer] Loading session:', sessionId);
      dispatch(loadSession(sessionId));
    }
  }, [sessionId, dispatch]); // Dependencies

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