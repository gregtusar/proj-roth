import React from 'react';
import { useAuthCheck } from '../../hooks/useAuthCheck';
import VideoLibrary from './VideoLibrary';

const VideoAssets: React.FC = () => {
  useAuthCheck();
  
  return <VideoLibrary />;
};

export default VideoAssets;