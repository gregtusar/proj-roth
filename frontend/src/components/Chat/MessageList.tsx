import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { styled } from 'baseui';
import { RootState } from '../../store';
import Message from './Message';
import { Spinner } from 'baseui/spinner';

const Container = styled<'div', { $isDarkMode?: boolean }>('div', ({ $isDarkMode }) => ({
  flex: 1,
  overflowY: 'auto',
  padding: '24px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
  backgroundColor: $isDarkMode ? '#111827' : '#ffffff',
  transition: 'background-color 0.3s ease',
}));

const LoadingContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  padding: '20px',
});

const EmptyState = styled<'div', { $isDarkMode: boolean }>('div', ({ $isDarkMode }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  flex: 1,
  color: $isDarkMode ? '#a0a0a0' : '#666',
  textAlign: 'center',
  padding: '40px',
  transition: 'color 0.3s ease',
}));

const EmptyStateIcon = styled('div', {
  fontSize: '48px',
  marginBottom: '16px',
});

const EmptyStateText = styled<'p', { $isDarkMode: boolean }>('p', ({ $isDarkMode }) => ({
  fontSize: '16px',
  color: $isDarkMode ? '#e0e0e0' : '#374151',
  transition: 'color 0.3s ease',
  marginBottom: '8px',
}));

const EmptyStateHint = styled<'p', { $isDarkMode: boolean }>('p', ({ $isDarkMode }) => ({
  fontSize: '14px',
  color: $isDarkMode ? '#808080' : '#999',
  transition: 'color 0.3s ease',
}));

const MessageList: React.FC = () => {
  const { messages, isLoading, streamingMessage, currentSessionId } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages, streamingMessage]);

  if (messages.length === 0 && !isLoading) {
    return (
      <Container $isDarkMode={isDarkMode}>
        <EmptyState $isDarkMode={isDarkMode}>
          <EmptyStateIcon>💬</EmptyStateIcon>
          <EmptyStateText $isDarkMode={isDarkMode}>Start a conversation</EmptyStateText>
          <EmptyStateHint $isDarkMode={isDarkMode}>
            Ask me about voter data, demographics, or political information in NJ District 07
          </EmptyStateHint>
        </EmptyState>
      </Container>
    );
  }

  return (
    <Container ref={containerRef} $isDarkMode={isDarkMode}>
      {messages.map((message) => (
        <Message key={message.message_id} message={message} />
      ))}
      
      {streamingMessage !== null && (
        <Message
          message={{
            message_id: 'streaming',
            session_id: currentSessionId || 'temp-session',
            user_id: 'assistant',
            message_type: 'assistant',
            message_text: streamingMessage,
            timestamp: new Date().toISOString(),
            sequence_number: messages.length,
          }}
          isStreaming
        />
      )}
      
      {isLoading && !streamingMessage && (
        <LoadingContainer>
          <Spinner $size={32} />
        </LoadingContainer>
      )}
    </Container>
  );
};

export default MessageList;