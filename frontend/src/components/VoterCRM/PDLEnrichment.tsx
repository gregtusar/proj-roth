import React, { useState } from 'react';
import { styled } from 'baseui';
import { Button } from 'baseui/button';
import { Spinner } from 'baseui/spinner';
import { Tag } from 'baseui/tag';
import { ArrowLeft, ChevronDown, ChevronRight } from 'baseui/icon';
import { Accordion, Panel } from 'baseui/accordion';
import PDLDataViewer from './PDLDataViewer';

const Container = styled('div', {
  padding: '24px',
});

const Header = styled('div', {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '24px',
});

const Title = styled('h3', ({ $theme }) => ({
  fontSize: '18px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  margin: 0,
}));

const Section = styled('div', ({ $theme }) => ({
  marginBottom: '24px',
  padding: '16px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  border: `1px solid ${$theme.colors.borderOpaque}`,
}));

const SectionTitle = styled('h4', ({ $theme }) => ({
  fontSize: '16px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  marginBottom: '16px',
}));

const InfoGrid = styled('div', {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
  gap: '16px',
});

const InfoItem = styled('div', ({ $theme }) => ({
  padding: '12px',
  backgroundColor: $theme.colors.backgroundTertiary,
  borderRadius: '6px',
}));

const InfoLabel = styled('div', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.contentSecondary,
  marginBottom: '4px',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

const InfoValue = styled('div', ({ $theme }) => ({
  fontSize: '14px',
  color: $theme.colors.contentPrimary,
  fontWeight: 500,
}));

const NoDataMessage = styled('div', ({ $theme }) => ({
  padding: '40px',
  textAlign: 'center',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  color: $theme.colors.contentSecondary,
  fontSize: '14px',
}));

const LoadingContainer = styled('div', {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  padding: '40px',
});

const JsonDisplay = styled('pre', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.contentPrimary,
  backgroundColor: $theme.colors.backgroundTertiary,
  padding: '16px',
  borderRadius: '6px',
  overflow: 'auto',
  maxHeight: '400px',
  fontFamily: 'monospace',
  lineHeight: 1.5,
}));

const ScrollableInfoSection = styled('div', ({ $theme }) => ({
  maxHeight: '500px',
  overflowY: 'auto',
  padding: '16px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  border: `1px solid ${$theme.colors.borderOpaque}`,
  '&::-webkit-scrollbar': {
    width: '8px',
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: $theme.colors.backgroundTertiary,
    borderRadius: '4px',
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: $theme.colors.contentTertiary,
    borderRadius: '4px',
    ':hover': {
      backgroundColor: $theme.colors.contentSecondary,
    },
  },
}));

const RawDataToggle = styled('button', ({ $theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
  background: 'none',
  border: 'none',
  color: $theme.colors.primary,
  fontSize: '14px',
  fontWeight: 500,
  cursor: 'pointer',
  padding: '8px 0',
  marginBottom: '12px',
  ':hover': {
    opacity: 0.8,
  },
}));

const StatusBadge = styled('div', {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '8px',
});

interface PDLEnrichmentProps {
  enrichmentData: any;
  onRefresh: () => void;
}

const PDLEnrichment: React.FC<PDLEnrichmentProps> = ({ enrichmentData, onRefresh }) => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  };

  const [showRawData, setShowRawData] = useState(false);
  
  const renderEnrichmentData = () => {
    if (!enrichmentData) {
      return (
        <NoDataMessage>
          <p>No PDL enrichment data available</p>
          <p style={{ fontSize: '12px', marginTop: '8px', opacity: 0.8 }}>
            People Data Labs enrichment provides professional and contact information
          </p>
          <Button
            onClick={handleRefresh}
            startEnhancer={<ArrowLeft size={20} />}
            kind="secondary"
            style={{ marginTop: '16px' }}
          >
            Fetch Enrichment Data ($0.25)
          </Button>
        </NoDataMessage>
      );
    }
    
    // If enrichmentData is a string, try to parse it
    let parsedEnrichmentData = enrichmentData;
    if (typeof enrichmentData === 'string') {
      try {
        parsedEnrichmentData = JSON.parse(enrichmentData);
      } catch (e) {
        // If it's not valid JSON, show error message
        return (
          <NoDataMessage>
            <p>Error: Invalid PDL data format</p>
            <p style={{ fontSize: '12px', marginTop: '8px', opacity: 0.8 }}>
              The PDL data could not be parsed. Please refresh to try again.
            </p>
            <Button
              onClick={handleRefresh}
              startEnhancer={<ArrowLeft size={20} />}
              kind="secondary"
              style={{ marginTop: '16px' }}
            >
              Refresh Data
            </Button>
          </NoDataMessage>
        );
      }
    }
    
    // Use parsed data from here on
    enrichmentData = parsedEnrichmentData;

    // Extract key information from PDL data
    const {
      pdl_id,
      likelihood,
      has_email,
      has_phone,
      has_linkedin,
      has_job_info,
      has_education,
      pdl_data: rawPdlData,
    } = enrichmentData;
    
    // Parse pdl_data if it's a string
    let pdl_data: any = {};
    if (rawPdlData) {
      if (typeof rawPdlData === 'string') {
        try {
          pdl_data = JSON.parse(rawPdlData);
        } catch (e) {
          console.error('Failed to parse PDL data:', e);
          pdl_data = {};
        }
      } else {
        pdl_data = rawPdlData;
      }
    }

    const emails = pdl_data.emails || [];
    const phones = pdl_data.phone_numbers || [];
    const profiles = pdl_data.profiles || [];
    const job = pdl_data.job || {};
    const education = pdl_data.education || [];

    return (
      <ScrollableInfoSection>
        {/* Status Section */}
        <Section>
          <SectionTitle>Enrichment Status</SectionTitle>
          <InfoGrid>
            <InfoItem>
              <InfoLabel>PDL ID</InfoLabel>
              <InfoValue>{pdl_id || 'N/A'}</InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Match Likelihood</InfoLabel>
              <InfoValue>
                {likelihood && (
                  <Tag 
                    closeable={false} 
                    kind={likelihood >= 8 ? 'positive' : likelihood >= 5 ? 'warning' : 'negative'}
                  >
                    {likelihood}/10
                  </Tag>
                )}
              </InfoValue>
            </InfoItem>
            <InfoItem>
              <InfoLabel>Data Availability</InfoLabel>
              <InfoValue>
                <StatusBadge>
                  {has_email && <Tag closeable={false} kind="positive" overrides={{ Root: { style: { marginRight: '4px', marginBottom: '4px' } } }}>Email</Tag>}
                  {has_phone && <Tag closeable={false} kind="positive" overrides={{ Root: { style: { marginRight: '4px', marginBottom: '4px' } } }}>Phone</Tag>}
                  {has_linkedin && <Tag closeable={false} kind="positive" overrides={{ Root: { style: { marginRight: '4px', marginBottom: '4px' } } }}>LinkedIn</Tag>}
                  {has_job_info && <Tag closeable={false} kind="positive" overrides={{ Root: { style: { marginRight: '4px', marginBottom: '4px' } } }}>Job</Tag>}
                  {has_education && <Tag closeable={false} kind="positive" overrides={{ Root: { style: { marginRight: '4px', marginBottom: '4px' } } }}>Education</Tag>}
                </StatusBadge>
              </InfoValue>
            </InfoItem>
          </InfoGrid>
        </Section>

        {/* Contact Information */}
        {(emails.length > 0 || phones.length > 0) && (
          <Section>
            <SectionTitle>Contact Information</SectionTitle>
            <InfoGrid>
              {emails.length > 0 && (
                <InfoItem>
                  <InfoLabel>Emails</InfoLabel>
                  <InfoValue>
                    {emails.map((email: any, idx: number) => (
                      <div key={idx} style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>{typeof email === 'string' ? email : (email.address || email)}</span>
                        {email.type && (
                          <Tag 
                            closeable={false} 
                            kind="neutral" 
                            overrides={{ Root: { style: { height: '20px', fontSize: '11px' } } }}
                          >
                            {email.type}
                          </Tag>
                        )}
                      </div>
                    ))}
                  </InfoValue>
                </InfoItem>
              )}
              {phones.length > 0 && (
                <InfoItem>
                  <InfoLabel>Phone Numbers</InfoLabel>
                  <InfoValue>
                    {phones.map((phone: any, idx: number) => (
                      <div key={idx} style={{ marginBottom: '4px' }}>
                        {typeof phone === 'string' ? phone : (phone.number || phone)}
                      </div>
                    ))}
                  </InfoValue>
                </InfoItem>
              )}
            </InfoGrid>
          </Section>
        )}

        {/* Professional Information */}
        {job && Object.keys(job).length > 0 && (
          <Section>
            <SectionTitle>Professional Information</SectionTitle>
            <InfoGrid>
              {job.title && (
                <InfoItem>
                  <InfoLabel>Job Title</InfoLabel>
                  <InfoValue>{job.title}</InfoValue>
                </InfoItem>
              )}
              {job.company && (
                <InfoItem>
                  <InfoLabel>Company</InfoLabel>
                  <InfoValue>{job.company}</InfoValue>
                </InfoItem>
              )}
              {job.industry && (
                <InfoItem>
                  <InfoLabel>Industry</InfoLabel>
                  <InfoValue>{job.industry}</InfoValue>
                </InfoItem>
              )}
            </InfoGrid>
          </Section>
        )}

        {/* Social Profiles */}
        {profiles.length > 0 && (
          <Section>
            <SectionTitle>Social Profiles</SectionTitle>
            <InfoGrid>
              {profiles.map((profile: any, idx: number) => (
                <InfoItem key={idx}>
                  <InfoLabel>{profile.network || 'Profile'}</InfoLabel>
                  <InfoValue>
                    <a 
                      href={profile.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{ color: 'inherit', textDecoration: 'underline' }}
                    >
                      {profile.username || profile.url}
                    </a>
                  </InfoValue>
                </InfoItem>
              ))}
            </InfoGrid>
          </Section>
        )}

        {/* Education */}
        {education.length > 0 && (
          <Section>
            <SectionTitle>Education</SectionTitle>
            <InfoGrid>
              {education.map((edu: any, idx: number) => (
                <InfoItem key={idx}>
                  <InfoLabel>{edu.degree || 'Degree'}</InfoLabel>
                  <InfoValue>
                    {edu.school}
                    {edu.end_date && ` (${edu.end_date})`}
                  </InfoValue>
                </InfoItem>
              ))}
            </InfoGrid>
          </Section>
        )}

        {/* Raw Data with Pretty Viewer */}
        <Section>
          <RawDataToggle onClick={() => setShowRawData(!showRawData)}>
            {showRawData ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
            View Raw PDL Data
          </RawDataToggle>
          {showRawData && (
            <PDLDataViewer data={pdl_data} />
          )}
        </Section>
      </ScrollableInfoSection>
    );
  };

  return (
    <Container>
      <Header>
        <Title>PDL Enrichment Data</Title>
        <Button
          onClick={handleRefresh}
          isLoading={isRefreshing}
          startEnhancer={<ArrowLeft size={20} />}
          kind="secondary"
          size="compact"
        >
          Refresh Data
        </Button>
      </Header>

      {isRefreshing ? (
        <LoadingContainer>
          <Spinner />
        </LoadingContainer>
      ) : (
        renderEnrichmentData()
      )}
    </Container>
  );
};

export default PDLEnrichment;