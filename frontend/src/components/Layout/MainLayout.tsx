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

const MainContent = styled('main', ({ $sidebarOpen }: { $sidebarOpen: boolean }) => ({
  flex: 1,
  marginLeft: $sidebarOpen ? '280px' : '60px',
  transition: 'margin-left 0.3s ease',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const MainLayout: React.FC = () => {
  const { isOpen } = useSelector((state: RootState) => state.sidebar);

  return (
    <LayoutContainer>
      <Sidebar />
      <MainContent $sidebarOpen={isOpen}>
        <Outlet />
      </MainContent>
    </LayoutContainer>
  );
};

export default MainLayout;