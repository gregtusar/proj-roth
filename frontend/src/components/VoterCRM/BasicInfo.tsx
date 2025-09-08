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
          <SearchResults>
            {typeof searchResults === 'string' 
              ? searchResults 
              : JSON.stringify(searchResults, null, 2)
            }
          </SearchResults>
        </Section>
      )}
    </>
  );
};

export default BasicInfo;