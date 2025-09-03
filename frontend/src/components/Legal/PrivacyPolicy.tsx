import React from 'react';
import { Container, Typography, Paper, Box } from '@mui/material';

const PrivacyPolicy: React.FC = () => {
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h3" gutterBottom>
          Privacy Policy
        </Typography>
        
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Last updated: {new Date().toLocaleDateString()}
        </Typography>

        <Box sx={{ mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Information We Collect
          </Typography>
          <Typography paragraph>
            We collect information you provide directly to us, such as when you create an account,
            use our services, or contact us for support. This includes:
          </Typography>
          <ul>
            <li>Name and email address (via Google OAuth)</li>
            <li>Search queries and interactions with voter data</li>
            <li>Saved lists and preferences</li>
          </ul>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            How We Use Your Information
          </Typography>
          <Typography paragraph>
            We use the information we collect to:
          </Typography>
          <ul>
            <li>Provide, maintain, and improve our services</li>
            <li>Process and complete transactions</li>
            <li>Send you technical notices and support messages</li>
            <li>Respond to your comments and questions</li>
          </ul>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Information Sharing
          </Typography>
          <Typography paragraph>
            We do not sell, trade, or otherwise transfer your personal information to third parties.
            We may share information only in the following circumstances:
          </Typography>
          <ul>
            <li>With your consent</li>
            <li>To comply with laws or respond to lawful requests</li>
            <li>To protect our rights, privacy, safety, or property</li>
          </ul>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Data Security
          </Typography>
          <Typography paragraph>
            We implement appropriate technical and organizational measures to protect the security
            of your personal information against unauthorized access, alteration, disclosure, or destruction.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Google OAuth
          </Typography>
          <Typography paragraph>
            Our application uses Google OAuth for authentication. When you sign in with Google,
            we only access your basic profile information (name and email). We do not access
            any other Google account data unless explicitly authorized by you.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Contact Us
          </Typography>
          <Typography paragraph>
            If you have any questions about this Privacy Policy, please contact us at:
            support@gwanalytica.ai
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default PrivacyPolicy;