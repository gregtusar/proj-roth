import React, { useState } from 'react';
import { styled } from 'baseui';
import { Avatar } from 'baseui/avatar';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message as MessageType } from '../../types/chat';
import { Tag, KIND as TagKind } from 'baseui/tag';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

const MessageContainer = styled('div', ({ $role, $isDarkMode }: { $role: string; $isDarkMode: boolean }) => ({
  display: 'flex',
  gap: '12px',
  padding: '12px',
  backgroundColor: $isDarkMode 
    ? ($role === 'user' ? '#2d2d2d' : '#262626')
    : ($role === 'user' ? '#f8f9fa' : '#ffffff'),
  borderRadius: '8px',
  border: $isDarkMode ? '1px solid #404040' : '1px solid #e0e0e0',
  transition: 'background-color 0.3s ease, border-color 0.3s ease',
}));

const MessageContent = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  flex: 1,
  fontSize: '14px',
  lineHeight: '1.6',
  color: $isDarkMode ? '#e0e0e0' : '#111827',
  '& p': {
    margin: '0 0 8px 0',
  },
  '& p:last-child': {
    margin: 0,
  },
  '& ul, & ol': {
    marginLeft: '20px',
    marginBottom: '8px',
  },
  '& pre': {
    margin: '8px 0',
  },
  '& code': {
    backgroundColor: $isDarkMode ? '#404040' : '#f0f0f0',
    padding: '2px 4px',
    borderRadius: '3px',
    fontSize: '13px',
  },
  transition: 'color 0.3s ease',
}));

const ToolCallContainer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  marginTop: '8px',
  padding: '8px',
  backgroundColor: $isDarkMode ? '#404040' : '#f5f5f5',
  borderRadius: '4px',
  fontSize: '12px',
  color: $isDarkMode ? '#a0a0a0' : '#666',
  transition: 'background-color 0.3s ease, color 0.3s ease',
}));

const StreamingIndicator = styled('span', {
  display: 'inline-block',
  width: '8px',
  height: '8px',
  backgroundColor: '#0066cc',
  borderRadius: '50%',
  marginLeft: '4px',
  animation: 'pulse 1.5s infinite',
  '@keyframes pulse': {
    '0%': { opacity: 1 },
    '50%': { opacity: 0.3 },
    '100%': { opacity: 1 },
  },
});

const CopyButton = styled('button', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  padding: '4px 8px',
  marginTop: '8px',
  backgroundColor: 'transparent',
  border: `1px solid ${$isDarkMode ? '#404040' : '#e0e0e0'}`,
  borderRadius: '4px',
  color: $isDarkMode ? '#a0a0a0' : '#666',
  fontSize: '12px',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  ':hover': {
    backgroundColor: $isDarkMode ? '#404040' : '#f0f0f0',
    borderColor: $isDarkMode ? '#606060' : '#d0d0d0',
  },
  ':active': {
    transform: 'scale(0.95)',
  },
}));

const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const CheckIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isStreaming = false }) => {
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const { user } = useSelector((state: RootState) => state.auth);
  const isUser = message.message_type === 'user';
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.message_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };
  
  // Get user initials from email or name
  const getUserInitials = () => {
    if (user?.name) {
      const parts = user.name.split(' ');
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return user.name[0].toUpperCase();
    }
    if (user?.email) {
      const parts = user.email.split('@')[0].split('.');
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return user.email[0].toUpperCase();
    }
    return 'U';
  };
  
  // Use Google profile picture for user if available, otherwise undefined (will show initials)
  const avatarSrc = isUser ? user?.picture : '/greywolf_logo.png';
  const avatarName = isUser ? getUserInitials() : 'Greywolf';

  return (
    <MessageContainer $role={message.message_type} $isDarkMode={isDarkMode}>
      <Avatar
        name={avatarName}
        size="32px"
        src={avatarSrc}
        overrides={{
          Root: {
            style: {
              backgroundColor: isUser && !user?.picture ? '#0066cc' : '#f3f4f6',
            },
          },
          Avatar: {
            style: {
              objectFit: 'cover',
            },
          },
        }}
      />
      <MessageContent $isDarkMode={isDarkMode}>
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {message.message_text}
        </ReactMarkdown>
        
        {isStreaming && <StreamingIndicator />}
        
        {message.metadata?.tool_calls && (
          <ToolCallContainer $isDarkMode={isDarkMode}>
            {message.metadata.tool_calls.map((call, index) => (
              <Tag
                key={index}
                kind={TagKind.neutral}
                closeable={false}
                overrides={{
                  Root: {
                    style: {
                      marginRight: '4px',
                      marginBottom: '4px',
                    },
                  },
                }}
              >
                {call.tool}
              </Tag>
            ))}
          </ToolCallContainer>
        )}
        
        {message.metadata?.results_count !== undefined && (
          <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
            Found {message.metadata.results_count} results
          </div>
        )}
        
        {!isUser && !isStreaming && (
          <CopyButton
            $isDarkMode={isDarkMode}
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy to clipboard'}
          >
            {copied ? <CheckIcon /> : <CopyIcon />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </CopyButton>
        )}
      </MessageContent>
    </MessageContainer>
  );
};

export default Message;