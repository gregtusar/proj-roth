import React from 'react';
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

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isStreaming = false }) => {
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const isUser = message.role === 'user';
  const avatarSrc = isUser ? undefined : undefined;
  const avatarName = isUser ? 'You' : 'Assistant';

  return (
    <MessageContainer $role={message.role} $isDarkMode={isDarkMode}>
      <Avatar
        name={avatarName}
        size="32px"
        src={avatarSrc}
        overrides={{
          Root: {
            style: {
              backgroundColor: isUser ? '#0066cc' : '#00aa00',
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
          {message.content}
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
      </MessageContent>
    </MessageContainer>
  );
};

export default Message;