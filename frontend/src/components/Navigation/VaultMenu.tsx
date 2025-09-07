import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { RootState } from '../../store';

const MenuContainer = styled('div', {
  padding: '0 8px',
});

const MenuItem = styled(Button, {
  width: '100%',
  marginBottom: '4px',
  justifyContent: 'flex-start',
  textAlign: 'left',
});

const MenuIcon = styled('span', {
  marginRight: '8px',
  fontSize: '16px',
});

const MenuLabel = styled('span', {
  fontSize: '14px',
});

interface VaultMenuProps {
  isCompact?: boolean;
}

const VaultMenu: React.FC<VaultMenuProps> = ({ isCompact = false }) => {
  const navigate = useNavigate();
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  const vaultItems = [
    { id: 'documents', icon: '📄', label: 'Documents', path: '/documents' },
    { id: 'images', icon: '🖼️', label: 'Images', path: '/images' },
    { id: 'videos', icon: '🎥', label: 'Videos', path: '/videos' },
  ];

  const handleItemClick = (path: string) => {
    navigate(path);
  };

  if (isCompact) {
    return (
      <MenuContainer>
        {vaultItems.map((item) => (
          <Button
            key={item.id}
            onClick={() => handleItemClick(item.path)}
            kind={KIND.tertiary}
            size={SIZE.mini}
            shape="circle"
            overrides={{
              BaseButton: {
                style: {
                  width: '40px',
                  height: '40px',
                  marginBottom: '4px',
                  ':hover': {
                    backgroundColor: isDarkMode ? '#374151' : '#e5e7eb',
                  },
                },
              },
            }}
          >
            {item.icon}
          </Button>
        ))}
      </MenuContainer>
    );
  }

  return (
    <MenuContainer>
      {vaultItems.map((item) => (
        <MenuItem
          key={item.id}
          onClick={() => handleItemClick(item.path)}
          kind={KIND.tertiary}
          size={SIZE.compact}
          overrides={{
            BaseButton: {
              style: {
                color: isDarkMode ? '#f3f4f6' : '#111827',
                fontWeight: '400',
                justifyContent: 'flex-start',
                paddingLeft: '12px',
                ':hover': {
                  backgroundColor: isDarkMode ? '#374151' : '#f3f4f6',
                },
              },
            },
          }}
        >
          <MenuIcon>{item.icon}</MenuIcon>
          <MenuLabel>{item.label}</MenuLabel>
        </MenuItem>
      ))}
    </MenuContainer>
  );
};

export default VaultMenu;