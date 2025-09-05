import React, { useState } from 'react';
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Checkbox,
  IconButton,
  Chip,
  Typography,
  Button,
  TablePagination,
  Tooltip
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RefreshIcon from '@mui/icons-material/Refresh';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import { Campaign } from '../../types/campaigns';
import { format } from 'date-fns';

interface CampaignListProps {
  campaigns: Campaign[];
  onSelect: (campaign: Campaign) => void;
  onMultiSelect: (campaignIds: string[]) => void;
  onRefresh: () => void;
}

const CampaignList: React.FC<CampaignListProps> = ({
  campaigns,
  onSelect,
  onMultiSelect,
  onRefresh
}) => {
  const [selected, setSelected] = useState<string[]>([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const newSelected = campaigns.map((c) => c.campaign_id);
      setSelected(newSelected);
    } else {
      setSelected([]);
    }
  };

  const handleClick = (event: React.MouseEvent<unknown>, id: string) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    setSelected(newSelected);
  };

  const handleCompare = () => {
    onMultiSelect(selected);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'default';
      case 'sending':
        return 'warning';
      case 'sent':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const formatRate = (rate: number | undefined) => {
    if (rate === undefined || rate === null) return '-';
    return `${rate.toFixed(1)}%`;
  };

  // Paginate campaigns
  const paginatedCampaigns = campaigns.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, px: 2 }}>
        <Typography variant="h6">
          Campaigns ({campaigns.length})
        </Typography>
        <Box>
          {selected.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<CompareArrowsIcon />}
              onClick={handleCompare}
              sx={{ mr: 1 }}
            >
              Compare Selected ({selected.length})
            </Button>
          )}
          <IconButton onClick={onRefresh} title="Refresh">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selected.length > 0 && selected.length < campaigns.length}
                  checked={campaigns.length > 0 && selected.length === campaigns.length}
                  onChange={handleSelectAllClick}
                />
              </TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Recipients</TableCell>
              <TableCell>Open Rate</TableCell>
              <TableCell>Click Rate</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Sent</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedCampaigns.map((campaign) => {
              const isItemSelected = isSelected(campaign.campaign_id);
              
              return (
                <TableRow
                  key={campaign.campaign_id}
                  hover
                  onClick={(event) => handleClick(event, campaign.campaign_id)}
                  role="checkbox"
                  aria-checked={isItemSelected}
                  selected={isItemSelected}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell padding="checkbox">
                    <Checkbox checked={isItemSelected} />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {campaign.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {campaign.subject_line}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={campaign.status}
                      color={getStatusColor(campaign.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{campaign.stats.total_recipients || 0}</TableCell>
                  <TableCell>{formatRate(campaign.stats.open_rate)}</TableCell>
                  <TableCell>{formatRate(campaign.stats.click_rate)}</TableCell>
                  <TableCell>{formatDate(campaign.created_at)}</TableCell>
                  <TableCell>{formatDate(campaign.sent_at)}</TableCell>
                  <TableCell>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(campaign);
                        }}
                      >
                        <VisibilityIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              );
            })}
            {campaigns.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    No campaigns found. Create your first campaign to get started.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        rowsPerPageOptions={[5, 10, 25]}
        component="div"
        count={campaigns.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </Box>
  );
};

export default CampaignList;