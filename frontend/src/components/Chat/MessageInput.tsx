import React, { useState, useRef, KeyboardEvent } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Textarea, SIZE } from 'baseui/textarea';
import { Button, KIND, SIZE as ButtonSize } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { addMessage } from '../../store/chatSlice';
import wsService from '../../services/websocket';

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
  const { isLoading, currentSessionId } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };

    dispatch(addMessage(userMessage));
    wsService.sendMessage(message.trim(), currentSessionId || undefined);
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