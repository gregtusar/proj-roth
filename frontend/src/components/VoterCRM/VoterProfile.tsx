import React, { useState, useEffect } from 'react';
import { styled } from 'baseui';
import { Tabs, Tab } from 'baseui/tabs';
import { Button } from 'baseui/button';
import { Spinner } from 'baseui/spinner';
import axios from 'axios';
import { SectionTitle, Caption, ErrorText } from '../Common/Typography';
import BasicInfo from './BasicInfo';
import VotingHistory from './VotingHistory';
import DonationHistory from './DonationHistory';
import EventsSection from './EventsSection';
import PDLEnrichment from './PDLEnrichment';

const Container = styled('div', {
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
});

const Header = styled('div', ({ $theme }) => ({
  padding: '0 0 16px 0',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
}));

const HeaderInfo = styled('div', {
  flex: 1,
});

const VoterName = styled(SectionTitle, {
  margin: 0,
});

const VoterId = styled(Caption, {
  marginTop: '4px',
});

const ContentArea = styled('div', {
  flex: 1,
  overflow: 'auto',
  padding: '24px 0',
});

const LoadingContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '400px',
});

const ErrorContainer = styled('div', {
  padding: '20px',
  textAlign: 'center',
});

interface VoterProfileProps {
  masterId: string;
  onClose: () => void;
}

const VoterProfile: React.FC<VoterProfileProps> = ({ masterId, onClose }) => {
  const [activeKey, setActiveKey] = useState('0');
  const [profile, setProfile] = useState<any>(null);
  const [votingHistory, setVotingHistory] = useState<any>(null);
  const [donationHistory, setDonationHistory] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<any>(null);

  useEffect(() => {
    loadVoterData();
  }, [masterId]);

  const loadVoterData = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: `Bearer ${token}` };

      // Load all data in parallel
      const [profileRes, votingRes, donationRes, eventsRes] = await Promise.all([
        axios.get(`/api/crm/voter/${masterId}`, { headers }),
        axios.get(`/api/crm/voting-history/${masterId}`, { headers }),
        axios.get(`/api/crm/donation-history/${masterId}`, { headers }),
        axios.get(`/api/crm/events/${masterId}`, { headers }),
      ]);

      setProfile(profileRes.data);
      setVotingHistory(votingRes.data);
      setDonationHistory(donationRes.data);
      setEvents(eventsRes.data);

      // Trigger search for additional information
      triggerAgentSearch(profileRes.data);
    } catch (err: any) {
      console.error('Error loading voter data:', err);
      setError(err.response?.data?.detail || 'Failed to load voter data');
    } finally {
      setLoading(false);
    }
  };

  const triggerAgentSearch = async (voterProfile: any) => {
    try {
      const token = localStorage.getItem('access_token');
      const searchQuery = `Find all available information about ${voterProfile.basic_info.name.first} ${voterProfile.basic_info.name.last} from ${voterProfile.current_address.city}, NJ`;
      
      // Use the agent to search and analyze information
      const response = await axios.post(
        '/api/agent/search',
        { 
          query: searchQuery,
          analyze: true  // Request AI analysis of results
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data) {
        setSearchResults(response.data);
      }
    } catch (err) {
      console.error('Error fetching search results:', err);
      setSearchResults({ error: 'Unable to fetch additional information' });
    }
  };


  const handleEventAdded = (newEvent: any) => {
    setEvents([newEvent, ...events]);
  };

  const handlePDLRefresh = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await axios.post(
        `/api/crm/enrich/${masterId}`,
        { force: true },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Reload profile to get updated PDL data
      loadVoterData();
    } catch (err) {
      console.error('Error refreshing PDL data:', err);
    }
  };

  if (loading) {
    return (
      <LoadingContainer>
        <Spinner />
      </LoadingContainer>
    );
  }

  if (error) {
    return (
      <ErrorContainer>
        <ErrorText>{error}</ErrorText>
      </ErrorContainer>
    );
  }

  if (!profile) {
    return (
      <ErrorContainer>
        <ErrorText>No profile data available</ErrorText>
      </ErrorContainer>
    );
  }

  const voterName = `${profile.basic_info.name.last}, ${profile.basic_info.name.first} ${profile.basic_info.name.middle || ''}`.trim();

  return (
    <Container>
      <Header>
        <HeaderInfo>
          <VoterName>{voterName}</VoterName>
          <VoterId>Master ID: {masterId}</VoterId>
        </HeaderInfo>
        <Button onClick={onClose} kind="secondary">
          Dismiss
        </Button>
      </Header>

      <ContentArea>
        <Tabs
          activeKey={activeKey}
          onChange={({ activeKey }) => setActiveKey(activeKey as string)}
        >
          <Tab title="Basic Info">
            <BasicInfo 
              profile={profile} 
              searchResults={searchResults}
            />
          </Tab>
          
          <Tab title="Voting History">
            <VotingHistory history={votingHistory} />
          </Tab>
          
          <Tab title="Donations">
            <DonationHistory history={donationHistory} />
          </Tab>
          
          <Tab title="PDL Enrichment">
            <PDLEnrichment 
              enrichmentData={profile.pdl_enrichment}
              onRefresh={handlePDLRefresh}
            />
          </Tab>
          
          <Tab title="Events">
            <EventsSection 
              events={events}
              masterId={masterId}
              onEventAdded={handleEventAdded}
            />
          </Tab>
        </Tabs>
      </ContentArea>
    </Container>
  );
};

export default VoterProfile;