import React from 'react';
import { useNavigate } from 'react-router-dom';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';

const MenuContainer = styled('div', {
  padding: '0 8px',
});

const MenuItem = styled(Button, {
  width: '100%',
  marginBottom: '4px',
  justifyContent: 'flex-start',
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

  const tools = [
    { id: 'lists', icon: '📋', label: 'List Manager', path: '/lists' },
    { id: 'query', icon: '🔍', label: 'Query Builder', path: '/query' },
    { id: 'export', icon: '📥', label: 'Export Data', path: '/export' },
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
                    backgroundColor: '#333',
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
                color: '#ccc',
                ':hover': {
                  backgroundColor: '#2a2a2a',
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