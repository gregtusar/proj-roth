import React, { useState, useMemo } from 'react';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { Input, SIZE as InputSize } from 'baseui/input';
import { Pagination } from 'baseui/pagination';
import { CSVLink } from 'react-csv';
import { QueryResult } from '../../types/lists';

const Container = styled('div', {
  backgroundColor: '#ffffff',
  borderRadius: '8px',
  padding: '16px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
});

const Header = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '16px',
});

const Title = styled('h3', {
  fontSize: '16px',
  fontWeight: 600,
  margin: 0,
});

const Controls = styled('div', {
  display: 'flex',
  gap: '12px',
  alignItems: 'center',
});

const TableContainer = styled('div', {
  overflowX: 'auto',
  marginBottom: '16px',
  maxWidth: '100%',
  border: '1px solid #e0e0e0',
  borderRadius: '4px',
});

const Table = styled('table', {
  width: '100%',
  minWidth: 'max-content',
  borderCollapse: 'collapse',
  fontSize: '14px',
});

const TableHead = styled('thead', {
  backgroundColor: '#f5f5f5',
  borderBottom: '2px solid #e0e0e0',
});

const TableHeadCell = styled('th', {
  padding: '12px 16px',
  textAlign: 'left',
  fontWeight: 600,
  whiteSpace: 'nowrap',
  minWidth: '120px',
  borderRight: '1px solid #e0e0e0',
  ':last-child': {
    borderRight: 'none',
  },
});

const TableBody = styled('tbody', {
  '& tr:hover': {
    backgroundColor: '#f9f9f9',
  },
});

const TableRow = styled('tr', {
  borderBottom: '1px solid #e0e0e0',
  ':last-child': {
    borderBottom: 'none',
  },
});

const TableCell = styled('td', {
  padding: '10px 16px',
  whiteSpace: 'nowrap',
  minWidth: '120px',
  borderRight: '1px solid #e0e0e0',
  ':last-child': {
    borderRight: 'none',
  },
});

const PaginationContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  gap: '16px',
});

const InfoText = styled('div', {
  fontSize: '14px',
  color: '#666',
});

interface ResultsTableProps {
  results: QueryResult;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [rowsPerPage] = useState(25);

  // Filter rows based on search
  const filteredRows = useMemo(() => {
    if (!searchTerm) return results.rows;
    
    return results.rows.filter((row) =>
      row.some((cell) =>
        String(cell).toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
  }, [results.rows, searchTerm]);

  // Paginate filtered rows
  const paginatedRows = useMemo(() => {
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    return filteredRows.slice(startIndex, endIndex);
  }, [filteredRows, currentPage, rowsPerPage]);

  const totalPages = Math.ceil(filteredRows.length / rowsPerPage);
  
  // Debug logging
  console.log('[ResultsTable] Debug info:', {
    totalRows: results.rows.length,
    filteredRows: filteredRows.length,
    rowsPerPage,
    totalPages,
    currentPage,
    showPagination: totalPages > 1
  });

  // Prepare CSV data
  const csvData = useMemo(() => {
    const headers = results.columns;
    const rows = results.rows;
    return [headers, ...rows];
  }, [results]);

  const handleCopyToClipboard = () => {
    const text = csvData
      .map((row) => row.join('\t'))
      .join('\n');
    navigator.clipboard.writeText(text);
  };

  return (
    <Container>
      <Header>
        <Title>
          Query Results ({filteredRows.length.toLocaleString()} rows)
        </Title>
        <Controls>
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm((e.target as HTMLInputElement).value)}
            placeholder="Search results..."
            size={InputSize.compact}
            clearable
            overrides={{
              Root: {
                style: {
                  width: '200px',
                },
              },
            }}
          />
          <Button
            onClick={handleCopyToClipboard}
            kind={KIND.secondary}
            size={SIZE.compact}
          >
            Copy
          </Button>
          <CSVLink
            data={csvData}
            filename={`query_results_${Date.now()}.csv`}
            style={{ textDecoration: 'none' }}
          >
            <Button kind={KIND.primary} size={SIZE.compact}>
              Export CSV
            </Button>
          </CSVLink>
        </Controls>
      </Header>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              {results.columns.map((column, index) => (
                <TableHeadCell key={`header-${index}`}>
                  {column}
                </TableHeadCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedRows.map((row, rowIndex) => (
              <TableRow key={`row-${rowIndex}`}>
                {results.columns.map((_, cellIndex) => (
                  <TableCell key={`cell-${rowIndex}-${cellIndex}`}>
                    {row[cellIndex] !== null && row[cellIndex] !== undefined
                      ? String(row[cellIndex])
                      : '—'}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {filteredRows.length > 0 && (
        <PaginationContainer>
          {totalPages > 1 ? (
            <>
              <Pagination
                numPages={totalPages}
                currentPage={currentPage}
                onPageChange={({ nextPage }) => setCurrentPage(nextPage)}
                size={SIZE.compact}
              />
              <InfoText>
                Showing {((currentPage - 1) * rowsPerPage + 1).toLocaleString()} -{' '}
                {Math.min(currentPage * rowsPerPage, filteredRows.length).toLocaleString()}{' '}
                of {filteredRows.length.toLocaleString()} rows
              </InfoText>
            </>
          ) : (
            <InfoText style={{ textAlign: 'center', width: '100%' }}>
              Showing all {filteredRows.length.toLocaleString()} rows
            </InfoText>
          )}
        </PaginationContainer>
      )}

      {results.execution_time && (
        <InfoText style={{ marginTop: '12px', textAlign: 'right' }}>
          Query executed in {results.execution_time.toFixed(2)} seconds
        </InfoText>
      )}
    </Container>
  );
};

export default ResultsTable;