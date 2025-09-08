import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Divider,
  TextField,
  Alert,
  CircularProgress,
  LinearProgress,
  Link,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import Grid from '@mui/material/GridLegacy';
import { SendIcon, EmailIcon, RefreshIcon } from '../Common/Icons';
import { Campaign, CampaignStats as CampaignStatsType } from '../../types/campaigns';
import api from '../../services/api';
import { format } from 'date-fns';

interface CampaignDetailProps {
  campaign: Campaign;
  onUpdate: () => void;
  onSent: () => void;
}

const CampaignDetail: React.FC<CampaignDetailProps> = ({ campaign, onUpdate, onSent }) => {
  const [stats, setStats] = useState<CampaignStatsType | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testEmail, setTestEmail] = useState('');
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);

  useEffect(() => {
    loadStats();
  }, [campaign.campaign_id]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const data = await api.get<any>(`/campaigns/${campaign.campaign_id}/stats`);
      if (data.success) {
        setStats(data.stats);
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendCampaign = async () => {
    setSending(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response: any = await api.post(`/campaigns/${campaign.campaign_id}/send`);
      if (response.success) {
        setSuccess('Campaign is being sent! This may take a few minutes.');
        setShowSendDialog(false);
        onSent();
        // Refresh stats after a delay
        setTimeout(() => {
          loadStats();
          onUpdate();
        }, 3000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send campaign');
    } finally {
      setSending(false);
    }
  };

  const handleSendTest = async () => {
    if (!testEmail) {
      setError('Please enter a test email address');
      return;
    }
    
    setSending(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response: any = await api.post(`/campaigns/${campaign.campaign_id}/test`, {
        test_email: testEmail
      });
      if (response.success) {
        setSuccess(`Test email sent to ${testEmail}`);
        setShowTestDialog(false);
        setTestEmail('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send test email');
    } finally {
      setSending(false);
    }
  };

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
    if (!dateString) return 'Not sent';
    try {
      return format(new Date(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Campaign Info */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 3 }}>
              <Box>
                <Typography variant="h5" gutterBottom>
                  {campaign.name}
                </Typography>
                <Chip
                  label={campaign.status}
                  color={getStatusColor(campaign.status) as any}
                  size="small"
                />
              </Box>
              <Box>
                {campaign.status === 'draft' && (
                  <>
                    <Button
                      variant="outlined"
                      startIcon={<EmailIcon />}
                      onClick={() => setShowTestDialog(true)}
                      sx={{ mr: 1 }}
                    >
                      Send Test
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<SendIcon />}
                      onClick={() => setShowSendDialog(true)}
                    >
                      Send Campaign
                    </Button>
                  </>
                )}
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={loadStats}
                  sx={{ ml: 1 }}
                >
                  Refresh
                </Button>
              </Box>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Subject Line
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {campaign.subject_line}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Created By
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {campaign.created_by}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Created At
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {formatDate(campaign.created_at)}
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  Sent At
                </Typography>
                <Typography variant="body1" gutterBottom>
                  {formatDate(campaign.sent_at)}
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary">
                  Email Template
                </Typography>
                <Link
                  href={campaign.google_doc_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View Google Doc
                </Link>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Campaign Statistics
              </Typography>
              
              {loading ? (
                <CircularProgress />
              ) : stats ? (
                <Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Recipients
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_recipients || 0}
                    </Typography>
                  </Box>
                  
                  {campaign.status !== 'draft' && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Delivery Rate
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={stats.delivery_rate || 0}
                              sx={{ height: 8, borderRadius: 4 }}
                            />
                          </Box>
                          <Typography variant="body2">
                            {stats.delivery_rate?.toFixed(1) || 0}%
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Open Rate
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={stats.open_rate || 0}
                              sx={{ height: 8, borderRadius: 4 }}
                              color="success"
                            />
                          </Box>
                          <Typography variant="body2">
                            {stats.open_rate?.toFixed(1) || 0}%
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Click Rate
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={stats.click_rate || 0}
                              sx={{ height: 8, borderRadius: 4 }}
                              color="info"
                            />
                          </Box>
                          <Typography variant="body2">
                            {stats.click_rate?.toFixed(1) || 0}%
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          Bounce Rate
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: '100%', mr: 1 }}>
                            <LinearProgress
                              variant="determinate"
                              value={stats.bounce_rate || 0}
                              sx={{ height: 8, borderRadius: 4 }}
                              color="error"
                            />
                          </Box>
                          <Typography variant="body2">
                            {stats.bounce_rate?.toFixed(1) || 0}%
                          </Typography>
                        </Box>
                      </Box>
                      
                      <Divider sx={{ my: 2 }} />
                      
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Sent
                          </Typography>
                          <Typography variant="h6">
                            {stats.sent || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Delivered
                          </Typography>
                          <Typography variant="h6">
                            {stats.delivered || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Opened
                          </Typography>
                          <Typography variant="h6">
                            {stats.opened || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Clicked
                          </Typography>
                          <Typography variant="h6">
                            {stats.clicked || 0}
                          </Typography>
                        </Grid>
                      </Grid>
                    </>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No statistics available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Send Campaign Dialog */}
      <Dialog open={showSendDialog} onClose={() => setShowSendDialog(false)}>
        <DialogTitle>Send Campaign</DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Are you sure you want to send this campaign?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            This will send {stats?.total_recipients || 0} emails immediately.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSendDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSendCampaign}
            disabled={sending}
            startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {sending ? 'Sending...' : 'Send Campaign'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Email Dialog */}
      <Dialog open={showTestDialog} onClose={() => setShowTestDialog(false)}>
        <DialogTitle>Send Test Email</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Test Email Address"
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            margin="normal"
            helperText="Enter the email address to send a test to"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTestDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSendTest}
            disabled={sending || !testEmail}
            startIcon={sending ? <CircularProgress size={20} /> : <EmailIcon />}
          >
            {sending ? 'Sending...' : 'Send Test'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CampaignDetail;