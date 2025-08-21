import React, { useState, useRef, KeyboardEvent } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Input, SIZE } from 'baseui/input';
import { Button, KIND, SIZE as ButtonSize } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { addMessage } from '../../store/chatSlice';
import wsService from '../../services/websocket';

const Container = styled('div', {
  padding: '16px 24px',
  borderTop: '1px solid #e0e0e0',
  backgroundColor: '#ffffff',
});

const InputContainer = styled('div', {
  display: 'flex',
  gap: '12px',
  alignItems: 'flex-end',
});

const StyledInput = styled(Input, {
  flex: 1,
});

const CharCount = styled('div', {
  fontSize: '12px',
  color: '#666',
  marginTop: '4px',
  textAlign: 'right',
});

const MessageInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, currentSessionId } = useSelector(
    (state: RootState) => state.chat
  );
  const inputRef = useRef<HTMLInputElement>(null);

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
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const maxLength = 4000;
  const remainingChars = maxLength - message.length;

  return (
    <Container>
      <InputContainer>
        <StyledInput
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage((e.target as HTMLInputElement).value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about voter data, demographics, or political information..."
          size={SIZE.large}
          disabled={isLoading}
          overrides={{
            Root: {
              style: {
                flex: 1,
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
        >
          Send
        </Button>
      </InputContainer>
      {message.length > 0 && (
        <CharCount
          style={{
            color: remainingChars < 100 ? '#ff0000' : '#666',
          }}
        >
          {remainingChars} characters remaining
        </CharCount>
      )}
    </Container>
  );
};

export default MessageInput;