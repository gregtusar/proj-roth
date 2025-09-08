import React, { useState, useCallback } from 'react';
import { styled } from 'baseui';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import VoterSearch from './VoterSearch';
import VoterProfile from './VoterProfile';
import { Modal, ModalHeader, ModalBody, ROLE, SIZE } from 'baseui/modal';

const Container = styled('div', ({ $theme }) => ({
  padding: '24px',
  backgroundColor: $theme.colors.backgroundPrimary,
  minHeight: '100vh',
}));

const Title = styled('h1', ({ $theme }) => ({
  fontSize: '28px',
  fontWeight: 600,
  marginBottom: '24px',
  color: $theme.colors.contentPrimary,
}));

const SearchSection = styled('div', ({ $theme }) => ({
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  padding: '24px',
  marginBottom: '24px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
}));

export interface VoterSearchResult {
  master_id: string;
  name: string;
  address: string;
  age?: number;
  party?: string;
}

const VoterCRM: React.FC = () => {
  const { isDarkMode } = useSelector((state: RootState) => state.settings);
  const [selectedVoter, setSelectedVoter] = useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  const handleVoterSelect = useCallback((voter: VoterSearchResult) => {
    setSelectedVoter(voter.master_id);
    setIsProfileOpen(true);
  }, []);

  const handleCloseProfile = useCallback(() => {
    setIsProfileOpen(false);
    // Keep selectedVoter for a moment to avoid flash during close animation
    setTimeout(() => setSelectedVoter(null), 300);
  }, []);

  return (
    <Container>
      <Title>Voter CRM</Title>
      
      <SearchSection>
        <VoterSearch onSelectVoter={handleVoterSelect} />
      </SearchSection>

      <Modal
        onClose={handleCloseProfile}
        isOpen={isProfileOpen}
        animate
        autoFocus
        size={SIZE.full}
        role={ROLE.dialog}
        overrides={{
          Root: {
            style: {
              zIndex: 1000,
            },
          },
          Dialog: {
            style: () => ({
              backgroundColor: isDarkMode ? '#1f2937' : '#ffffff',
              maxWidth: '95vw',
              width: '1400px',
              height: '90vh',
              margin: '5vh auto',
              display: 'flex',
              flexDirection: 'column',
            }),
          },
        }}
      >
        <ModalHeader>Voter Profile</ModalHeader>
        <ModalBody>
          {selectedVoter && (
            <VoterProfile 
              masterId={selectedVoter} 
              onClose={handleCloseProfile}
            />
          )}
        </ModalBody>
      </Modal>
    </Container>
  );
};

export default VoterCRM;