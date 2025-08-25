import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { loadChatSessions, deleteSessionAsync, renameSession } from '../../store/chatSlice';
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
  maxWidth: 'calc(100% - 40px)', // Leave space for menu button
  paddingRight: '8px',
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

const ChatItemContainer = styled('div', {
  display: 'flex',
  alignItems: 'center',
  width: '100%',
  gap: '4px',
});

const EditableTitle = styled('input', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '14px',
  fontWeight: 500,
  color: $isDarkMode ? '#f3f4f6' : '#111827',
  backgroundColor: 'transparent',
  border: 'none',
  outline: 'none',
  width: '100%',
  padding: '2px 4px',
  borderRadius: '4px',
  ':focus': {
    backgroundColor: $isDarkMode ? '#374151' : '#f3f4f6',
  },
}));

interface RecentChatsProps {
  isCompact?: boolean;
}

const RecentChats: React.FC<RecentChatsProps> = ({ isCompact = false }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch<AppDispatch>();
  const { sessions, currentSessionId, error } = useSelector(
    (state: RootState) => state.chat
  );
  const { isDarkMode } = useSelector(
    (state: RootState) => state.settings
  );
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');
  const [openPopoverId, setOpenPopoverId] = useState<string | null>(null);

  useEffect(() => {
    dispatch(loadChatSessions());
  }, [dispatch]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openPopoverId) {
        const target = event.target as HTMLElement;
        // Check if click is outside the menu
        if (!target.closest('[data-menu-container]')) {
          setOpenPopoverId(null);
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openPopoverId]);

  const handleChatClick = (sessionId: string) => {
    console.log('[RecentChats] handleChatClick called with sessionId:', sessionId);
    console.log('[RecentChats] Navigating to:', `/chat/${sessionId}`);
    navigate(`/chat/${sessionId}`);
    console.log('[RecentChats] Navigation called');
  };

  const handleDelete = (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
      dispatch(deleteSessionAsync(sessionId));
    }
  };

  const handleRename = (sessionId: string, currentName: string) => {
    setEditingSessionId(sessionId);
    setEditingName(currentName);
  };

  const handleSaveRename = () => {
    if (editingSessionId && editingName.trim()) {
      dispatch(renameSession({ sessionId: editingSessionId, sessionName: editingName }));
    }
    setEditingSessionId(null);
    setEditingName('');
  };

  if (isCompact) {
    return (
      <ChatList>
        {sessions.slice(0, 5).map((session) => (
          <Button
            key={session.session_id}
            onClick={() => handleChatClick(session.session_id)}
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
                    session.session_id === currentSessionId ? (isDarkMode ? '#374151' : '#e5e7eb') : 'transparent',
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

  if (error) {
    return <EmptyState $isDarkMode={isDarkMode}>Error loading chats: {error}</EmptyState>;
  }

  if (sessions.length === 0) {
    return <EmptyState $isDarkMode={isDarkMode}>No recent chats</EmptyState>;
  }

  return (
    <ChatList>
      {sessions.slice(0, 10).map((session) => (
        <div key={session.session_id} style={{ position: 'relative' }}>
          <ChatItem
            onClick={(e) => {
              console.log('[ChatItem] onClick fired, event target:', e.target);
              // Don't navigate if clicking on the menu button (check for data-menu-button attribute)
              const target = e.target as HTMLElement;
              console.log('[ChatItem] Checking if target is menu button');
              if (!target.closest('[data-menu-button]')) {
                console.log('[ChatItem] Not a menu button, calling handleChatClick');
                handleChatClick(session.session_id);
              } else {
                console.log('[ChatItem] Target is menu button, not navigating');
              }
            }}
            kind={KIND.tertiary}
            size={SIZE.compact}
            overrides={{
              BaseButton: {
                style: {
                  backgroundColor:
                    session.session_id === currentSessionId ? (isDarkMode ? '#374151' : '#e5e7eb') : 'transparent',
                  color: isDarkMode ? '#f3f4f6' : '#111827',
                  paddingLeft: '12px',
                  paddingRight: '50px', // More space for menu button
                  justifyContent: 'flex-start',
                  ':hover': {
                    backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                  },
                },
              },
            }}
          >
            <ChatItemContainer>
              <div style={{ flex: 1 }}>
                {editingSessionId === session.session_id ? (
                  <EditableTitle
                    $isDarkMode={isDarkMode}
                    value={editingName}
                    onChange={(e) => setEditingName(e.target.value)}
                    onBlur={handleSaveRename}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSaveRename();
                      }
                    }}
                    onClick={(e) => e.stopPropagation()}
                    autoFocus
                  />
                ) : (
                  <ChatTitle $isDarkMode={isDarkMode}>{session.session_name || 'Untitled Chat'}</ChatTitle>
                )}
                <ChatDate $isDarkMode={isDarkMode}>
                  {format(new Date(session.updated_at), 'MMM d, h:mm a')}
                </ChatDate>
              </div>
            </ChatItemContainer>
          </ChatItem>
          <div style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)' }}>
            <div style={{ position: 'relative' }} data-menu-container>
              <Button
                data-menu-button
                kind={KIND.tertiary}
                size={SIZE.mini}
                overrides={{
                  BaseButton: {
                    style: {
                      minWidth: '24px',
                      height: '24px',
                      padding: '0',
                      color: isDarkMode ? '#e5e7eb' : '#374151',
                      backgroundColor: isDarkMode ? 'rgba(55, 65, 81, 0.3)' : 'rgba(243, 244, 246, 0.7)',
                      ':hover': {
                        backgroundColor: isDarkMode ? '#4b5563' : '#e5e7eb',
                        color: isDarkMode ? '#ffffff' : '#111827',
                      },
                    },
                  },
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  console.log('Three dot menu clicked for session:', session.session_id);
                  // Toggle the popover for this session
                  setOpenPopoverId(openPopoverId === session.session_id ? null : session.session_id);
                }}
              >
                ⋮
              </Button>
              {openPopoverId === session.session_id && (
                <div
                  style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: '4px',
                    backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                    minWidth: '120px',
                    zIndex: 10000,
                    overflow: 'hidden',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <div
                    style={{
                      padding: '8px 12px',
                      cursor: 'pointer',
                      color: isDarkMode ? '#e5e7eb' : '#111827',
                      backgroundColor: 'transparent',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = isDarkMode ? '#374151' : '#f3f4f6';
                      e.currentTarget.style.color = isDarkMode ? '#ffffff' : '#111827';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = isDarkMode ? '#e5e7eb' : '#111827';
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRename(session.session_id, session.session_name);
                      setOpenPopoverId(null);
                    }}
                  >
                    Rename
                  </div>
                  <div
                    style={{
                      padding: '8px 12px',
                      cursor: 'pointer',
                      color: '#dc2626',
                      fontWeight: 600,
                      backgroundColor: 'transparent',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(220, 38, 38, 0.1)';
                      e.currentTarget.style.color = '#ef4444';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent';
                      e.currentTarget.style.color = '#dc2626';
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(session.session_id);
                      setOpenPopoverId(null);
                    }}
                  >
                    Delete
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </ChatList>
  );
};

export default RecentChats;
