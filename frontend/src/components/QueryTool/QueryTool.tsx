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
import apiClient from '../../services/api';

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
      const data = await apiClient.post<{ sql: string }>('/generate-sql', { prompt });
      setSql(data.sql);
      setIsEditingSQL(false);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate SQL';
      setError(errorMessage);
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
      // Fetch one extra row to determine if there are more pages
      const paginatedSQL = `${sql.trim().replace(/;?\s*$/, '')} LIMIT ${currentPageSize + 1} OFFSET ${offset}`;
      
      const data = await apiClient.post<any>('/execute-query', { sql: paginatedSQL });

      // Check if we got more rows than requested (indicates more pages)
      const hasMore = data.rows && data.rows.length > currentPageSize;
      const actualRows = hasMore ? data.rows.slice(0, currentPageSize) : data.rows;

      // Estimate total count based on current page and whether there are more results
      // This is an approximation but avoids the expensive COUNT query
      let estimatedTotal = offset + actualRows.length;
      if (hasMore) {
        // If there are more rows, we don't know the exact count
        // Show at least enough for the next page
        estimatedTotal = offset + currentPageSize + 1;
      }

      setResults({
        rows: actualRows,
        totalCount: estimatedTotal,
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
      setLoading(false);
    }
  };

  // Disabled auto-generation to avoid errors while typing
  // useEffect(() => {
  //   if (prompt && !sql) {
  //     const timer = setTimeout(() => {
  //       generateSQL();
  //     }, 1000);
  //     return () => clearTimeout(timer);
  //   }
  // }, [prompt]);

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
              results={{
                columns: results.rows.length > 0 ? Object.keys(results.rows[0]) : [],
                rows: results.rows.map(row => Object.values(row))
              }}
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