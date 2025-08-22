import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { loadChatHistory } from '../../store/chatSlice';
import { format } from 'date-fns';

const ChatList = styled('div', {
  padding: '0 8px',
});

const ChatItem = styled(Button, {
  width: '100%',
  marginBottom: '4px',
  justifyContent: 'flex-start',
  textAlign: 'left',
});

const ChatTitle = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '14px',
  fontWeight: 500,
  color: $isDarkMode ? '#f3f4f6' : '#111827',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
}));

const ChatDate = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '12px',
  color: $isDarkMode ? '#9ca3af' : '#6b7280',
  marginTop: '2px',
}));

const EmptyState = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '16px',
  fontSize: '14px',
  color: $isDarkMode ? '#9ca3af' : '#6b7280',
  textAlign: 'center',
}));

interface RecentChatsProps {
  isCompact?: boolean;
}

const RecentChats: React.FC<RecentChatsProps> = ({ isCompact = false }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { sessions, currentSessionId } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector(
    (state: RootState) => state.settings
  );

  useEffect(() => {
    dispatch(loadChatHistory());
  }, [dispatch]);

  const handleChatClick = (sessionId: string) => {
    navigate(`/chat/${sessionId}`);
  };

  if (isCompact) {
    return (
      <ChatList>
        {sessions.slice(0, 5).map((session) => (
          <Button
            key={session.id}
            onClick={() => handleChatClick(session.id)}
            kind={KIND.tertiary}
            size={SIZE.mini}
            shape="circle"
            overrides={{
              BaseButton: {
                style: {
                  width: '40px',
                  height: '40px',
                  marginBottom: '4px',
                  backgroundColor:
                    session.id === currentSessionId ? (isDarkMode ? '#374151' : '#e5e7eb') : 'transparent',
                  ':hover': {
                    backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                  },
                },
              },
            }}
          >
            💬
          </Button>
        ))}
      </ChatList>
    );
  }

  if (sessions.length === 0) {
    return <EmptyState $isDarkMode={isDarkMode}>No recent chats</EmptyState>;
  }

  return (
    <ChatList>
      {sessions.slice(0, 10).map((session) => (
        <ChatItem
          key={session.id}
          onClick={() => handleChatClick(session.id)}
          kind={KIND.tertiary}
          size={SIZE.compact}
          overrides={{
            BaseButton: {
              style: {
                backgroundColor:
                  session.id === currentSessionId ? (isDarkMode ? '#374151' : '#e5e7eb') : 'transparent',
                color: isDarkMode ? '#f3f4f6' : '#111827',
                paddingLeft: '12px',
                justifyContent: 'flex-start',
                ':hover': {
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                },
              },
            },
          }}
        >
          <div style={{ width: '100%' }}>
            <ChatTitle $isDarkMode={isDarkMode}>{session.title || 'Untitled Chat'}</ChatTitle>
            <ChatDate $isDarkMode={isDarkMode}>
              {format(new Date(session.updated_at), 'MMM d, h:mm a')}
            </ChatDate>
          </div>
        </ChatItem>
      ))}
    </ChatList>
  );
};

export default RecentChats;