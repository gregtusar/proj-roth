import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { styled } from 'baseui';
import { RootState } from '../../store';
import Message from './Message';
import { Spinner } from 'baseui/spinner';

const Container = styled('div', {
  flex: 1,
  overflowY: 'auto',
  padding: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
});

const LoadingContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  padding: '20px',
});

const EmptyState = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flex: 1,
  color: '#666',
  textAlign: 'center',
  padding: '40px',
});

const EmptyStateIcon = styled('div', {
  fontSize: '48px',
  marginBottom: '16px',
});

const EmptyStateText = styled('p', {
  fontSize: '16px',
  marginBottom: '8px',
});

const EmptyStateHint = styled('p', {
  fontSize: '14px',
  color: '#999',
});

const MessageList: React.FC = () => {
  const { messages, isLoading, streamingMessage } = useSelector(
    (state: RootState) => state.chat
  );
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, streamingMessage]);

  if (messages.length === 0 && !isLoading) {
    return (
      <Container>
        <EmptyState>
          <EmptyStateIcon>💬</EmptyStateIcon>
          <EmptyStateText>Start a conversation</EmptyStateText>
          <EmptyStateHint>
            Ask me about voter data, demographics, or political information in NJ District 07
          </EmptyStateHint>
        </EmptyState>
      </Container>
    );
  }

  return (
    <Container ref={containerRef}>
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
      
      {streamingMessage !== null && (
        <Message
          message={{
            id: 'streaming',
            role: 'assistant',
            content: streamingMessage,
            timestamp: new Date().toISOString(),
          }}
          isStreaming
        />
      )}
      
      {isLoading && !streamingMessage && (
        <LoadingContainer>
          <Spinner size={32} />
        </LoadingContainer>
      )}
    </Container>
  );
};

export default MessageList;