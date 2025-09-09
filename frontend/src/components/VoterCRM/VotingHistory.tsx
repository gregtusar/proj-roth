import React from 'react';
import { styled } from 'baseui';
import { Check, Delete } from 'baseui/icon';
import { Tag } from 'baseui/tag';

const Container = styled('div', {
  padding: '24px',
});

const Section = styled('div', () => ({
  marginBottom: '32px',
}));

const SectionTitle = styled('h3', ({ $theme }) => ({
  fontSize: '18px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  marginBottom: '16px',
}));

const VotingTable = styled('table', ({ $theme }) => ({
  width: '100%',
  borderCollapse: 'collapse',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  overflow: 'hidden',
}));

const TableHeader = styled('thead', ({ $theme }) => ({
  backgroundColor: $theme.colors.backgroundTertiary,
}));

const TableRow = styled('tr', ({ $theme }) => ({
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  ':last-child': {
    borderBottom: 'none',
  },
}));

const TableHeaderCell = styled('th', ({ $theme }) => ({
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: '12px',
  fontWeight: 600,
  color: $theme.colors.contentSecondary,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

const TableCell = styled('td', ({ $theme }) => ({
  padding: '12px 16px',
  fontSize: '14px',
  color: $theme.colors.contentPrimary,
}));

const VoteIndicator = styled('div', {
  display: 'flex',
  alignItems: 'center',
  gap: '8px',
});

const NoDataMessage = styled('div', ({ $theme }) => ({
  padding: '24px',
  textAlign: 'center',
  color: $theme.colors.contentSecondary,
  fontSize: '14px',
}));

const Summary = styled('div', () => ({
  display: 'flex',
  gap: '24px',
  marginBottom: '24px',
  flexWrap: 'wrap',
}));

const SummaryItem = styled('div', ({ $theme }) => ({
  padding: '16px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
  minWidth: '150px',
}));

const SummaryLabel = styled('div', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.contentSecondary,
  marginBottom: '4px',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
}));

const SummaryValue = styled('div', ({ $theme }) => ({
  fontSize: '24px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
}));

interface VotingHistoryProps {
  history: any;
}

const VotingHistory: React.FC<VotingHistoryProps> = ({ history }) => {
  if (!history) {
    return (
      <Container>
        <NoDataMessage>Loading voting history...</NoDataMessage>
      </Container>
    );
  }

  const { primaries = [], generals = [] } = history;

  // Calculate summary statistics
  const totalPrimariesVoted = primaries.filter((p: any) => p.voted).length;
  const totalPrimariesAvailable = primaries.length;
  const totalGeneralsVoted = generals.filter((g: any) => g.voted).length;
  const totalGeneralsAvailable = generals.length;

  // Combine all years for display
  const allYears = new Set([
    ...primaries.map((p: any) => p.year),
    ...generals.map((g: any) => g.year),
  ]);
  const sortedYears = Array.from(allYears).sort((a, b) => Number(b) - Number(a));

  const getPrimaryParty = (year: string) => {
    const primary = primaries.find((p: any) => p.year === year && p.voted);
    return primary?.party || null;
  };
  
  const didVoteInGeneral = (year: string) => 
    generals.some((g: any) => g.year === year && g.voted);

  return (
    <Container>
      <Summary>
        <SummaryItem>
          <SummaryLabel>Primary Elections</SummaryLabel>
          <SummaryValue>{totalPrimariesVoted} / {totalPrimariesAvailable}</SummaryValue>
        </SummaryItem>
        <SummaryItem>
          <SummaryLabel>General Elections</SummaryLabel>
          <SummaryValue>{totalGeneralsVoted} / {totalGeneralsAvailable}</SummaryValue>
        </SummaryItem>
        <SummaryItem>
          <SummaryLabel>Total Participation</SummaryLabel>
          <SummaryValue>{totalPrimariesVoted + totalGeneralsVoted} / {totalPrimariesAvailable + totalGeneralsAvailable}</SummaryValue>
        </SummaryItem>
      </Summary>

      <Section>
        <SectionTitle>Election Participation History</SectionTitle>
        {sortedYears.length > 0 ? (
          <VotingTable>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Year</TableHeaderCell>
                <TableHeaderCell>Primary Election</TableHeaderCell>
                <TableHeaderCell>General Election</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <tbody>
              {sortedYears.map((year) => {
                const primaryParty = getPrimaryParty(year);
                return (
                  <TableRow key={year}>
                    <TableCell>
                      <strong>{year}</strong>
                    </TableCell>
                    <TableCell>
                      <VoteIndicator>
                        {primaryParty ? (
                          <>
                            <Check size={20} color="positive" />
                            <Tag 
                              closeable={false} 
                              kind={primaryParty === 'DEM' ? 'blue' : primaryParty === 'REP' ? 'red' : 'neutral'}
                            >
                              {primaryParty} Primary
                            </Tag>
                          </>
                        ) : (
                          <>
                            <Delete size={20} color="neutral" />
                            <span style={{ color: '#999' }}>Did not vote</span>
                          </>
                        )}
                      </VoteIndicator>
                    </TableCell>
                    <TableCell>
                      <VoteIndicator>
                        {didVoteInGeneral(year) ? (
                          <>
                            <Check size={20} color="positive" />
                            <Tag closeable={false} kind="positive">Voted</Tag>
                          </>
                        ) : (
                          <>
                            <Delete size={20} color="neutral" />
                            <span style={{ color: '#999' }}>Did not vote</span>
                          </>
                        )}
                      </VoteIndicator>
                    </TableCell>
                  </TableRow>
                );
              })}
            </tbody>
          </VotingTable>
        ) : (
          <NoDataMessage>No voting history available</NoDataMessage>
        )}
      </Section>
    </Container>
  );
};

export default VotingHistory;