import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Button
} from '@mui/material';
// Recharts import removed - using table-based analytics instead
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import { Campaign, CampaignStats as CampaignStatsType } from '../../types/campaigns';
import api from '../../services/api';

interface CampaignStatsProps {
  campaignIds: string[];
}


const CampaignStats: React.FC<CampaignStatsProps> = ({ campaignIds }) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<{ [key: string]: CampaignStatsType }>({});

  useEffect(() => {
    loadCampaignData();
  }, [campaignIds]);

  const loadCampaignData = async () => {
    setLoading(true);
    try {
      // Load campaign details and stats for each selected campaign
      const campaignPromises = campaignIds.map(id => 
        api.get(`/campaigns/${id}`)
      );
      const statsPromises = campaignIds.map(id => 
        api.get(`/campaigns/${id}/stats`)
      );

      const campaignResponses = await Promise.all(campaignPromises);
      const statsResponses = await Promise.all(statsPromises);

      const campaignsData = campaignResponses
        .filter(r => r.success)
        .map(r => r.campaign);
      
      const statsData: { [key: string]: CampaignStatsType } = {};
      statsResponses.forEach((r, index) => {
        if (r.success) {
          statsData[campaignIds[index]] = r.stats;
        }
      });

      setCampaigns(campaignsData);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading campaign data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = () => {
    // Prepare CSV data
    const csvData = campaigns.map(campaign => ({
      'Campaign Name': campaign.name,
      'Status': campaign.status,
      'Total Recipients': stats[campaign.campaign_id]?.total_recipients || 0,
      'Sent': stats[campaign.campaign_id]?.sent || 0,
      'Delivered': stats[campaign.campaign_id]?.delivered || 0,
      'Opened': stats[campaign.campaign_id]?.opened || 0,
      'Clicked': stats[campaign.campaign_id]?.clicked || 0,
      'Bounced': stats[campaign.campaign_id]?.bounced || 0,
      'Open Rate': `${stats[campaign.campaign_id]?.open_rate?.toFixed(1) || 0}%`,
      'Click Rate': `${stats[campaign.campaign_id]?.click_rate?.toFixed(1) || 0}%`,
      'Bounce Rate': `${stats[campaign.campaign_id]?.bounce_rate?.toFixed(1) || 0}%`
    }));

    // Convert to CSV string
    const headers = Object.keys(csvData[0]);
    const csvContent = [
      headers.join(','),
      ...csvData.map(row => 
        headers.map(header => row[header as keyof typeof row]).join(',')
      )
    ].join('\n');

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `campaign_stats_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Calculate aggregate stats
  const aggregateStats = {
    totalSent: Object.values(stats).reduce((sum, s) => sum + (s.sent || 0), 0),
    totalDelivered: Object.values(stats).reduce((sum, s) => sum + (s.delivered || 0), 0),
    totalOpened: Object.values(stats).reduce((sum, s) => sum + (s.opened || 0), 0),
    totalClicked: Object.values(stats).reduce((sum, s) => sum + (s.clicked || 0), 0),
    totalBounced: Object.values(stats).reduce((sum, s) => sum + (s.bounced || 0), 0)
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Campaign Analytics ({campaigns.length} campaigns)
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadCampaignData}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportCSV}
          >
            Export CSV
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Total Sent
              </Typography>
              <Typography variant="h4">
                {aggregateStats.totalSent.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Total Delivered
              </Typography>
              <Typography variant="h4">
                {aggregateStats.totalDelivered.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Total Opened
              </Typography>
              <Typography variant="h4">
                {aggregateStats.totalOpened.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Total Clicked
              </Typography>
              <Typography variant="h4">
                {aggregateStats.totalClicked.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Total Bounced
              </Typography>
              <Typography variant="h4">
                {aggregateStats.totalBounced.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>


      {/* Detailed Table */}
      <Paper sx={{ mt: 3 }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Detailed Statistics
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Campaign</TableCell>
                <TableCell align="right">Recipients</TableCell>
                <TableCell align="right">Sent</TableCell>
                <TableCell align="right">Delivered</TableCell>
                <TableCell align="right">Opened</TableCell>
                <TableCell align="right">Clicked</TableCell>
                <TableCell align="right">Bounced</TableCell>
                <TableCell align="right">Open Rate</TableCell>
                <TableCell align="right">Click Rate</TableCell>
                <TableCell align="right">Bounce Rate</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {campaigns.map((campaign) => (
                <TableRow key={campaign.campaign_id}>
                  <TableCell>{campaign.name}</TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.total_recipients || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.sent || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.delivered || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.opened || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.clicked || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.bounced || 0}
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.open_rate?.toFixed(1) || 0}%
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.click_rate?.toFixed(1) || 0}%
                  </TableCell>
                  <TableCell align="right">
                    {stats[campaign.campaign_id]?.bounce_rate?.toFixed(1) || 0}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default CampaignStats;