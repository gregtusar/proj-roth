import React, { useState } from 'react';
import { styled } from 'baseui';
import { Button } from 'baseui/button';
import { Spinner } from 'baseui/spinner';
import { Tag } from 'baseui/tag';
import { ArrowLeft, ChevronDown, ChevronRight } from 'baseui/icon';
import { Accordion, Panel } from 'baseui/accordion';

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

const Section = styled('div', () => ({
  marginBottom: '32px',
  padding: '20px',
  backgroundColor: '#f5f5f5',
  borderRadius: '8px',
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
          <Button
            onClick={handleRefresh}
            startEnhancer={<ArrowLeft size={20} />}
            kind="secondary"
            style={{ marginTop: '16px' }}
          >
            Fetch Enrichment Data
          </Button>
        </NoDataMessage>
      );
    }

    // Extract key information from PDL data
    const {
      pdl_id,
      likelihood,
      has_email,
      has_phone,
      has_linkedin,
      has_job_info,
      has_education,
      pdl_data = {},
    } = enrichmentData;

    const emails = pdl_data.emails || [];
    const phones = pdl_data.phone_numbers || [];
    const profiles = pdl_data.profiles || [];
    const job = pdl_data.job || {};
    const education = pdl_data.education || [];

    return (
      <>
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
                  {has_email && <Tag closeable={false} kind="positive">Email</Tag>}
                  {has_phone && <Tag closeable={false} kind="positive">Phone</Tag>}
                  {has_linkedin && <Tag closeable={false} kind="positive">LinkedIn</Tag>}
                  {has_job_info && <Tag closeable={false} kind="positive">Job</Tag>}
                  {has_education && <Tag closeable={false} kind="positive">Education</Tag>}
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
                      <div key={idx}>
                        {email.address}
                        {email.type && <Tag closeable={false} kind="neutral">{email.type}</Tag>}
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
                      <div key={idx}>{phone}</div>
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
                    <a href={profile.url} target="_blank" rel="noopener noreferrer">
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

        {/* Raw Data (collapsible) */}
        <Section>
          <RawDataToggle onClick={() => setShowRawData(!showRawData)}>
            {showRawData ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
            View Raw PDL Data
          </RawDataToggle>
          {showRawData && (
            <JsonDisplay>{JSON.stringify(pdl_data, null, 2)}</JsonDisplay>
          )}
        </Section>
      </>
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