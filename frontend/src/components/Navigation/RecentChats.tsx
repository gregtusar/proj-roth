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

const ChatTitle = styled('div', {
  fontSize: '14px',
  fontWeight: 500,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
});

const ChatDate = styled('div', {
  fontSize: '12px',
  color: '#888',
  marginTop: '2px',
});

const EmptyState = styled('div', {
  padding: '16px',
  fontSize: '14px',
  color: '#666',
  textAlign: 'center',
});

interface RecentChatsProps {
  isCompact?: boolean;
}

const RecentChats: React.FC<RecentChatsProps> = ({ isCompact = false }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { sessions, currentSessionId } = useSelector(
    (state: RootState) => state.chat
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
                    session.id === currentSessionId ? '#333' : 'transparent',
                  ':hover': {
                    backgroundColor: '#333',
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
    return <EmptyState>No recent chats</EmptyState>;
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
                  session.id === currentSessionId ? '#2a2a2a' : 'transparent',
                color: '#fff',
                ':hover': {
                  backgroundColor: '#333',
                },
              },
            },
          }}
        >
          <div style={{ width: '100%' }}>
            <ChatTitle>{session.title || 'Untitled Chat'}</ChatTitle>
            <ChatDate>
              {format(new Date(session.updated_at), 'MMM d, h:mm a')}
            </ChatDate>
          </div>
        </ChatItem>
      ))}
    </ChatList>
  );
};

export default RecentChats;