import React from 'react';
import { styled } from 'baseui';
import { Avatar } from 'baseui/avatar';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message as MessageType } from '../../types/chat';
import { Tag, KIND as TagKind } from 'baseui/tag';

const MessageContainer = styled('div', ({ $role }: { $role: string }) => ({
  display: 'flex',
  gap: '12px',
  padding: '12px',
  backgroundColor: $role === 'user' ? '#f8f9fa' : '#ffffff',
  borderRadius: '8px',
  border: '1px solid #e0e0e0',
}));

const MessageContent = styled('div', {
  flex: 1,
  fontSize: '14px',
  lineHeight: '1.6',
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
    backgroundColor: '#f0f0f0',
    padding: '2px 4px',
    borderRadius: '3px',
    fontSize: '13px',
  },
});

const ToolCallContainer = styled('div', {
  marginTop: '8px',
  padding: '8px',
  backgroundColor: '#f5f5f5',
  borderRadius: '4px',
  fontSize: '12px',
});

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
  const isUser = message.role === 'user';
  const avatarSrc = isUser ? undefined : undefined;
  const avatarName = isUser ? 'You' : 'Assistant';

  return (
    <MessageContainer $role={message.role}>
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
      <MessageContent>
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <SyntaxHighlighter
                  style={vscDarkPlus}
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
          <ToolCallContainer>
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