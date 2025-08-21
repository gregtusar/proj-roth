import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { RootState, AppDispatch } from '../../store';
import { toggleProjectExpanded } from '../../store/sidebarSlice';

const TreeContainer = styled('div', {
  padding: '0 8px',
});

const TreeNode = styled('div', {
  marginBottom: '2px',
});

const NodeButton = styled(Button, {
  width: '100%',
  justifyContent: 'flex-start',
  textAlign: 'left',
});

const NodeContent = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  width: '100%',
});

const NodeIcon = styled('span', {
  fontSize: '14px',
  width: '20px',
  textAlign: 'center',
});

const NodeLabel = styled('span', {
  fontSize: '14px',
  flex: 1,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
});

const ChildrenContainer = styled('div', {
  marginLeft: '20px',
});

interface ProjectTreeProps {
  isCompact?: boolean;
}

const ProjectTree: React.FC<ProjectTreeProps> = ({ isCompact = false }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { projects, expandedProjects } = useSelector(
    (state: RootState) => state.sidebar
  );

  // Default project structure
  const defaultProjects = [
    {
      id: 'nj-07',
      name: 'NJ District 07',
      icon: '📁',
      children: [
        { id: 'voters', name: 'Voter Data', icon: '👥' },
        { id: 'demographics', name: 'Demographics', icon: '📊' },
        { id: 'geocoding', name: 'Geocoding', icon: '📍' },
        { id: 'analysis', name: 'Analysis', icon: '📈' },
      ],
    },
    {
      id: 'tools',
      name: 'Tools',
      icon: '🛠️',
      children: [
        { id: 'bigquery', name: 'BigQuery', icon: '🗄️' },
        { id: 'maps', name: 'Google Maps', icon: '🗺️' },
        { id: 'search', name: 'Search', icon: '🔍' },
      ],
    },
  ];

  const projectsToShow = projects.length > 0 ? projects : defaultProjects;

  const handleToggle = (projectId: string) => {
    dispatch(toggleProjectExpanded(projectId));
  };

  const renderNode = (node: any, level: number = 0) => {
    const isExpanded = expandedProjects.includes(node.id);
    const hasChildren = node.children && node.children.length > 0;

    if (isCompact && level === 0) {
      return (
        <TreeNode key={node.id}>
          <Button
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
            {node.icon}
          </Button>
        </TreeNode>
      );
    }

    return (
      <TreeNode key={node.id}>
        <NodeButton
          onClick={() => hasChildren && handleToggle(node.id)}
          kind={KIND.tertiary}
          size={SIZE.compact}
          overrides={{
            BaseButton: {
              style: {
                color: '#ccc',
                paddingLeft: `${8 + level * 16}px`,
                ':hover': {
                  backgroundColor: '#2a2a2a',
                },
              },
            },
          }}
        >
          <NodeContent>
            {hasChildren && (
              <NodeIcon>{isExpanded ? '▼' : '▶'}</NodeIcon>
            )}
            <NodeIcon>{node.icon}</NodeIcon>
            <NodeLabel>{node.name}</NodeLabel>
          </NodeContent>
        </NodeButton>
        {hasChildren && isExpanded && !isCompact && (
          <ChildrenContainer>
            {node.children.map((child: any) => renderNode(child, level + 1))}
          </ChildrenContainer>
        )}
      </TreeNode>
    );
  };

  return (
    <TreeContainer>
      {projectsToShow.map((project) => renderNode(project))}
    </TreeContainer>
  );
};

export default ProjectTree;