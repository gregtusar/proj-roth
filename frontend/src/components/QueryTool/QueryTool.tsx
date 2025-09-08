import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { ButtonGroup } from 'baseui/button-group';
import { Input } from 'baseui/input';
import { Heading, HeadingLevel } from 'baseui/heading';
import { Modal, ModalHeader, ModalBody, ModalFooter, ModalButton } from 'baseui/modal';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-sql';
import ResultsTable from '../ListManager/ResultsTable';
import { useAuthCheck } from '../../hooks/useAuthCheck';
import apiClient from '../../services/api';
import { QueryResult } from '../../types/lists';

interface SaveDialogState {
  open: boolean;
  listName: string;
  description: string;
}

const Container = styled('div', {
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: '#f5f5f5',
  padding: '24px',
});

const HeaderSection = styled('div', {
  marginBottom: '24px',
});

const PromptContainer = styled('div', {
  backgroundColor: '#ffffff',
  borderRadius: '8px',
  padding: '20px',
  marginBottom: '24px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
});

const EditorContainer = styled('div', {
  backgroundColor: '#1e1e1e',
  borderRadius: '8px',
  padding: '16px',
  marginBottom: '24px',
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

const ErrorAlert = styled('div', {
  backgroundColor: '#fee2e2',
  color: '#dc2626',
  padding: '12px',
  borderRadius: '4px',
  marginBottom: '16px',
});

const QueryTool: React.FC = () => {
  useAuthCheck();
  const navigate = useNavigate();

  const [prompt, setPrompt] = useState('');
  const [sql, setSql] = useState('');
  const [isEditingSQL, setIsEditingSQL] = useState(false);
  const [isRunningQuery, setIsRunningQuery] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<QueryResult | null>(null);
  const [saveDialog, setSaveDialog] = useState<SaveDialogState>({
    open: false,
    listName: '',
    description: ''
  });

  const generateSQL = async () => {
    if (!prompt.trim()) {
      setError('Please enter a query description');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const data = await apiClient.post<{ sql: string }>('/generate-sql', { prompt });
      setSql(data.sql);
      setIsEditingSQL(false);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate SQL';
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  };

  const executeQuery = async () => {
    if (!sql.trim()) {
      setError('Please generate or enter SQL first');
      return;
    }

    setIsRunningQuery(true);
    setError(null);
    setResults(null);

    try {
      // Execute query without modifying it - let backend handle it
      const data = await apiClient.post<QueryResult>('/execute-query', { sql });
      setResults(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to execute query';
      setError(errorMessage);
    } finally {
      setIsRunningQuery(false);
    }
  };

  const handleSaveChanges = () => {
    setIsEditingSQL(false);
  };

  const handleCancelEdit = () => {
    // Reset SQL to last saved state if needed
    setIsEditingSQL(false);
  };

  const handleSaveList = async () => {
    if (!saveDialog.listName.trim()) {
      setError('Please enter a list name');
      return;
    }

    if (!sql.trim()) {
      setError('No SQL to save');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      await apiClient.post('/lists/', {
        name: saveDialog.listName,
        description: saveDialog.description || prompt,
        query: sql,
        prompt: prompt
      });

      setSaveDialog({ open: false, listName: '', description: '' });
      navigate('/lists');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to save list';
      setError(errorMessage);
    } finally {
      setIsSaving(false);
    }
  };

  const highlightSQL = (code: string) => {
    return Prism.highlight(code, Prism.languages.sql, 'sql');
  };


  return (
    <Container>
      <HeaderSection>
        <HeadingLevel>
          <Heading styleLevel={3}>Query Builder</Heading>
        </HeadingLevel>
      </HeaderSection>

      <PromptContainer>
        <div style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
          Describe your query in natural language
        </div>
        <Input
          value={prompt}
          onChange={(e) => setPrompt((e.target as HTMLInputElement).value)}
          placeholder="e.g., Find all Democratic voters in Westfield who voted in the last 3 elections"
          overrides={{
            Root: {
              style: {
                marginBottom: '12px',
              },
            },
          }}
        />
        <Button
          onClick={generateSQL}
          kind={KIND.primary}
          size={SIZE.compact}
          disabled={!prompt.trim() || isGenerating}
          isLoading={isGenerating}
        >
          Generate SQL
        </Button>
      </PromptContainer>

      {sql && (
        <EditorContainer>
          <EditorHeader>
            <EditorTitle>SQL Query</EditorTitle>
            <ButtonGroup size={SIZE.mini}>
              {!isEditingSQL ? [
                  <Button
                    key="edit"
                    onClick={() => setIsEditingSQL(true)}
                    kind={KIND.secondary}
                    size={SIZE.mini}
                  >
                    Edit
                  </Button>,
                  <Button
                    key="run"
                    onClick={executeQuery}
                    kind={KIND.primary}
                    size={SIZE.mini}
                    isLoading={isRunningQuery}
                  >
                    Run Query
                  </Button>,
                  <Button
                    key="save"
                    onClick={() => setSaveDialog({ ...saveDialog, open: true })}
                    kind={KIND.secondary}
                    size={SIZE.mini}
                  >
                    Save as List
                  </Button>
              ] : [
                  <Button 
                    key="cancel"
                    onClick={handleCancelEdit} 
                    kind={KIND.tertiary} 
                    size={SIZE.mini}
                  >
                    Cancel
                  </Button>,
                  <Button 
                    key="save-changes"
                    onClick={handleSaveChanges} 
                    kind={KIND.primary} 
                    size={SIZE.mini}
                  >
                    Save
                  </Button>
              ]}
            </ButtonGroup>
          </EditorHeader>

          <StyledEditor>
            <Editor
              value={sql}
              onValueChange={(code) => {
                if (isEditingSQL) {
                  setSql(code);
                }
              }}
              highlight={highlightSQL}
              padding={10}
              disabled={!isEditingSQL}
              style={{
                fontFamily: '"Fira Code", "Fira Mono", monospace',
                fontSize: 13,
                backgroundColor: isEditingSQL ? '#2a2a2a' : '#1e1e1e',
                color: '#d4d4d4',
                minHeight: '100px',
                borderRadius: '4px',
                cursor: isEditingSQL ? 'text' : 'not-allowed',
                opacity: isEditingSQL ? 1 : 0.8,
              }}
            />
          </StyledEditor>

          {results && results.rows && (
            <div style={{ color: '#888', fontSize: '12px', marginTop: '8px' }}>
              Query returned {results.rows.length.toLocaleString()} rows
            </div>
          )}
        </EditorContainer>
      )}

      {error && (
        <ErrorAlert>
          {error}
        </ErrorAlert>
      )}

      {results && <ResultsTable results={results} />}

      <Modal
        isOpen={saveDialog.open}
        onClose={() => setSaveDialog({ ...saveDialog, open: false })}
        size="default"
      >
        <ModalHeader>Save Query as List</ModalHeader>
        <ModalBody>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ marginBottom: '8px', fontSize: '14px', fontWeight: 600 }}>List Name</div>
            <Input
              value={saveDialog.listName}
              onChange={(e) => setSaveDialog({ ...saveDialog, listName: (e.target as HTMLInputElement).value })}
              placeholder="e.g., Active Democratic Voters in Westfield"
              autoFocus
            />
          </div>
          <div>
            <div style={{ marginBottom: '8px', fontSize: '14px', fontWeight: 600 }}>Description (optional)</div>
            <Input
              value={saveDialog.description}
              onChange={(e) => setSaveDialog({ ...saveDialog, description: (e.target as HTMLInputElement).value })}
              placeholder="Additional description of this list"
            />
          </div>
        </ModalBody>
        <ModalFooter>
          <ModalButton kind={KIND.tertiary} onClick={() => setSaveDialog({ ...saveDialog, open: false })}>
            Cancel
          </ModalButton>
          <ModalButton
            onClick={handleSaveList}
            disabled={!saveDialog.listName.trim() || isSaving}
            isLoading={isSaving}
          >
            Save List
          </ModalButton>
        </ModalFooter>
      </Modal>
    </Container>
  );
};

export default QueryTool;