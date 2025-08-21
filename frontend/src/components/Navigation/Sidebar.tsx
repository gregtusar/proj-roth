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
import ProjectTree from './ProjectTree';
import ToolsMenu from './ToolsMenu';

const SidebarContainer = styled('aside', ({ $isOpen }: { $isOpen: boolean }) => ({
  position: 'fixed',
  top: 0,
  left: 0,
  height: '100vh',
  width: $isOpen ? '280px' : '60px',
  backgroundColor: '#1a1a1a',
  color: '#ffffff',
  transition: 'width 0.3s ease',
  zIndex: 1000,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const Header = styled('div', ({ $isOpen }: { $isOpen: boolean }) => ({
  padding: '16px',
  borderBottom: '1px solid #333',
  display: 'flex',
  alignItems: 'center',
  justifyContent: $isOpen ? 'space-between' : 'center',
}));

const Logo = styled('div', ({ $isOpen }: { $isOpen: boolean }) => ({
  fontSize: '24px',
  fontWeight: 'bold',
  display: $isOpen ? 'flex' : 'none',
  alignItems: 'center',
  gap: '8px',
}));

const Content = styled('div', {
  flex: 1,
  overflowY: 'auto',
  overflowX: 'hidden',
  padding: '16px 0',
});

const Footer = styled('div', {
  padding: '16px',
  borderTop: '1px solid #333',
});

const NavSection = styled('div', {
  marginBottom: '24px',
});

const NavButton = styled(Button, {
  width: '100%',
  justifyContent: 'flex-start',
  marginBottom: '4px',
});

const SectionTitle = styled('h3', ({ $isOpen }: { $isOpen: boolean }) => ({
  fontSize: '12px',
  fontWeight: 600,
  textTransform: 'uppercase',
  color: '#888',
  padding: '0 16px',
  marginBottom: '8px',
  display: $isOpen ? 'block' : 'none',
}));

const UserInfo = styled('div', ({ $isOpen }: { $isOpen: boolean }) => ({
  display: $isOpen ? 'flex' : 'none',
  alignItems: 'center',
  gap: '8px',
  marginBottom: '8px',
  padding: '8px',
  backgroundColor: '#2a2a2a',
  borderRadius: '4px',
}));

const UserAvatar = styled('img', {
  width: '32px',
  height: '32px',
  borderRadius: '50%',
});

const UserName = styled('div', {
  fontSize: '14px',
  color: '#ccc',
});

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch<AppDispatch>();
  const { isOpen, activeSection } = useSelector(
    (state: RootState) => state.sidebar
  );
  const { user } = useSelector((state: RootState) => state.auth);

  const handleNewChat = () => {
    dispatch(clearMessages());
    navigate('/chat');
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
          <span>🗳️</span>
          <span>NJ Voter Chat</span>
        </Logo>
        <Button
          onClick={handleToggle}
          kind={KIND.tertiary}
          size={SIZE.mini}
          shape={SHAPE.circle}
          overrides={{
            BaseButton: {
              style: {
                color: '#fff',
                ':hover': {
                  backgroundColor: '#333',
                },
              },
            },
          }}
        >
          {isOpen ? '◀' : '▶'}
        </Button>
      </Header>

      <Content>
        <NavSection>
          <NavButton
            onClick={handleNewChat}
            kind={KIND.secondary}
            size={SIZE.compact}
            overrides={{
              BaseButton: {
                style: {
                  backgroundColor: '#0066cc',
                  color: '#fff',
                  ':hover': {
                    backgroundColor: '#0052a3',
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
          <SectionTitle $isOpen={isOpen}>Projects</SectionTitle>
          <ProjectTree isCompact={!isOpen} />
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
              <div style={{ fontSize: '12px', color: '#888' }}>{user.email}</div>
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
                color: '#ff4444',
                justifyContent: isOpen ? 'flex-start' : 'center',
                ':hover': {
                  backgroundColor: '#2a2a2a',
                },
              },
            },
          }}
        >
          {isOpen ? 'Sign Out' : '⎋'}
        </Button>
      </Footer>
    </SidebarContainer>
  );
};

export default Sidebar;