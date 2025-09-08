import React from 'react';
import {
  Table,
  TableBuilder,
  TableBuilderColumn,
} from 'baseui/table-semantic';
import { StyledTable } from 'baseui/table';
import { Pagination } from 'baseui/pagination';
import { Select } from 'baseui/select';
import { Input } from 'baseui/input';
import { Button } from 'baseui/button';
import { styled } from 'baseui';
import { Search, Filter } from './Icons';
import { tokens } from '../../theme/customTheme';

// Re-export Base UI table components
export { Table, TableBuilder, TableBuilderColumn };

// Table container with toolbar
const TableContainer = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  gap: tokens.spacing.scale600,
  height: '100%',
});

const TableToolbar = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: `${tokens.spacing.scale400} 0`,
  gap: tokens.spacing.scale600,
});

const ToolbarLeft = styled('div', {
  display: 'flex',
  gap: tokens.spacing.scale400,
  alignItems: 'center',
  flex: 1,
});

const ToolbarRight = styled('div', {
  display: 'flex',
  gap: tokens.spacing.scale400,
  alignItems: 'center',
});

const TableContent = styled('div', {
  flex: 1,
  overflow: 'auto',
});

const TableFooter = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: `${tokens.spacing.scale400} 0`,
  borderTop: '1px solid',
  borderColor: 'inherit',
});

// Enhanced table component with common features
interface EnhancedTableProps {
  data: any[];
  columns: TableBuilderColumn<any>[];
  searchable?: boolean;
  filterable?: boolean;
  exportable?: boolean;
  paginated?: boolean;
  pageSize?: number;
  onSearch?: (query: string) => void;
  onFilter?: (filters: any) => void;
  onExport?: () => void;
  loading?: boolean;
  emptyMessage?: string;
}

export const EnhancedTable: React.FC<EnhancedTableProps> = ({
  data,
  columns,
  searchable = true,
  filterable = false,
  exportable = false,
  paginated = true,
  pageSize = 10,
  onSearch,
  onFilter,
  onExport,
  loading: _loading = false,
  emptyMessage: _emptyMessage = 'No data available',
}) => {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [currentPage, setCurrentPage] = React.useState(1);
  const [rowsPerPage, setRowsPerPage] = React.useState(pageSize);

  // Filter data based on search
  const filteredData = React.useMemo(() => {
    if (!searchQuery) return data;
    
    return data.filter(row =>
      Object.values(row).some(value =>
        String(value).toLowerCase().includes(searchQuery.toLowerCase())
      )
    );
  }, [data, searchQuery]);

  // Paginate data
  const paginatedData = React.useMemo(() => {
    if (!paginated) return filteredData;
    
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    return filteredData.slice(startIndex, endIndex);
  }, [filteredData, currentPage, rowsPerPage, paginated]);

  const totalPages = Math.ceil(filteredData.length / rowsPerPage);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
    if (onSearch) onSearch(query);
  };

  const handleExport = () => {
    if (onExport) {
      onExport();
    } else {
      // Default CSV export
      const csv = [
        columns.map(col => (col as any).label || '').join(','),
        ...filteredData.map(row =>
          columns.map(col => {
            const value = typeof (col as any).mapDataToValue === 'function'
              ? (col as any).mapDataToValue(row)
              : row[(col as any).mapDataToValue as string];
            return JSON.stringify(value || '');
          }).join(',')
        )
      ].join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'table-export.csv';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <TableContainer>
      {(searchable || filterable || exportable) && (
        <TableToolbar>
          <ToolbarLeft>
            {searchable && (
              <Input
                value={searchQuery}
                onChange={e => handleSearch(e.currentTarget.value)}
                placeholder="Search..."
                startEnhancer={<Search size={20} />}
                overrides={{
                  Root: {
                    style: {
                      width: '300px',
                    },
                  },
                }}
              />
            )}
            {filterable && (
              <Button
                kind="secondary"
                startEnhancer={<Filter size={20} />}
                onClick={() => onFilter && onFilter({})}
              >
                Filter
              </Button>
            )}
          </ToolbarLeft>
          <ToolbarRight>
            {exportable && (
              <Button
                kind="secondary"
                onClick={handleExport}
              >
                Export
              </Button>
            )}
          </ToolbarRight>
        </TableToolbar>
      )}

      <TableContent>
        <Table
          data={paginatedData}
          columns={columns as any[]}
        />
      </TableContent>

      {paginated && filteredData.length > 0 && (
        <TableFooter>
          <div style={{ display: 'flex', alignItems: 'center', gap: tokens.spacing.scale400 }}>
            <span>Rows per page:</span>
            <Select
              size="compact"
              options={[
                { label: '10', id: 10 },
                { label: '25', id: 25 },
                { label: '50', id: 50 },
                { label: '100', id: 100 },
              ]}
              value={[{ label: String(rowsPerPage), id: rowsPerPage }]}
              onChange={({ value }) => {
                setRowsPerPage(value[0].id as number);
                setCurrentPage(1);
              }}
              clearable={false}
              searchable={false}
              overrides={{
                Root: {
                  style: {
                    width: '100px',
                  },
                },
              }}
            />
          </div>

          <Pagination
            numPages={totalPages}
            currentPage={currentPage}
            onPageChange={({ nextPage }) => setCurrentPage(nextPage)}
            size="compact"
          />

          <div>
            Showing {((currentPage - 1) * rowsPerPage) + 1} - {Math.min(currentPage * rowsPerPage, filteredData.length)} of {filteredData.length}
          </div>
        </TableFooter>
      )}
    </TableContainer>
  );
};

// Styled table for custom implementations
export const StyledDataTable = styled(StyledTable, ({ $theme }) => ({
  borderRadius: tokens.borders.radius400,
  overflow: 'hidden',
  boxShadow: $theme.lighting.shadow400,
}));