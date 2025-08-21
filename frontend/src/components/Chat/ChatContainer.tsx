import React, { useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { RootState, AppDispatch } from '../../store';
import { loadSession } from '../../store/chatSlice';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const Container = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  width: '100%',
  backgroundColor: '#ffffff',
});

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId && sessionId !== currentSessionId) {
      dispatch(loadSession(sessionId));
    }
  }, [sessionId, currentSessionId, dispatch]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, []);

  return (
    <Container>
      <Header>
        <Title>NJ Voter Chat</Title>
      </Header>
      <ChatArea>
        <MessageList />
        <div ref={messagesEndRef} />
        <MessageInput />
      </ChatArea>
    </Container>
  );
};

export default ChatContainer;