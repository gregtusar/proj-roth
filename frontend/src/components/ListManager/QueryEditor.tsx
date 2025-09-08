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

interface QueryEditorProps {
  list: VoterList;
}

const QueryEditor: React.FC<QueryEditorProps> = ({ list }) => {
  const dispatch = useDispatch<AppDispatch>();
  const [query, setQuery] = useState(list.query);
  const [isEditing, setIsEditing] = useState(false);
  const [isRunningQuery, setIsRunningQuery] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

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
    console.log('[QueryEditor] handleSave called');
    console.log('[QueryEditor] Current query:', query);
    console.log('[QueryEditor] Original query:', list.query);
    console.log('[QueryEditor] Has changes:', query !== list.query);
    
    if (query !== list.query) {
      setIsSaving(true);
      try {
        console.log('[QueryEditor] Dispatching updateList with:', { listId: list.id, query });
        const result = await dispatch(updateList({ listId: list.id, updates: { query } })).unwrap();
        console.log('[QueryEditor] Successfully saved query update, result:', result);
        setIsEditing(false);
        // Show success feedback
        alert('Query saved successfully!');
      } catch (error) {
        console.error('[QueryEditor] Failed to save query:', error);
        alert(`Failed to save query: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setIsSaving(false);
      }
    } else {
      // No changes to save, just exit edit mode
      console.log('[QueryEditor] No changes to save, exiting edit mode');
      setIsEditing(false);
    }
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
          {!isEditing ? [
              <Button
                key="regenerate"
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
              </Button>,
              <Button
                key="edit"
                onClick={() => setIsEditing(true)}
                kind={KIND.secondary}
                size={SIZE.mini}
              >
                Edit
              </Button>,
              <Button
                key="run"
                onClick={handleRun}
                kind={KIND.primary}
                size={SIZE.mini}
                isLoading={isRunningQuery}
              >
                Run Query
              </Button>
          ] : [
              <Button 
                key="cancel"
                onClick={handleCancel} 
                kind={KIND.tertiary} 
                size={SIZE.mini}
                disabled={isSaving}
              >
                Cancel
              </Button>,
              <Button 
                key="save"
                onClick={handleSave} 
                kind={KIND.primary} 
                size={SIZE.mini}
                isLoading={isSaving}
                disabled={isSaving}
              >
                Save
              </Button>
          ]}
        </ButtonGroup>
      </EditorHeader>

      <StyledEditor>
        <Editor
          value={query}
          onValueChange={(code) => {
            console.log('[QueryEditor] Editor value changed, isEditing:', isEditing);
            if (isEditing) {
              setQuery(code);
            }
          }}
          highlight={highlightSQL}
          padding={10}
          disabled={!isEditing}
          style={{
            fontFamily: '"Fira Code", "Fira Mono", monospace',
            fontSize: 13,
            backgroundColor: isEditing ? '#2a2a2a' : '#1e1e1e',
            color: '#d4d4d4',
            minHeight: '100px',
            borderRadius: '4px',
            cursor: isEditing ? 'text' : 'not-allowed',
            opacity: isEditing ? 1 : 0.8,
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