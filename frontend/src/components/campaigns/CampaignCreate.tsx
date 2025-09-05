import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Stepper,
  Step,
  StepLabel,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import { Campaign, CreateCampaignRequest } from '../../types/campaigns';
import api from '../../services/api';

interface CampaignCreateProps {
  open: boolean;
  onClose: () => void;
  onCreated: (campaign: Campaign) => void;
}

const steps = ['Campaign Details', 'Select List', 'Email Content', 'Review'];

const CampaignCreate: React.FC<CampaignCreateProps> = ({ open, onClose, onCreated }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lists, setLists] = useState<any[]>([]);
  
  const [formData, setFormData] = useState<CreateCampaignRequest>({
    name: '',
    list_id: '',
    subject_line: '',
    google_doc_url: ''
  });

  useEffect(() => {
    if (open) {
      loadLists();
    }
  }, [open]);

  const loadLists = async () => {
    try {
      const response = await api.get('/api/lists');
      if (response.data.success) {
        setLists(response.data.lists || []);
      }
    } catch (err) {
      console.error('Error loading lists:', err);
      setError('Failed to load lists');
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleInputChange = (field: keyof CreateCampaignRequest) => (
    event: React.ChangeEvent<HTMLInputElement | { value: unknown }>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    });
  };

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/api/campaigns', formData);
      if (response.data.success) {
        // Fetch the created campaign details
        const campaignResponse = await api.get(`/api/campaigns/${response.data.campaign_id}`);
        if (campaignResponse.data.success) {
          onCreated(campaignResponse.data.campaign);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setLoading(false);
    }
  };

  const isStepValid = (step: number) => {
    switch (step) {
      case 0:
        return formData.name && formData.subject_line;
      case 1:
        return formData.list_id;
      case 2:
        return formData.google_doc_url && isValidGoogleDocUrl(formData.google_doc_url);
      case 3:
        return true;
      default:
        return false;
    }
  };

  const isValidGoogleDocUrl = (url: string) => {
    return url.includes('docs.google.com/document/');
  };

  const getSelectedList = () => {
    return lists.find(l => l.id === formData.list_id);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Campaign Name"
              value={formData.name}
              onChange={handleInputChange('name')}
              margin="normal"
              required
              helperText="Give your campaign a memorable name"
            />
            <TextField
              fullWidth
              label="Subject Line"
              value={formData.subject_line}
              onChange={handleInputChange('subject_line')}
              margin="normal"
              required
              helperText="This will appear in the recipient's inbox"
            />
          </Box>
        );
      
      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Select List</InputLabel>
              <Select
                value={formData.list_id}
                onChange={handleInputChange('list_id') as any}
                label="Select List"
              >
                {lists.map((list) => (
                  <MenuItem key={list.id} value={list.id}>
                    {list.name} ({list.voter_count || 0} recipients)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {formData.list_id && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Selected: {getSelectedList()?.name} with {getSelectedList()?.voter_count || 0} recipients
              </Typography>
            )}
          </Box>
        );
      
      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Google Doc URL"
              value={formData.google_doc_url}
              onChange={handleInputChange('google_doc_url')}
              margin="normal"
              required
              placeholder="https://docs.google.com/document/d/..."
              helperText="Paste the URL of your Google Doc email template"
              error={formData.google_doc_url !== '' && !isValidGoogleDocUrl(formData.google_doc_url)}
            />
            {formData.google_doc_url && isValidGoogleDocUrl(formData.google_doc_url) && (
              <Box sx={{ mt: 1 }}>
                <Link
                  href={formData.google_doc_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open document in new tab
                </Link>
              </Box>
            )}
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                You can use these personalization tags in your document:
              </Typography>
              <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', mt: 1 }}>
                {'{{first_name}}'} - Recipient's first name<br />
                {'{{last_name}}'} - Recipient's last name<br />
                {'{{city}}'} - Recipient's city
              </Typography>
            </Alert>
          </Box>
        );
      
      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Review Campaign Details
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Campaign Name
              </Typography>
              <Typography variant="body1" gutterBottom>
                {formData.name}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Subject Line
              </Typography>
              <Typography variant="body1" gutterBottom>
                {formData.subject_line}
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                List
              </Typography>
              <Typography variant="body1" gutterBottom>
                {getSelectedList()?.name} ({getSelectedList()?.voter_count || 0} recipients)
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Email Template
              </Typography>
              <Link
                href={formData.google_doc_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                View Google Doc
              </Link>
            </Box>
          </Box>
        );
      
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Campaign</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        <Stepper activeStep={activeStep} sx={{ pt: 2, pb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {renderStepContent(activeStep)}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          disabled={activeStep === 0}
          onClick={handleBack}
        >
          Back
        </Button>
        {activeStep === steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={loading || !isStepValid(activeStep)}
          >
            {loading ? <CircularProgress size={24} /> : 'Create Campaign'}
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={!isStepValid(activeStep)}
          >
            Next
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default CampaignCreate;