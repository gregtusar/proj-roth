import React from 'react';
import { styled } from 'baseui';
import { Tag } from 'baseui/tag';

const Section = styled('div', () => ({
  marginBottom: '32px',
}));

const SectionTitle = styled('h3', ({ $theme }) => ({
  fontSize: '18px',
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
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
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

const AddressHistory = styled('div', ({ $theme }) => ({
  marginTop: '16px',
  padding: '12px',
  backgroundColor: $theme.colors.backgroundTertiary,
  borderRadius: '8px',
}));

const AddressItem = styled('div', ({ $theme }) => ({
  padding: '8px 0',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  ':last-child': {
    borderBottom: 'none',
  },
}));

const SearchResults = styled('div', ({ $theme }) => ({
  marginTop: '16px',
  padding: '16px',
  backgroundColor: $theme.colors.backgroundTertiary,
  borderRadius: '8px',
  fontSize: '14px',
  lineHeight: 1.6,
  color: $theme.colors.contentPrimary,
  maxHeight: '400px',
  overflow: 'auto',
}));

const AgentSummary = styled('div', ({ $theme }) => ({
  padding: '16px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  marginBottom: '16px',
  fontSize: '14px',
  lineHeight: 1.8,
  color: $theme.colors.contentPrimary,
  whiteSpace: 'pre-wrap',
}));

const SourcesSection = styled('details', ({ $theme }) => ({
  marginTop: '16px',
  padding: '12px',
  backgroundColor: $theme.colors.backgroundTertiary,
  borderRadius: '6px',
  cursor: 'pointer',
  '& summary': {
    fontSize: '13px',
    fontWeight: 600,
    color: $theme.colors.contentSecondary,
    userSelect: 'none',
    ':hover': {
      color: $theme.colors.contentPrimary,
    },
  },
}));

const SearchResultItem = styled('div', ({ $theme }) => ({
  marginBottom: '12px',
  paddingBottom: '12px',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  ':last-child': {
    borderBottom: 'none',
    marginBottom: 0,
    paddingBottom: 0,
  },
}));

const SearchResultTitle = styled('div', ({ $theme }) => ({
  fontSize: '14px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  marginBottom: '4px',
}));

const SearchResultSnippet = styled('div', ({ $theme }) => ({
  fontSize: '13px',
  color: $theme.colors.contentSecondary,
  lineHeight: 1.5,
}));

const SearchResultLink = styled('a', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.primary,
  textDecoration: 'none',
  ':hover': {
    textDecoration: 'underline',
  },
}));

interface BasicInfoProps {
  profile: any;
  searchResults?: any;
}

const BasicInfo: React.FC<BasicInfoProps> = ({ profile, searchResults }) => {
  const { basic_info, current_address, address_history } = profile;

  const getPartyColor = (party: string) => {
    switch (party?.toUpperCase()) {
      case 'DEM':
      case 'DEMOCRATIC':
        return 'blue';
      case 'REP':
      case 'REPUBLICAN':
        return 'red';
      case 'UNA':
      case 'UNAFFILIATED':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  return (
    <>
      <Section>
        <SectionTitle>Personal Information</SectionTitle>
        <InfoGrid>
          <InfoItem>
            <InfoLabel>Full Name</InfoLabel>
            <InfoValue>
              {basic_info.name.first} {basic_info.name.middle} {basic_info.name.last}
              {basic_info.name.suffix && ` ${basic_info.name.suffix}`}
            </InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Age</InfoLabel>
            <InfoValue>{basic_info.age || 'N/A'}</InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Race/Ethnicity</InfoLabel>
            <InfoValue>{basic_info.race || 'N/A'}</InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Party Affiliation</InfoLabel>
            <InfoValue>
              {basic_info.party && (
                <Tag
                  closeable={false}
                  kind={getPartyColor(basic_info.party)}
                >
                  {basic_info.party}
                </Tag>
              )}
            </InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Registration Date</InfoLabel>
            <InfoValue>{basic_info.registration_date || 'N/A'}</InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Voter Status</InfoLabel>
            <InfoValue>{basic_info.voter_status || 'Active'}</InfoValue>
          </InfoItem>
          
          {basic_info.email && (
            <InfoItem>
              <InfoLabel>Email</InfoLabel>
              <InfoValue>{basic_info.email}</InfoValue>
            </InfoItem>
          )}
        </InfoGrid>
      </Section>

      <Section>
        <SectionTitle>Current Address</SectionTitle>
        <InfoGrid>
          <InfoItem>
            <InfoLabel>Street Address</InfoLabel>
            <InfoValue>
              {current_address.line1}
              {current_address.line2 && <><br />{current_address.line2}</>}
            </InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>City, State ZIP</InfoLabel>
            <InfoValue>
              {current_address.city}, {current_address.state} {current_address.zip}
            </InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>County</InfoLabel>
            <InfoValue>{current_address.county || 'N/A'}</InfoValue>
          </InfoItem>
          
          <InfoItem>
            <InfoLabel>Municipality</InfoLabel>
            <InfoValue>{current_address.municipality || 'N/A'}</InfoValue>
          </InfoItem>
        </InfoGrid>
      </Section>

      {address_history && address_history.length > 1 && (
        <Section>
          <SectionTitle>Address History</SectionTitle>
          <AddressHistory>
            {address_history.map((addr: any, index: number) => (
              <AddressItem key={index}>
                <InfoValue>
                  {addr.addr_residential_line1}, {addr.addr_residential_city}, {addr.addr_residential_state} {addr.addr_residential_zip}
                </InfoValue>
                <InfoLabel style={{ marginTop: '4px' }}>
                  {addr.first_seen && `First seen: ${new Date(addr.first_seen).toLocaleDateString()}`}
                  {addr.last_seen && ` | Last seen: ${new Date(addr.last_seen).toLocaleDateString()}`}
                </InfoLabel>
              </AddressItem>
            ))}
          </AddressHistory>
        </Section>
      )}

      {searchResults && (
        <Section>
          <SectionTitle>Additional Information</SectionTitle>
          {(() => {
            // Handle different response formats
            if (typeof searchResults === 'string') {
              return (
                <SearchResults>
                  <div>{searchResults}</div>
                </SearchResults>
              );
            }
            
            if (searchResults.error) {
              return (
                <SearchResults>
                  <InfoLabel style={{ color: 'inherit' }}>
                    Unable to fetch additional information at this time.
                  </InfoLabel>
                </SearchResults>
              );
            }
            
            // If we have an agent summary, display it prominently
            if (searchResults.summary) {
              return (
                <>
                  <AgentSummary>
                    {searchResults.summary}
                  </AgentSummary>
                  
                  {searchResults.raw_results && searchResults.raw_results.length > 0 && (
                    <SourcesSection>
                      <summary>View sources ({searchResults.raw_results.length} results)</summary>
                      <div style={{ marginTop: '12px' }}>
                        {searchResults.raw_results.map((result: any, index: number) => (
                          <SearchResultItem key={index}>
                            <SearchResultTitle>{result.title}</SearchResultTitle>
                            <SearchResultSnippet>{result.snippet}</SearchResultSnippet>
                            {result.link && (
                              <SearchResultLink href={result.link} target="_blank" rel="noopener noreferrer">
                                View source →
                              </SearchResultLink>
                            )}
                          </SearchResultItem>
                        ))}
                      </div>
                    </SourcesSection>
                  )}
                </>
              );
            }
            
            // Original search results display
            if (searchResults.results && Array.isArray(searchResults.results)) {
              if (searchResults.results.length === 0) {
                return (
                  <SearchResults>
                    <InfoLabel style={{ color: 'inherit' }}>
                      No additional information found.
                    </InfoLabel>
                  </SearchResults>
                );
              }
              
              return (
                <SearchResults>
                  {searchResults.results.map((result: any, index: number) => (
                    <SearchResultItem key={index}>
                      <SearchResultTitle>{result.title}</SearchResultTitle>
                      <SearchResultSnippet>{result.snippet}</SearchResultSnippet>
                      {result.link && (
                        <SearchResultLink href={result.link} target="_blank" rel="noopener noreferrer">
                          View source →
                        </SearchResultLink>
                      )}
                    </SearchResultItem>
                  ))}
                </SearchResults>
              );
            }
            
            // Check if this is PDL data
            if (searchResults.pdl_id || searchResults.pdl_data || searchResults.enrichment) {
              return (
                <SearchResults>
                  <InfoLabel style={{ color: 'inherit', marginBottom: '8px' }}>
                    PDL enrichment data available. View in the PDL Enrichment tab for detailed information.
                  </InfoLabel>
                </SearchResults>
              );
            }
            
            // Fallback for unexpected format
            return (
              <SearchResults>
                <InfoLabel style={{ color: 'inherit' }}>
                  Unable to display additional information in the expected format.
                </InfoLabel>
              </SearchResults>
            );
          })()}
        </Section>
      )}
    </>
  );
};

export default BasicInfo;