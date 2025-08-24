import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE, SHAPE } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { toggleSidebar, setActiveSection } from '../../store/sidebarSlice';
import { clearMessages } from '../../store/chatSlice';
import { logout } from '../../store/authSlice';
import RecentChats from './RecentChats';
import ToolsMenu from './ToolsMenu';

const SidebarContainer = styled('aside', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  position: 'fixed',
  top: 0,
  left: 0,
  height: '100vh',
  width: $isOpen ? '260px' : '60px',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#f7f8fa',
  color: $isDarkMode ? '#e5e7eb' : '#1a1a1a',
  transition: 'width 0.3s ease, background-color 0.3s ease',
  zIndex: 1000,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  borderRight: $isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
}));

const Header = styled('div', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  padding: '20px 16px',
  borderBottom: $isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
  display: 'flex',
  alignItems: 'center',
  justifyContent: $isOpen ? 'space-between' : 'center',
  backgroundColor: $isDarkMode ? '#111827' : '#ffffff',
}));

const Logo = styled('div', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  fontSize: '18px',
  fontWeight: '600',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const LogoImage = styled('img', {
  width: '36px',
  height: '36px',
  objectFit: 'contain',
});

const LogoText = styled('span', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  display: $isOpen ? 'block' : 'none',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
  fontWeight: '600',
}));

const Content = styled('div', {
  flex: 1,
  overflowY: 'auto',
  overflowX: 'hidden',
  padding: '8px',
});

const Footer = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  padding: '16px',
  borderTop: $isDarkMode ? '1px solid #374151' : '1px solid #e5e7eb',
  backgroundColor: $isDarkMode ? '#111827' : '#ffffff',
}));

const NavSection = styled('div', {
  marginBottom: '8px',
});

const NavButton = styled(Button, {
  width: '100%',
  justifyContent: 'flex-start',
  marginBottom: '4px',
});

const SectionTitle = styled('h3', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  fontSize: '12px',
  fontWeight: 700,
  textTransform: 'uppercase',
  color: $isDarkMode ? '#9ca3af' : '#111827',
  padding: '8px 12px',
  marginBottom: '4px',
  display: $isOpen ? 'block' : 'none',
  letterSpacing: '0.5px',
}));

const UserInfo = styled('div', ({ $isOpen, $isDarkMode }: { $isOpen: boolean; $isDarkMode: boolean }) => ({
  display: $isOpen ? 'flex' : 'none',
  alignItems: 'center',
  gap: '12px',
  marginBottom: '12px',
  padding: '12px',
  backgroundColor: $isDarkMode ? '#1f2937' : '#f7f8fa',
  borderRadius: '8px',
}));

const UserAvatar = styled('img', {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
});

const UserName = styled('div', ({ $isDarkMode }: { $isDarkMode: boolean }) => ({
  fontSize: '14px',
  fontWeight: '500',
  color: $isDarkMode ? '#f3f4f6' : '#111827',
}));

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const { isOpen, activeSection } = useSelector(
    (state: RootState) => state.sidebar
  );
  const { user } = useSelector((state: RootState) => state.auth);
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  const handleNewChat = async () => {
    // Clear current messages and session
    dispatch(clearMessages());
    // Navigate to chat without session ID to indicate new chat
    navigate('/chat/new');
    // The actual session will be created when the first message is sent
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
  };

  const handleToggle = () => {
    dispatch(toggleSidebar());
  };

  return (
    <SidebarContainer $isOpen={isOpen}>
      <Header $isOpen={isOpen}>
        <Logo $isOpen={isOpen}>
          <LogoImage src="/greywolf_logo.png" alt="Greywolf" />
          <LogoText $isOpen={isOpen}>Greywolf Analytica</LogoText>
        </Logo>
        <Button
          onClick={handleToggle}
          kind={KIND.tertiary}
          size={SIZE.mini}
          shape={SHAPE.circle}
          overrides={{
            BaseButton: {
              style: {
                color: isDarkMode ? '#9ca3af' : '#6b7280',
                backgroundColor: 'transparent',
                ':hover': {
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                },
              },
            },
          }}
        >
          {isOpen ? '←' : '→'}
        </Button>
      </Header>

      <Content>
        <NavSection>
          <NavButton
            onClick={handleNewChat}
            kind={KIND.primary}
            size={SIZE.compact}
            overrides={{
              BaseButton: {
                style: {
                  backgroundColor: '#3b82f6',
                  color: '#ffffff',
                  borderRadius: '8px',
                  padding: '10px 16px',
                  fontWeight: '500',
                  fontSize: '14px',
                  width: '100%',
                  justifyContent: 'center',
                  ':hover': {
                    backgroundColor: '#2563eb',
                  },
                },
              },
            }}
          >
            {isOpen ? '+ New Chat' : '+'}
          </NavButton>
        </NavSection>

        <NavSection>
          <SectionTitle $isOpen={isOpen}>Recent Chats</SectionTitle>
          <RecentChats isCompact={!isOpen} />
        </NavSection>

        <NavSection>
          <SectionTitle $isOpen={isOpen}>Tools</SectionTitle>
          <ToolsMenu isCompact={!isOpen} />
        </NavSection>
      </Content>

      <Footer>
        {user && (
          <UserInfo $isOpen={isOpen}>
            {user.picture && <UserAvatar src={user.picture} alt={user.name} />}
            <div style={{ flex: 1 }}>
              <UserName>{user.name}</UserName>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>{user.email}</div>
            </div>
          </UserInfo>
        )}
        <Button
          onClick={handleLogout}
          kind={KIND.tertiary}
          size={SIZE.compact}
          overrides={{
            BaseButton: {
              style: {
                width: '100%',
                color: isDarkMode ? '#9ca3af' : '#6b7280',
                justifyContent: isOpen ? 'flex-start' : 'center',
                fontSize: '14px',
                fontWeight: '400',
                ':hover': {
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                  color: '#ef4444',
                },
              },
            },
          }}
        >
          {isOpen ? 'Sign Out' : '↩'}
        </Button>
      </Footer>
    </SidebarContainer>
  );
};

export default Sidebar;