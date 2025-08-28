import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Chip,
  LinearProgress,
  Alert,
  Stack,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  VideoLibrary as VideoIcon,
  Close as CloseIcon,
  Add as AddIcon
} from '@mui/icons-material';
import apiClient from '../../services/api';

interface VideoUploadProps {
  onUploadComplete?: (videoId: string) => void;
  onClose?: () => void;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'complete' | 'error';
  error?: string;
  videoId?: string;
}

const VideoUpload: React.FC<VideoUploadProps> = ({ onUploadComplete, onClose }) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [metadataDialog, setMetadataDialog] = useState<{
    open: boolean;
    file: File | null;
    gcsPath?: string;
  }>({ open: false, file: null });
  
  // Metadata form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [campaign, setCampaign] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  
  const campaigns = [
    '2024 General Election',
    '2024 Primary',
    'Voter Registration Drive',
    'Get Out The Vote',
    'Issue Awareness',
    'Fundraising'
  ];

  const onDrop = useCallback((acceptedFiles: File[]) => {
    // Filter for video files only
    const videoFiles = acceptedFiles.filter(file => file.type.startsWith('video/'));
    
    if (videoFiles.length === 0) {
      return;
    }

    // For single file, show metadata dialog
    if (videoFiles.length === 1) {
      const file = videoFiles[0];
      setTitle(file.name.replace(/\.[^/.]+$/, '')); // Remove extension
      setMetadataDialog({ open: true, file });
    } else {
      // For multiple files, upload with default metadata
      videoFiles.forEach(file => {
        uploadFile(file, {
          title: file.name.replace(/\.[^/.]+$/, ''),
          tags: [],
          campaign: ''
        });
      });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
    },
    maxSize: 500 * 1024 * 1024 // 500MB
  });

  const uploadFile = async (
    file: File,
    metadata: { title: string; description?: string; tags: string[]; campaign?: string }
  ) => {
    const uploadId = Date.now().toString();
    const newUpload: UploadingFile = {
      file,
      progress: 0,
      status: 'pending'
    };

    setUploadingFiles(prev => [...prev, newUpload]);

    try {
      // Step 1: Get signed upload URL
      newUpload.status = 'uploading';
      setUploadingFiles(prev => 
        prev.map(u => u.file === file ? { ...u, status: 'uploading' } : u)
      );

      const uploadUrlResponse = await apiClient.post<{
        upload_url: string;
        gcs_path: string;
        expires_in: number;
        proxy_endpoint?: string;
        error_fallback?: boolean;
      }>('/videos/upload-url', {
        filename: file.name,
        content_type: file.type
      });

      // Step 2: Upload file - either directly to GCS or via proxy
      if (uploadUrlResponse.upload_url === 'USE_PROXY_UPLOAD') {
        // Use proxy upload endpoint
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', metadata.title);
        formData.append('description', metadata.description || '');
        formData.append('tags', metadata.tags.join(','));
        if (metadata.campaign) {
          formData.append('campaign', metadata.campaign);
        }

        const xhr = new XMLHttpRequest();
        
        const proxyResponse = await new Promise<any>((resolve, reject) => {
          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const progress = Math.round((e.loaded / e.total) * 100);
              setUploadingFiles(prev =>
                prev.map(u => u.file === file ? { ...u, progress } : u)
              );
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
              try {
                const response = JSON.parse(xhr.responseText);
                resolve(response);
              } catch (e) {
                reject(new Error('Failed to parse server response'));
              }
            } else {
              reject(new Error(`Upload failed with status ${xhr.status}`));
            }
          });

          xhr.addEventListener('error', () => reject(new Error('Upload failed')));

          // Get auth token for proxy upload
          const token = localStorage.getItem('auth_token');
          
          xhr.open('POST', '/api/videos/upload-file');
          if (token) {
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          }
          xhr.send(formData);
        });
        
        // Mark as complete (proxy endpoint handles everything)
        setUploadingFiles(prev =>
          prev.map(u => u.file === file 
            ? { ...u, status: 'complete', videoId: proxyResponse.id }
            : u
          )
        );

        if (onUploadComplete) {
          onUploadComplete(proxyResponse.id);
        }
        
        return; // Exit early, proxy handled everything
        
      } else {
        // Original direct upload to GCS
        const xhr = new XMLHttpRequest();
        
        await new Promise<void>((resolve, reject) => {
          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const progress = Math.round((e.loaded / e.total) * 100);
              setUploadingFiles(prev =>
                prev.map(u => u.file === file ? { ...u, progress } : u)
              );
            }
          });

          xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
              resolve();
            } else {
              reject(new Error(`Upload failed with status ${xhr.status}`));
            }
          });

          xhr.addEventListener('error', () => reject(new Error('Upload failed')));

          xhr.open('PUT', uploadUrlResponse.upload_url);
          xhr.setRequestHeader('Content-Type', file.type);
          xhr.send(file);
        });
      }

      // Step 3: Create video asset record
      setUploadingFiles(prev =>
        prev.map(u => u.file === file ? { ...u, status: 'processing', progress: 100 } : u)
      );

      const createResponse = await apiClient.post<{
        id: string;
        status: string;
        message: string;
      }>('/videos/', {
        title: metadata.title,
        description: metadata.description,
        tags: metadata.tags,
        campaign: metadata.campaign,
        gcs_path: uploadUrlResponse.gcs_path,
        original_filename: file.name
      });

      // Mark as complete
      setUploadingFiles(prev =>
        prev.map(u => u.file === file 
          ? { ...u, status: 'complete', videoId: createResponse.id }
          : u
        )
      );

      if (onUploadComplete) {
        onUploadComplete(createResponse.id);
      }

    } catch (error: any) {
      console.error('Upload error:', error);
      setUploadingFiles(prev =>
        prev.map(u => u.file === file 
          ? { ...u, status: 'error', error: error.message || 'Upload failed' }
          : u
        )
      );
    }
  };

  const handleMetadataSubmit = () => {
    if (!metadataDialog.file || !title.trim()) return;

    uploadFile(metadataDialog.file, {
      title: title.trim(),
      description: description.trim(),
      tags,
      campaign
    });

    // Reset form
    setMetadataDialog({ open: false, file: null });
    setTitle('');
    setDescription('');
    setTags([]);
    setCampaign('');
    setTagInput('');
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB';
    return Math.round(bytes / 1048576) + ' MB';
  };

  const hasActiveUploads = uploadingFiles.some(
    u => u.status === 'uploading' || u.status === 'processing'
  );

  return (
    <Box>
      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          transition: 'all 0.3s',
          '&:hover': {
            backgroundColor: 'action.hover',
            borderColor: 'primary.main'
          }
        }}
      >
        <input {...getInputProps()} />
        <VideoIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop videos here' : 'Drag & drop videos here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          or
        </Typography>
        <Button variant="contained" startIcon={<UploadIcon />}>
          Browse Files
        </Button>
        <Typography variant="caption" display="block" sx={{ mt: 2 }}>
          Supported formats: MP4, MOV, AVI, MKV, WebM • Max size: 500MB
        </Typography>
      </Paper>

      {uploadingFiles.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Uploads ({uploadingFiles.length})
          </Typography>
          <Stack spacing={2}>
            {uploadingFiles.map((upload, index) => (
              <Paper key={index} sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <VideoIcon sx={{ mr: 2, color: 'action.active' }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body1">
                      {upload.file.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatFileSize(upload.file.size)}
                    </Typography>
                  </Box>
                  <Chip
                    label={upload.status}
                    size="small"
                    color={
                      upload.status === 'complete' ? 'success' :
                      upload.status === 'error' ? 'error' :
                      upload.status === 'processing' ? 'warning' :
                      'default'
                    }
                  />
                </Box>
                
                {(upload.status === 'uploading' || upload.status === 'processing') && (
                  <LinearProgress
                    variant={upload.status === 'processing' ? 'indeterminate' : 'determinate'}
                    value={upload.progress}
                    sx={{ mt: 1 }}
                  />
                )}
                
                {upload.error && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    {upload.error}
                  </Alert>
                )}
                
                {upload.status === 'complete' && (
                  <Alert severity="success" sx={{ mt: 1 }}>
                    Video uploaded successfully! Processing will continue in the background.
                  </Alert>
                )}
              </Paper>
            ))}
          </Stack>
        </Box>
      )}

      {/* Metadata Dialog */}
      <Dialog
        open={metadataDialog.open}
        onClose={() => !hasActiveUploads && setMetadataDialog({ open: false, file: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Video Details
          <IconButton
            onClick={() => setMetadataDialog({ open: false, file: null })}
            sx={{ position: 'absolute', right: 8, top: 8 }}
            disabled={hasActiveUploads}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              fullWidth
              required
              helperText="Give your video a descriptive title"
            />
            
            <TextField
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              fullWidth
              multiline
              rows={3}
              helperText="Optional description of the video content"
            />
            
            <FormControl fullWidth>
              <InputLabel>Campaign</InputLabel>
              <Select
                value={campaign}
                onChange={(e) => setCampaign(e.target.value)}
                label="Campaign"
              >
                <MenuItem value="">None</MenuItem>
                {campaigns.map(c => (
                  <MenuItem key={c} value={c}>{c}</MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Box>
              <TextField
                label="Add tags"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddTag())}
                fullWidth
                InputProps={{
                  endAdornment: (
                    <IconButton onClick={handleAddTag} size="small">
                      <AddIcon />
                    </IconButton>
                  )
                }}
                helperText="Press Enter to add tags"
              />
              <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {tags.map(tag => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => handleRemoveTag(tag)}
                    size="small"
                  />
                ))}
              </Box>
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setMetadataDialog({ open: false, file: null })}
            disabled={hasActiveUploads}
          >
            Cancel
          </Button>
          <Button
            onClick={handleMetadataSubmit}
            variant="contained"
            disabled={!title.trim() || hasActiveUploads}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default VideoUpload;