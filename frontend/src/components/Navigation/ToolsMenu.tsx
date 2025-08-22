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

interface ToolsMenuProps {
  isCompact?: boolean;
}

const ToolsMenu: React.FC<ToolsMenuProps> = ({ isCompact = false }) => {
  const navigate = useNavigate();
  const { isDarkMode } = useSelector((state: RootState) => state.settings);

  const tools = [
    { id: 'lists', icon: '📋', label: 'List Manager', path: '/lists' },
    { id: 'query', icon: '🔍', label: 'Query', path: '/query' },
    { id: 'videos', icon: '🎥', label: 'Video Assets', path: '/videos' },
    { id: 'campaign', icon: '📢', label: 'Campaign Manager', path: '/campaign' },
    { id: 'abtesting', icon: '🧪', label: 'A/B Testing Tool', path: '/ab-testing' },
    { id: 'streetmap', icon: '🗺️', label: 'Street Map', path: '/street-map' },
    { id: 'settings', icon: '⚙️', label: 'Settings', path: '/settings' },
  ];

  const handleToolClick = (path: string) => {
    navigate(path);
  };

  if (isCompact) {
    return (
      <MenuContainer>
        {tools.map((tool) => (
          <Button
            key={tool.id}
            onClick={() => handleToolClick(tool.path)}
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
            {tool.icon}
          </Button>
        ))}
      </MenuContainer>
    );
  }

  return (
    <MenuContainer>
      {tools.map((tool) => (
        <MenuItem
          key={tool.id}
          onClick={() => handleToolClick(tool.path)}
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
          <MenuIcon>{tool.icon}</MenuIcon>
          <MenuLabel>{tool.label}</MenuLabel>
        </MenuItem>
      ))}
    </MenuContainer>
  );
};

export default ToolsMenu;