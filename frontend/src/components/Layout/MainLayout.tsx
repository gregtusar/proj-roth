import React from 'react';
import { Outlet } from 'react-router-dom';
import { styled } from 'baseui';
import Sidebar from '../Navigation/Sidebar';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';

const LayoutContainer = styled('div', {
  display: 'flex',
  height: '100vh',
  width: '100vw',
  overflow: 'hidden',
});

const MainContent = styled('main', ({ $sidebarOpen, $isDarkMode }: { $sidebarOpen: boolean; $isDarkMode: boolean }) => ({
  flex: 1,
  marginLeft: $sidebarOpen ? '260px' : '60px',
  transition: 'margin-left 0.3s ease, background-color 0.3s ease',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  backgroundColor: $isDarkMode ? '#1a1a1a' : '#ffffff',
}));

const MainLayout: React.FC = () => {
  const { isOpen } = useSelector((state: RootState) => state.sidebar);
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  return (
    <LayoutContainer>
      <Sidebar />
      <MainContent $sidebarOpen={isOpen} $isDarkMode={isDarkMode}>
        <Outlet />
      </MainContent>
    </LayoutContainer>
  );
};

export default MainLayout;