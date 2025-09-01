import React from 'react';
import { useAuthCheck } from '../../hooks/useAuthCheck';
import DocumentLibrary from './DocumentLibrary';

const DocumentAssets: React.FC = () => {
  useAuthCheck();
  
  return <DocumentLibrary />;
};

export default DocumentAssets;