import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const TermsOfService: React.FC = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h3" gutterBottom>
          Terms of Service
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Last updated: {new Date().toLocaleDateString()}
        </Typography>

        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Acceptance of Terms
          </Typography>
          <Typography paragraph>
            By accessing and using this service, you accept and agree to be bound by the terms
            and provision of this agreement.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Use License
          </Typography>
          <Typography paragraph>
            Permission is granted to temporarily access the materials (information or software)
            on our service for personal, non-commercial transitory viewing only.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Disclaimer
          </Typography>
          <Typography paragraph>
            The materials on our service are provided on an 'as is' basis. We make no warranties,
            expressed or implied, and hereby disclaim and negate all other warranties including,
            without limitation, implied warranties or conditions of merchantability, fitness for
            a particular purpose, or non-infringement of intellectual property or other violation of rights.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Limitations
          </Typography>
          <Typography paragraph>
            In no event shall our organization or its suppliers be liable for any damages
            (including, without limitation, damages for loss of data or profit, or due to business
            interruption) arising out of the use or inability to use our service.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Privacy
          </Typography>
          <Typography paragraph>
            Your use of our service is also governed by our Privacy Policy.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Contact Information
          </Typography>
          <Typography paragraph>
            If you have any questions about these Terms of Service, please contact us at:
            support@gwanalytica.ai
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default TermsOfService;