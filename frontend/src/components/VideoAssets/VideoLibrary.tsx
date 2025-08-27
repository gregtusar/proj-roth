import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  Chip,
  Stack,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Tooltip,
  Menu,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  PlayArrow as PlayIcon,
  Download as DownloadIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  MoreVert as MoreIcon,
  ContentCopy as CopyIcon,
  Instagram as InstagramIcon,
  VideoLibrary as TikTokIcon,
  Email as EmailIcon,
  CloudDownload
} from '@mui/icons-material';
import apiClient from '../../services/api';
import VideoUpload from './VideoUpload';
import VideoPlayer from './VideoPlayer';

interface VideoAsset {
  id: string;
  title: string;
  description?: string;
  tags: string[];
  campaign?: string;
  status: 'uploading' | 'processing' | 'ready' | 'error';
  thumbnail_url?: string;
  duration?: number;
  uploaded_at: string;
  uploaded_by_email: string;
  versions_count: number;
  usage_count: number;
}

interface VideoDetail extends VideoAsset {
  original_url: string;
  versions: {
    [key: string]: {
      url: string;
      size: number;
      duration?: number;
      resolution?: string;
    };
  };
  metadata?: {
    duration: number;
    resolution: string;
    aspect_ratio: string;
    file_size: number;
  };
}

const VideoLibrary: React.FC = () => {
  const [videos, setVideos] = useState<VideoAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [campaignFilter, setCampaignFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedVideo, setSelectedVideo] = useState<VideoDetail | null>(null);
  const [playerOpen, setPlayerOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuVideo, setMenuVideo] = useState<VideoAsset | null>(null);

  const campaigns = [
    '2024 General Election',
    '2024 Primary',
    'Voter Registration Drive',
    'Get Out The Vote',
    'Issue Awareness',
    'Fundraising'
  ];

  useEffect(() => {
    loadVideos();
  }, [campaignFilter, statusFilter]);

  const loadVideos = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (campaignFilter) params.append('campaign', campaignFilter);
      if (statusFilter) params.append('status', statusFilter);
      
      const data = await apiClient.get<VideoAsset[]>(`/videos/?${params}`);
      setVideos(data);
    } catch (error) {
      console.error('Error loading videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadVideos();
      return;
    }

    try {
      setLoading(true);
      const data = await apiClient.get<VideoAsset[]>(
        `/videos/search?q=${encodeURIComponent(searchQuery)}`
      );
      setVideos(data);
    } catch (error) {
      console.error('Error searching videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadVideoDetail = async (videoId: string) => {
    try {
      const data = await apiClient.get<VideoDetail>(`/videos/${videoId}`);
      setSelectedVideo(data);
    } catch (error) {
      console.error('Error loading video detail:', error);
    }
  };

  const handlePlayVideo = async (video: VideoAsset) => {
    await loadVideoDetail(video.id);
    setPlayerOpen(true);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, video: VideoAsset) => {
    setAnchorEl(event.currentTarget);
    setMenuVideo(video);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuVideo(null);
  };

  const handleDownloadVersion = async (platform: string) => {
    if (!menuVideo) return;
    
    await loadVideoDetail(menuVideo.id);
    if (selectedVideo?.versions[platform]) {
      window.open(selectedVideo.versions[platform].url, '_blank');
    }
    handleMenuClose();
  };

  const handleCopyLink = async () => {
    if (!menuVideo) return;
    
    await loadVideoDetail(menuVideo.id);
    if (selectedVideo) {
      navigator.clipboard.writeText(selectedVideo.original_url);
    }
    handleMenuClose();
  };

  const handleDeleteVideo = async () => {
    if (!menuVideo) return;
    
    try {
      await apiClient.delete(`/videos/${menuVideo.id}`);
      loadVideos();
    } catch (error) {
      console.error('Error deleting video:', error);
    }
    handleMenuClose();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success';
      case 'processing': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Video Assets</Typography>
        <Button
          variant="contained"
          startIcon={<CloudDownload />}
          onClick={() => setUploadOpen(true)}
        >
          Upload Video
        </Button>
      </Box>

      {/* Search and Filters */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              placeholder="Search videos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={4} md={3}>
            <FormControl fullWidth>
              <InputLabel>Campaign</InputLabel>
              <Select
                value={campaignFilter}
                onChange={(e) => setCampaignFilter(e.target.value)}
                label="Campaign"
              >
                <MenuItem value="">All Campaigns</MenuItem>
                {campaigns.map(c => (
                  <MenuItem key={c} value={c}>{c}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4} md={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="ready">Ready</MenuItem>
                <MenuItem value="processing">Processing</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={12} md={3}>
            <Typography variant="body2" color="text.secondary">
              {videos.length} video{videos.length !== 1 ? 's' : ''} found
            </Typography>
          </Grid>
        </Grid>
      </Box>

      {/* Video Grid */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : videos.length === 0 ? (
        <Alert severity="info">
          No videos found. Upload your first video to get started!
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {videos.map(video => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={video.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                  <CardMedia
                    component="img"
                    image={video.thumbnail_url || '/video-placeholder.png'}
                    alt={video.title}
                    sx={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      cursor: video.status === 'ready' ? 'pointer' : 'default'
                    }}
                    onClick={() => video.status === 'ready' && handlePlayVideo(video)}
                  />
                  {video.status === 'ready' && (
                    <IconButton
                      sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        color: 'white',
                        '&:hover': {
                          backgroundColor: 'rgba(0, 0, 0, 0.9)'
                        }
                      }}
                      onClick={() => handlePlayVideo(video)}
                    >
                      <PlayIcon sx={{ fontSize: 40 }} />
                    </IconButton>
                  )}
                  <Box sx={{ position: 'absolute', bottom: 8, right: 8 }}>
                    <Chip
                      label={formatDuration(video.duration)}
                      size="small"
                      sx={{ backgroundColor: 'rgba(0, 0, 0, 0.7)', color: 'white' }}
                    />
                  </Box>
                  <Box sx={{ position: 'absolute', top: 8, left: 8 }}>
                    <Chip
                      label={video.status}
                      size="small"
                      color={getStatusColor(video.status) as any}
                    />
                  </Box>
                </Box>
                
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" noWrap gutterBottom>
                    {video.title}
                  </Typography>
                  {video.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                      }}
                    >
                      {video.description}
                    </Typography>
                  )}
                  <Box sx={{ mt: 1 }}>
                    {video.campaign && (
                      <Chip label={video.campaign} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    )}
                    {video.tags.slice(0, 2).map(tag => (
                      <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                    {video.tags.length > 2 && (
                      <Chip label={`+${video.tags.length - 2}`} size="small" variant="outlined" sx={{ mb: 0.5 }} />
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    {formatDate(video.uploaded_at)} • {video.versions_count} versions
                  </Typography>
                </CardContent>
                
                <CardActions sx={{ justifyContent: 'space-between' }}>
                  <Typography variant="caption" color="text.secondary">
                    Used {video.usage_count} time{video.usage_count !== 1 ? 's' : ''}
                  </Typography>
                  <IconButton
                    size="small"
                    onClick={(e) => handleMenuOpen(e, video)}
                  >
                    <MoreIcon />
                  </IconButton>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleDownloadVersion('original')}>
          <ListItemIcon><DownloadIcon /></ListItemIcon>
          <ListItemText>Download Original</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDownloadVersion('tiktok')}>
          <ListItemIcon><TikTokIcon /></ListItemIcon>
          <ListItemText>Download TikTok Version</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDownloadVersion('instagram_reel')}>
          <ListItemIcon><InstagramIcon /></ListItemIcon>
          <ListItemText>Download Instagram Version</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleDownloadVersion('email')}>
          <ListItemIcon><EmailIcon /></ListItemIcon>
          <ListItemText>Download Email Version</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleCopyLink}>
          <ListItemIcon><CopyIcon /></ListItemIcon>
          <ListItemText>Copy Link</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDeleteVideo}>
          <ListItemIcon><DeleteIcon /></ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Video Player Dialog */}
      {selectedVideo && (
        <VideoPlayer
          open={playerOpen}
          onClose={() => setPlayerOpen(false)}
          video={selectedVideo}
        />
      )}

      {/* Upload Dialog */}
      <Dialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Upload Videos</DialogTitle>
        <DialogContent>
          <VideoUpload
            onUploadComplete={() => {
              loadVideos();
              setUploadOpen(false);
            }}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default VideoLibrary;