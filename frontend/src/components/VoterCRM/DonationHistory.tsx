import React, { useState } from 'react';
import { styled } from 'baseui';
import { Tabs, Tab } from 'baseui/tabs';
import { Tag } from 'baseui/tag';
import { Pagination } from 'baseui/pagination';
import { Button, SIZE as ButtonSize } from 'baseui/button';

const Container = styled('div', {
  padding: '24px',
});

const Summary = styled('div', () => ({
  display: 'flex',
  gap: '24px',
  marginBottom: '24px',
  flexWrap: 'wrap',
}));

const SummaryCard = styled('div', ({ $theme }) => ({
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

const DonationTable = styled('table', ({ $theme }) => ({
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

const RecipientSection = styled('div', ({ $theme }) => ({
  marginBottom: '24px',
  padding: '16px',
  backgroundColor: $theme.colors.backgroundSecondary,
  borderRadius: '8px',
}));

const RecipientHeader = styled('div', ({ $theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '12px',
  paddingBottom: '12px',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
}));

const RecipientName = styled('h4', ({ $theme }) => ({
  fontSize: '16px',
  fontWeight: 600,
  color: $theme.colors.contentPrimary,
  margin: 0,
}));

const RecipientStats = styled('div', ({ $theme }) => ({
  display: 'flex',
  gap: '12px',
  fontSize: '14px',
  color: $theme.colors.contentSecondary,
}));

const NoDataMessage = styled('div', ({ $theme }) => ({
  padding: '24px',
  textAlign: 'center',
  color: $theme.colors.contentSecondary,
  fontSize: '14px',
}));

interface DonationHistoryProps {
  history: any;
}

const DonationHistory: React.FC<DonationHistoryProps> = ({ history }) => {
  const [activeTab, setActiveTab] = useState('0');
  const [currentPage, setCurrentPage] = useState(1);
  const [recipientPage, setRecipientPage] = useState(1);
  const itemsPerPage = 10;
  const recipientsPerPage = 5;

  if (!history) {
    return (
      <Container>
        <NoDataMessage>Loading donation history...</NoDataMessage>
      </Container>
    );
  }

  const { summary = {}, donations = [], by_recipient = {} } = history;

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  const getPartyTag = (recipient: string) => {
    const lowerRecipient = recipient.toLowerCase();
    if (lowerRecipient.includes('democrat') || lowerRecipient.includes('dem ')) {
      return <Tag closeable={false} kind="blue">DEM</Tag>;
    } else if (lowerRecipient.includes('republican') || lowerRecipient.includes('rep ')) {
      return <Tag closeable={false} kind="red">REP</Tag>;
    }
    return null;
  };

  return (
    <Container>
      <Summary>
        <SummaryCard>
          <SummaryLabel>Total Donated</SummaryLabel>
          <SummaryValue>{formatCurrency(summary.total_amount || 0)}</SummaryValue>
        </SummaryCard>
        <SummaryCard>
          <SummaryLabel>Number of Donations</SummaryLabel>
          <SummaryValue>{summary.num_donations || 0}</SummaryValue>
        </SummaryCard>
        <SummaryCard>
          <SummaryLabel>Recipients</SummaryLabel>
          <SummaryValue>{summary.num_recipients || 0}</SummaryValue>
        </SummaryCard>
        {donations.length > 0 && (
          <SummaryCard>
            <SummaryLabel>Average Donation</SummaryLabel>
            <SummaryValue>
              {formatCurrency((summary.total_amount || 0) / (summary.num_donations || 1))}
            </SummaryValue>
          </SummaryCard>
        )}
      </Summary>

      <Tabs
        activeKey={activeTab}
        onChange={({ activeKey }) => setActiveTab(activeKey as string)}
      >
        <Tab title="All Donations">
          {donations.length > 0 ? (
            <>
              <DonationTable>
                <TableHeader>
                  <TableRow>
                    <TableHeaderCell>Date</TableHeaderCell>
                    <TableHeaderCell>Recipient</TableHeaderCell>
                    <TableHeaderCell>Amount</TableHeaderCell>
                    <TableHeaderCell>Election</TableHeaderCell>
                    <TableHeaderCell>Employer</TableHeaderCell>
                    <TableHeaderCell>Occupation</TableHeaderCell>
                  </TableRow>
                </TableHeader>
                <tbody>
                  {donations
                    .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                    .map((donation: any, index: number) => (
                      <TableRow key={index}>
                        <TableCell>{formatDate(donation.date)}</TableCell>
                        <TableCell>
                          {donation.recipient}
                          {getPartyTag(donation.recipient)}
                        </TableCell>
                        <TableCell>
                          <strong>{formatCurrency(donation.amount)}</strong>
                        </TableCell>
                        <TableCell>
                          {donation.election_type} {donation.election_year}
                        </TableCell>
                        <TableCell>{donation.contributor_employer || '—'}</TableCell>
                        <TableCell>{donation.contributor_occupation || '—'}</TableCell>
                      </TableRow>
                    ))}
                </tbody>
              </DonationTable>
              {donations.length > itemsPerPage && (
                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
                  <Pagination
                    numPages={Math.ceil(donations.length / itemsPerPage)}
                    currentPage={currentPage}
                    onPageChange={({ nextPage }) => {
                      setCurrentPage(Math.min(Math.max(nextPage, 1), Math.ceil(donations.length / itemsPerPage)));
                    }}
                  />
                </div>
              )}
            </>
          ) : (
            <NoDataMessage>No donation history found</NoDataMessage>
          )}
        </Tab>

        <Tab title="By Recipient">
          {Object.keys(by_recipient).length > 0 ? (
            <>
              {Object.entries(by_recipient)
                .sort((a: any, b: any) => b[1].total - a[1].total)
                .slice((recipientPage - 1) * recipientsPerPage, recipientPage * recipientsPerPage)
                .map(([recipient, data]: any) => (
                  <RecipientSection key={recipient}>
                    <RecipientHeader>
                      <RecipientName>
                        {recipient}
                        {getPartyTag(recipient)}
                      </RecipientName>
                      <RecipientStats>
                        <span>{data.count} donations</span>
                        <span>•</span>
                        <strong>{formatCurrency(data.total)}</strong>
                      </RecipientStats>
                    </RecipientHeader>
                    <DonationTable>
                      <TableHeader>
                        <TableRow>
                          <TableHeaderCell>Date</TableHeaderCell>
                          <TableHeaderCell>Amount</TableHeaderCell>
                          <TableHeaderCell>Election</TableHeaderCell>
                          <TableHeaderCell>Report Type</TableHeaderCell>
                        </TableRow>
                      </TableHeader>
                      <tbody>
                        {data.donations.slice(0, 10).map((donation: any, index: number) => (
                          <TableRow key={index}>
                            <TableCell>{formatDate(donation.date)}</TableCell>
                            <TableCell>
                              <strong>{formatCurrency(donation.amount)}</strong>
                            </TableCell>
                            <TableCell>
                              {donation.election_type} {donation.election_year}
                            </TableCell>
                            <TableCell>{donation.report_type || '—'}</TableCell>
                          </TableRow>
                        ))}
                      </tbody>
                    </DonationTable>
                    {data.donations.length > 10 && (
                      <div style={{ marginTop: '8px', padding: '8px', fontSize: '12px', color: '#666' }}>
                        Showing first 10 of {data.donations.length} donations to this recipient
                      </div>
                    )}
                  </RecipientSection>
                ))}
              {Object.keys(by_recipient).length > recipientsPerPage && (
                <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center' }}>
                  <Pagination
                    numPages={Math.ceil(Object.keys(by_recipient).length / recipientsPerPage)}
                    currentPage={recipientPage}
                    onPageChange={({ nextPage }) => {
                      setRecipientPage(Math.min(Math.max(nextPage, 1), Math.ceil(Object.keys(by_recipient).length / recipientsPerPage)));
                    }}
                  />
                </div>
              )}
            </>
          ) : (
            <NoDataMessage>No donation history found</NoDataMessage>
          )}
        </Tab>
      </Tabs>
    </Container>
  );
};

export default DonationHistory;