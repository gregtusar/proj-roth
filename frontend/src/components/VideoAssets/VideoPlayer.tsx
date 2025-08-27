import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Box,
  Typography,
  Tabs,
  Tab,
  Button,
  Stack,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  ContentCopy as CopyIcon,
  Share as ShareIcon,
  Check as CheckIcon
} from '@mui/icons-material';

interface VideoVersion {
  url: string;
  size: number;
  duration?: number;
  resolution?: string;
  format?: string;
}

interface VideoDetail {
  id: string;
  title: string;
  description?: string;
  tags: string[];
  campaign?: string;
  original_url: string;
  versions: {
    [key: string]: VideoVersion;
  };
  metadata?: {
    duration: number;
    resolution: string;
    aspect_ratio: string;
    file_size: number;
    fps?: number;
    codec?: string;
    bitrate?: number;
  };
  uploaded_at: string;
  usage_count: number;
}

interface VideoPlayerProps {
  open: boolean;
  onClose: () => void;
  video: VideoDetail;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ open, onClose, video }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedVersion, setSelectedVersion] = useState('original');
  const [copied, setCopied] = useState(false);

  const getVideoUrl = () => {
    if (selectedVersion === 'original') {
      return video.original_url;
    }
    return video.versions[selectedVersion]?.url || video.original_url;
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(getVideoUrl());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    window.open(getVideoUrl(), '_blank');
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'N/A';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB';
    return Math.round(bytes / 1048576) + ' MB';
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const versionLabels: { [key: string]: string } = {
    original: 'Original',
    tiktok: 'TikTok (9:16)',
    instagram_reel: 'Instagram Reel (9:16)',
    instagram_feed: 'Instagram Feed (1:1)',
    instagram_story: 'Instagram Story (9:16)',
    email: 'Email (Compressed)',
    youtube_short: 'YouTube Short (9:16)'
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh', display: 'flex', flexDirection: 'column' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">{video.title}</Typography>
          <Stack direction="row" spacing={1}>
            <Tooltip title={copied ? 'Copied!' : 'Copy link'}>
              <IconButton onClick={handleCopyLink}>
                {copied ? <CheckIcon /> : <CopyIcon />}
              </IconButton>
            </Tooltip>
            <IconButton onClick={handleDownload}>
              <DownloadIcon />
            </IconButton>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Stack>
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column', flex: 1 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
            <Tab label="Player" />
            <Tab label="Versions" />
            <Tab label="Details" />
          </Tabs>
        </Box>
        
        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          {activeTab === 0 && (
            <Box>
              <Box sx={{ mb: 2 }}>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {['original', ...Object.keys(video.versions)].map(version => (
                    <Chip
                      key={version}
                      label={versionLabels[version] || version}
                      onClick={() => setSelectedVersion(version)}
                      color={selectedVersion === version ? 'primary' : 'default'}
                      variant={selectedVersion === version ? 'filled' : 'outlined'}
                    />
                  ))}
                </Stack>
              </Box>
              
              <Box sx={{ width: '100%', bgcolor: 'black', borderRadius: 1 }}>
                <video
                  key={getVideoUrl()}
                  controls
                  style={{ width: '100%', maxHeight: '60vh' }}
                  src={getVideoUrl()}
                >
                  Your browser does not support the video tag.
                </video>
              </Box>
              
              {video.description && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Description
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {video.description}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
          
          {activeTab === 1 && (
            <List>
              <ListItem>
                <ListItemText
                  primary="Original"
                  secondary={
                    video.metadata
                      ? `${video.metadata.resolution} • ${formatDuration(video.metadata.duration)} • ${formatFileSize(video.metadata.file_size)}`
                      : 'Loading...'
                  }
                />
                <ListItemSecondaryAction>
                  <Button
                    startIcon={<DownloadIcon />}
                    onClick={() => window.open(video.original_url, '_blank')}
                  >
                    Download
                  </Button>
                </ListItemSecondaryAction>
              </ListItem>
              
              <Divider />
              
              {Object.entries(video.versions).map(([key, version]) => (
                <React.Fragment key={key}>
                  <ListItem>
                    <ListItemText
                      primary={versionLabels[key] || key}
                      secondary={`${version.resolution || 'N/A'} • ${formatDuration(version.duration)} • ${formatFileSize(version.size)}`}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        startIcon={<DownloadIcon />}
                        onClick={() => window.open(version.url, '_blank')}
                        size="small"
                      >
                        Download
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          )}
          
          {activeTab === 2 && (
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Campaign
                </Typography>
                <Typography variant="body1">
                  {video.campaign || 'No campaign assigned'}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Tags
                </Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                  {video.tags.length > 0 ? (
                    video.tags.map(tag => (
                      <Chip key={tag} label={tag} size="small" />
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No tags
                    </Typography>
                  )}
                </Stack>
              </Box>
              
              {video.metadata && (
                <>
                  <Divider />
                  <Typography variant="h6">Technical Details</Typography>
                  
                  <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Duration
                      </Typography>
                      <Typography variant="body1">
                        {formatDuration(video.metadata.duration)}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Resolution
                      </Typography>
                      <Typography variant="body1">
                        {video.metadata.resolution}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Aspect Ratio
                      </Typography>
                      <Typography variant="body1">
                        {video.metadata.aspect_ratio}
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        File Size
                      </Typography>
                      <Typography variant="body1">
                        {formatFileSize(video.metadata.file_size)}
                      </Typography>
                    </Box>
                    
                    {video.metadata.fps && (
                      <Box>
                        <Typography variant="subtitle2" color="text.secondary">
                          Frame Rate
                        </Typography>
                        <Typography variant="body1">
                          {video.metadata.fps.toFixed(1)} fps
                        </Typography>
                      </Box>
                    )}
                    
                    {video.metadata.codec && (
                      <Box>
                        <Typography variant="subtitle2" color="text.secondary">
                          Codec
                        </Typography>
                        <Typography variant="body1">
                          {video.metadata.codec}
                        </Typography>
                      </Box>
                    )}
                    
                    {video.metadata.bitrate && (
                      <Box>
                        <Typography variant="subtitle2" color="text.secondary">
                          Bitrate
                        </Typography>
                        <Typography variant="body1">
                          {Math.round(video.metadata.bitrate / 1000)} kbps
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </>
              )}
              
              <Divider />
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Upload Date
                </Typography>
                <Typography variant="body1">
                  {new Date(video.uploaded_at).toLocaleString()}
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" color="text.secondary">
                  Usage Count
                </Typography>
                <Typography variant="body1">
                  Used {video.usage_count} time{video.usage_count !== 1 ? 's' : ''}
                </Typography>
              </Box>
            </Stack>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default VideoPlayer;