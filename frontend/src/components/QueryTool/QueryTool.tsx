import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Stack,
  Chip
} from '@mui/material';
import {
  PlayArrow as RunIcon,
  Save as SaveIcon,
  Edit as EditIcon,
  AutoAwesome as GenerateIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon
} from '@mui/icons-material';
import { Editor } from '@monaco-editor/react';
import ResultsTable from '../ListManager/ResultsTable';
import { useAuthCheck } from '../../hooks/useAuthCheck';

interface QueryResult {
  rows: any[];
  totalCount: number;
  page: number;
  pageSize: number;
}

interface SaveDialogState {
  open: boolean;
  listName: string;
  description: string;
}

const QueryTool: React.FC = () => {
  useAuthCheck();
  const navigate = useNavigate();

  const [prompt, setPrompt] = useState('');
  const [sql, setSql] = useState('');
  const [isEditingSQL, setIsEditingSQL] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<QueryResult | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [copied, setCopied] = useState(false);
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

    setGenerating(true);
    setError(null);

    try {
      const response = await fetch('/api/generate-sql', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate SQL');
      }

      const data = await response.json();
      setSql(data.sql);
      setIsEditingSQL(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate SQL');
    } finally {
      setGenerating(false);
    }
  };

  const executeQuery = useCallback(async (currentPage: number = 1, currentPageSize: number = 25) => {
    if (!sql.trim()) {
      setError('Please generate or enter SQL first');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const offset = (currentPage - 1) * currentPageSize;
      const paginatedSQL = `${sql.trim().replace(/;?\s*$/, '')} LIMIT ${currentPageSize} OFFSET ${offset}`;
      
      const countSQL = `SELECT COUNT(*) as total FROM (${sql.trim().replace(/;?\s*$/, '')}) as subquery`;

      const [dataResponse, countResponse] = await Promise.all([
        fetch('/api/execute-query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ sql: paginatedSQL })
        }),
        fetch('/api/execute-query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ sql: countSQL })
        })
      ]);

      if (!dataResponse.ok) {
        const errorData = await dataResponse.json();
        throw new Error(errorData.detail || 'Failed to execute query');
      }

      const data = await dataResponse.json();
      let totalCount = 0;
      
      if (countResponse.ok) {
        const countData = await countResponse.json();
        totalCount = countData.rows?.[0]?.total || data.rows.length;
      }

      setResults({
        rows: data.rows,
        totalCount,
        page: currentPage,
        pageSize: currentPageSize
      });
      setPage(currentPage);
      setPageSize(currentPageSize);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute query');
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, [sql]);

  const handlePageChange = (newPage: number) => {
    executeQuery(newPage, pageSize);
  };

  const handlePageSizeChange = (newPageSize: number) => {
    executeQuery(1, newPageSize);
  };

  const handlePromptKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      generateSQL();
    }
  };

  const handleCopySQL = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/lists', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: saveDialog.listName,
          description: saveDialog.description || prompt,
          query: sql,
          prompt: prompt
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save list');
      }

      setSaveDialog({ open: false, listName: '', description: '' });
      navigate('/lists');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save list');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (prompt && !sql) {
      const timer = setTimeout(() => {
        generateSQL();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [prompt]);

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Query Builder
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Stack spacing={2}>
          <TextField
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            label="Describe your query in natural language"
            placeholder="e.g., Find all Democratic voters in Westfield who voted in the last 3 elections"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyPress={handlePromptKeyPress}
            disabled={generating}
            InputProps={{
              endAdornment: (
                <Button
                  variant="contained"
                  startIcon={generating ? <CircularProgress size={20} /> : <GenerateIcon />}
                  onClick={generateSQL}
                  disabled={!prompt.trim() || generating}
                  sx={{ ml: 1 }}
                >
                  {generating ? 'Generating...' : 'Generate SQL'}
                </Button>
              )
            }}
          />

          {sql && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" sx={{ flexGrow: 1 }}>
                  Generated SQL
                </Typography>
                <Stack direction="row" spacing={1}>
                  <Tooltip title={copied ? 'Copied!' : 'Copy SQL'}>
                    <IconButton size="small" onClick={handleCopySQL}>
                      {copied ? <CheckIcon /> : <CopyIcon />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title={isEditingSQL ? 'View mode' : 'Edit SQL'}>
                    <IconButton 
                      size="small" 
                      onClick={() => setIsEditingSQL(!isEditingSQL)}
                      color={isEditingSQL ? 'primary' : 'default'}
                    >
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Box>

              {isEditingSQL ? (
                <Box sx={{ border: '1px solid #ddd', borderRadius: 1 }}>
                  <Editor
                    height="200px"
                    language="sql"
                    theme="vs-light"
                    value={sql}
                    onChange={(value) => setSql(value || '')}
                    options={{
                      minimap: { enabled: false },
                      fontSize: 14,
                      wordWrap: 'on',
                      lineNumbers: 'on',
                      scrollBeyondLastLine: false
                    }}
                  />
                </Box>
              ) : (
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    bgcolor: 'grey.50',
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}
                >
                  {sql}
                </Paper>
              )}

              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <RunIcon />}
                  onClick={() => executeQuery(1, pageSize)}
                  disabled={!sql.trim() || loading}
                >
                  {loading ? 'Running...' : 'Run Query'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<SaveIcon />}
                  onClick={() => setSaveDialog({ ...saveDialog, open: true })}
                  disabled={!sql.trim()}
                >
                  Save as List
                </Button>
              </Stack>
            </Box>
          )}
        </Stack>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {results && (
        <Paper sx={{ flexGrow: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <Box sx={{ p: 2, borderBottom: '1px solid #ddd' }}>
            <Typography variant="h6">
              Results
              <Chip 
                label={`${results.totalCount.toLocaleString()} total`} 
                size="small" 
                sx={{ ml: 2 }} 
              />
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
            <ResultsTable
              data={results.rows}
              totalCount={results.totalCount}
              page={page}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
              loading={loading}
            />
          </Box>
        </Paper>
      )}

      <Dialog 
        open={saveDialog.open} 
        onClose={() => setSaveDialog({ ...saveDialog, open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save Query as List</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              autoFocus
              fullWidth
              label="List Name"
              value={saveDialog.listName}
              onChange={(e) => setSaveDialog({ ...saveDialog, listName: e.target.value })}
              placeholder="e.g., Active Democratic Voters in Westfield"
            />
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description (optional)"
              value={saveDialog.description}
              onChange={(e) => setSaveDialog({ ...saveDialog, description: e.target.value })}
              placeholder="Additional description of this list"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialog({ ...saveDialog, open: false })}>
            Cancel
          </Button>
          <Button 
            onClick={handleSaveList} 
            variant="contained"
            disabled={!saveDialog.listName.trim() || loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Save List'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QueryTool;