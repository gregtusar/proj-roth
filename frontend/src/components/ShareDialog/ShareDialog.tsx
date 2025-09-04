import React, { useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box, IconButton, Alert } from '@mui/material';
import { ChatSession } from '../../types/chat';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import LinkIcon from '@mui/icons-material/Link';
import LinkOffIcon from '@mui/icons-material/LinkOff';

interface ShareDialogProps {
  session: ChatSession;
  onClose: () => void;
  onShareUpdated: () => void;
}

const ShareDialog: React.FC<ShareDialogProps> = ({ session, onClose, onShareUpdated }) => {
  const [isSharing, setIsSharing] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);

  const shareLink = `${window.location.origin}/chat/${session.session_id}`;

  const handleToggleShare = async () => {
    setIsSharing(true);
    try {
      const endpoint = session.is_public 
        ? `/api/sessions/${session.session_id}/share`
        : `/api/sessions/${session.session_id}/share`;
      
      const method = session.is_public ? 'DELETE' : 'POST';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to update share status');
      }

      onShareUpdated();
      
      // If we just made it public, copy link to clipboard and show feedback
      if (!session.is_public) {
        await handleCopyLink();
        setShareSuccess(true);
        // Show success message briefly before closing
        setTimeout(() => {
          onClose();
        }, 1500);
      } else {
        // If making private, close immediately
        onClose();
      }
    } catch (error) {
      console.error('Error updating share status:', error);
      setIsSharing(false);
    }
  };

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <Dialog 
      open={true} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          {session.is_public ? <LinkIcon /> : <LinkOffIcon />}
          {session.is_public ? 'Chat is Shared' : 'Share Chat'}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {shareSuccess ? (
          <Alert severity="success">
            Chat shared successfully! Link copied to clipboard.
          </Alert>
        ) : (
        <>
        {session.is_public ? (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              This chat is currently public. Anyone with the link can view it.
            </Typography>
            
            <Box 
              sx={{ 
                mt: 2, 
                p: 1, 
                bgcolor: 'grey.100', 
                borderRadius: 1,
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              <Typography 
                variant="body2" 
                sx={{ 
                  flex: 1, 
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  wordBreak: 'break-all'
                }}
              >
                {shareLink}
              </Typography>
              <IconButton 
                size="small" 
                onClick={handleCopyLink}
                title="Copy link"
              >
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Box>
            
            {copySuccess && (
              <Alert severity="success" sx={{ mt: 2 }}>
                Link copied to clipboard!
              </Alert>
            )}
            
            <Alert severity="warning" sx={{ mt: 2 }}>
              Making this chat private will remove access for anyone who has the link.
            </Alert>
          </>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Share this chat to allow anyone with the link to view it.
            </Typography>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              Once shared, anyone with the link will be able to view this chat's contents. 
              You can make it private again at any time.
            </Alert>
          </>
        )}
        </>
        )}
      </DialogContent>

      {!shareSuccess && (
        <DialogActions>
          <Button onClick={onClose} color="inherit">
            Cancel
          </Button>
          <Button
            onClick={handleToggleShare}
            variant="contained"
            disabled={isSharing}
            color={session.is_public ? "error" : "primary"}
            startIcon={session.is_public ? <LinkOffIcon /> : <LinkIcon />}
          >
            {isSharing ? 'Updating...' : session.is_public ? 'Make Private' : 'Share Chat'}
          </Button>
        </DialogActions>
      )}
    </Dialog>
  );
};

export default ShareDialog;