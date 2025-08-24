import React, { useState, useRef, KeyboardEvent } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Textarea, SIZE } from 'baseui/textarea';
import { Button, KIND, SIZE as ButtonSize } from 'baseui/button';
import { RootState, AppDispatch, store } from '../../store';
import { addMessage } from '../../store/chatSlice';
import wsService from '../../services/websocket';
import { Message } from '../../types/chat';

const Container = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '16px 24px',
  borderTop: $isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
  backgroundColor: $isDarkMode ? '#1f2937' : '#ffffff',
  transition: 'background-color 0.3s ease, border-color 0.3s ease',
}));

const InputContainer = styled('div', {
  display: 'flex',
  gap: '12px',
  alignItems: 'center', // Center align the send button with input
});

const StyledTextarea = styled(Textarea, {
  flex: 1,
});

const CharCount = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '12px',
  color: $isDarkMode ? '#a0a0a0' : '#666',
  marginTop: '4px',
  textAlign: 'right',
  transition: 'color 0.3s ease',
}));

const MessageInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch<AppDispatch>();
  const { messages, isLoading, currentSessionId } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() || isLoading) return;

    // Don't add message to store yet - wait for backend confirmation
    // This ensures we have the correct session_id
    const messageText = message.trim();
    
    // Send message through WebSocket
    // Backend will create session if needed and return proper session_id
    wsService.sendMessage(messageText, currentSessionId || undefined);
    
    // Add user message to store with temporary ID
    // It will be replaced when we get the real message from backend
    const tempMessage: Message = {
      message_id: `temp-${Date.now()}`,
      session_id: currentSessionId || 'pending',
      user_id: store.getState().auth.user?.id || 'current_user',
      message_type: 'user',
      message_text: messageText,
      timestamp: new Date().toISOString(),
      sequence_number: messages.length,
    };
    dispatch(addMessage(tempMessage));
    
    setMessage('');
    // Focus will be handled by the inputRef prop
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const maxLength = 4000;
  const remainingChars = maxLength - message.length;

  return (
    <Container $isDarkMode={isDarkMode}>
      <InputContainer>
        <StyledTextarea
          inputRef={inputRef}
          value={message}
          onChange={(e) => setMessage((e.target as HTMLTextAreaElement).value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about voter data, demographics, or political information..."
          size={SIZE.large}
          disabled={isLoading}
          autoFocus
          rows={2}
          maxRows={6}
          resize="vertical"
          overrides={{
            Root: {
              style: {
                flex: 1,
              },
            },
            Input: {
              style: {
                minHeight: '56px',
                maxHeight: '150px',
                resize: 'none',
                overflowY: 'auto',
              },
            },
          }}
        />
        <Button
          onClick={handleSend}
          disabled={!message.trim() || isLoading}
          kind={KIND.primary}
          size={ButtonSize.large}
          isLoading={isLoading}
          overrides={{
            BaseButton: {
              style: {
                height: '40px', // Match input height
              },
            },
          }}
        >
          Send
        </Button>
      </InputContainer>
      {message.length > 0 && (
        <CharCount
          $isDarkMode={isDarkMode}
          style={{
            color: remainingChars < 100 ? '#ff0000' : isDarkMode ? '#a0a0a0' : '#666',
          }}
        >
          {remainingChars} characters remaining
        </CharCount>
      )}
    </Container>
  );
};

export default MessageInput;