import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { ButtonGroup } from 'baseui/button-group';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-sql';
import { AppDispatch } from '../../store';
import { runQuery, updateList } from '../../store/listsSlice';
import { VoterList } from '../../types/lists';
import * as listsService from '../../services/lists';

const EditorContainer = styled('div', {
  backgroundColor: '#1e1e1e',
  borderRadius: '8px',
  padding: '16px',
  marginBottom: '20px',
  position: 'relative',
});

const EditorHeader = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '12px',
});

const EditorTitle = styled('div', {
  color: '#cccccc',
  fontSize: '14px',
  fontWeight: 600,
});

const StyledEditor = styled('div', {
  '& textarea': {
    outline: 'none !important',
  },
  '& pre': {
    margin: '0 !important',
  },
});

const ButtonContainer = styled('div', {
  marginTop: '12px',
  display: 'flex',
  justifyContent: 'flex-end',
  gap: '8px',
});

interface QueryEditorProps {
  list: VoterList;
}

const QueryEditor: React.FC<QueryEditorProps> = ({ list }) => {
  const dispatch = useDispatch<AppDispatch>();
  const [query, setQuery] = useState(list.query);
  const [isEditing, setIsEditing] = useState(false);
  const [isRunningQuery, setIsRunningQuery] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Update query when list changes
  React.useEffect(() => {
    setQuery(list.query);
    setIsEditing(false);
  }, [list.id, list.query]);

  const handleRun = async () => {
    setIsRunningQuery(true);
    try {
      await dispatch(runQuery(list.id)).unwrap();
    } finally {
      setIsRunningQuery(false);
    }
  };

  const handleSave = async () => {
    if (query !== list.query) {
      await dispatch(updateList({ listId: list.id, updates: { query } })).unwrap();
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setQuery(list.query);
    setIsEditing(false);
  };

  const handleRegenerateQuery = async () => {
    // This will call the backend to use AI to generate SQL from the description
    setIsRegenerating(true);
    try {
      const response = await listsService.regenerateSqlQuery(list.id);
      setQuery(response.query);
      // Automatically save the new query
      await dispatch(updateList({ listId: list.id, updates: { query: response.query } })).unwrap();
    } catch (error) {
      console.error('Failed to regenerate SQL query:', error);
      alert('Failed to regenerate SQL query. Please try again.');
    } finally {
      setIsRegenerating(false);
    }
  };

  const highlightSQL = (code: string) => {
    return Prism.highlight(code, Prism.languages.sql, 'sql');
  };

  return (
    <EditorContainer>
      <EditorHeader>
        <EditorTitle>SQL Query</EditorTitle>
        <ButtonGroup size={SIZE.mini}>
          {!isEditing ? (
            <>
              <Button
                onClick={handleRegenerateQuery}
                kind={KIND.tertiary}
                size={SIZE.mini}
                disabled={!list.description}
                isLoading={isRegenerating}
                overrides={{
                  BaseButton: {
                    style: {
                      color: '#ffffff',
                      ':hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      },
                      ':disabled': {
                        color: 'rgba(255, 255, 255, 0.5)',
                      },
                    },
                  },
                }}
              >
                Regenerate SQL
              </Button>
              <Button
                onClick={() => setIsEditing(true)}
                kind={KIND.secondary}
                size={SIZE.mini}
              >
                Edit
              </Button>
              <Button
                onClick={handleRun}
                kind={KIND.primary}
                size={SIZE.mini}
                isLoading={isRunningQuery}
              >
                Run Query
              </Button>
            </>
          ) : (
            <>
              <Button onClick={handleCancel} kind={KIND.tertiary} size={SIZE.mini}>
                Cancel
              </Button>
              <Button onClick={handleSave} kind={KIND.primary} size={SIZE.mini}>
                Save
              </Button>
            </>
          )}
        </ButtonGroup>
      </EditorHeader>

      <StyledEditor>
        <Editor
          value={query}
          onValueChange={setQuery}
          highlight={highlightSQL}
          padding={10}
          disabled={!isEditing}
          style={{
            fontFamily: '"Fira Code", "Fira Mono", monospace',
            fontSize: 13,
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
            minHeight: '100px',
            borderRadius: '4px',
          }}
        />
      </StyledEditor>

      {list.row_count !== undefined && list.row_count !== null && (
        <div style={{ color: '#888', fontSize: '12px', marginTop: '8px' }}>
          Last run returned {list.row_count.toLocaleString()} rows
        </div>
      )}
    </EditorContainer>
  );
};

export default QueryEditor;