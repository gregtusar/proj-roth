import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Tab,
  Tabs,
  Paper,
  Container,
  Alert,
  CircularProgress
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import CampaignList from './CampaignList';
import CampaignCreate from './CampaignCreate';
import CampaignDetail from './CampaignDetail';
import CampaignStats from './CampaignStats';
import { Campaign } from '../../types/campaigns';
import api from '../../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`campaign-tabpanel-${index}`}
      aria-labelledby={`campaign-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const CampaignManager: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/campaigns');
      if (response.data.success) {
        setCampaigns(response.data.campaigns);
      }
    } catch (err: any) {
      setError('Failed to load campaigns');
      console.error('Error loading campaigns:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCreateCampaign = () => {
    setShowCreateDialog(true);
  };

  const handleCampaignCreated = (campaign: Campaign) => {
    loadCampaigns();
    setShowCreateDialog(false);
    setSelectedCampaign(campaign);
    setTabValue(1); // Switch to campaigns tab
  };

  const handleCampaignSelect = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setTabValue(2); // Switch to detail view
  };

  const handleMultiSelect = (campaignIds: string[]) => {
    setSelectedCampaigns(campaignIds);
    if (campaignIds.length > 0) {
      setTabValue(3); // Switch to stats view
    }
  };

  const handleCampaignSent = () => {
    loadCampaigns();
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ width: '100%', mt: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Campaign Manager
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateCampaign}
            sx={{ ml: 2 }}
          >
            New Campaign
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab label="Overview" />
            <Tab label="Campaigns" />
            <Tab label="Campaign Detail" disabled={!selectedCampaign} />
            <Tab label="Analytics" disabled={selectedCampaigns.length === 0} />
          </Tabs>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <TabPanel value={tabValue} index={0}>
                <Box sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Campaign Overview
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Total Campaigns
                      </Typography>
                      <Typography variant="h4">
                        {campaigns.length}
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Active Campaigns
                      </Typography>
                      <Typography variant="h4">
                        {campaigns.filter(c => c.status === 'sending').length}
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Sent Campaigns
                      </Typography>
                      <Typography variant="h4">
                        {campaigns.filter(c => c.status === 'sent').length}
                      </Typography>
                    </Paper>
                    <Paper sx={{ p: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Draft Campaigns
                      </Typography>
                      <Typography variant="h4">
                        {campaigns.filter(c => c.status === 'draft').length}
                      </Typography>
                    </Paper>
                  </Box>
                </Box>
              </TabPanel>

              <TabPanel value={tabValue} index={1}>
                <CampaignList
                  campaigns={campaigns}
                  onSelect={handleCampaignSelect}
                  onMultiSelect={handleMultiSelect}
                  onRefresh={loadCampaigns}
                />
              </TabPanel>

              <TabPanel value={tabValue} index={2}>
                {selectedCampaign && (
                  <CampaignDetail
                    campaign={selectedCampaign}
                    onUpdate={loadCampaigns}
                    onSent={handleCampaignSent}
                  />
                )}
              </TabPanel>

              <TabPanel value={tabValue} index={3}>
                {selectedCampaigns.length > 0 && (
                  <CampaignStats campaignIds={selectedCampaigns} />
                )}
              </TabPanel>
            </>
          )}
        </Paper>

        {showCreateDialog && (
          <CampaignCreate
            open={showCreateDialog}
            onClose={() => setShowCreateDialog(false)}
            onCreated={handleCampaignCreated}
          />
        )}
      </Box>
    </Container>
  );
};

export default CampaignManager;