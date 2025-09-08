import React, { useState, useCallback, useEffect } from 'react';
import { styled } from 'baseui';
import { Input } from 'baseui/input';
import { Button } from 'baseui/button';
import { Search } from 'baseui/icon';
import { Popover, PLACEMENT } from 'baseui/popover';
import { debounce } from 'lodash';
import axios from 'axios';
import { VoterSearchResult } from './VoterCRM';

const SearchContainer = styled('div', {
  display: 'flex',
  gap: '12px',
  alignItems: 'center',
});

const SearchInput = styled('div', {
  flex: 1,
  maxWidth: '600px',
});

const ResultItem = styled('div', ({ $theme }) => ({
  padding: '8px 12px',
  cursor: 'pointer',
  borderBottom: `1px solid ${$theme.colors.borderOpaque}`,
  ':hover': {
    backgroundColor: $theme.colors.backgroundTertiary,
  },
}));

const ResultName = styled('div', ({ $theme }) => ({
  fontWeight: 500,
  fontSize: '14px',
  color: $theme.colors.contentPrimary,
}));

const ResultDetails = styled('div', ({ $theme }) => ({
  fontSize: '12px',
  color: $theme.colors.contentSecondary,
  marginTop: '2px',
}));

const NoResults = styled('div', ({ $theme }) => ({
  padding: '12px',
  textAlign: 'center',
  color: $theme.colors.contentSecondary,
  fontSize: '14px',
}));

interface VoterSearchProps {
  onSelectVoter: (voter: VoterSearchResult) => void;
}

const VoterSearch: React.FC<VoterSearchProps> = ({ onSelectVoter }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VoterSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      if (query.length < 2) {
        setSearchResults([]);
        setIsPopoverOpen(false);
        return;
      }

      setIsSearching(true);
      try {
        const token = localStorage.getItem('access_token');
        const response = await axios.get('/api/crm/search', {
          params: { q: query, limit: 20 },
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        setSearchResults(response.data);
        setIsPopoverOpen(response.data.length > 0);
      } catch (error) {
        console.error('Error searching voters:', error);
        setSearchResults([]);
        setIsPopoverOpen(false);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    debouncedSearch(searchQuery);
  }, [searchQuery, debouncedSearch]);

  const handleSearch = () => {
    if (searchQuery.length >= 2) {
      debouncedSearch(searchQuery);
    }
  };

  const handleSelectVoter = (voter: VoterSearchResult) => {
    onSelectVoter(voter);
    setSearchQuery('');
    setSearchResults([]);
    setIsPopoverOpen(false);
  };

  const formatPartyAge = (voter: VoterSearchResult) => {
    const parts = [];
    if (voter.party) parts.push(voter.party);
    if (voter.age) parts.push(`Age ${voter.age}`);
    return parts.length > 0 ? ` • ${parts.join(' • ')}` : '';
  };

  return (
    <SearchContainer>
      <SearchInput>
        <Popover
          isOpen={isPopoverOpen}
          onClickOutside={() => setIsPopoverOpen(false)}
          placement={PLACEMENT.bottomLeft}
          content={() => (
            <div style={{ maxHeight: '400px', overflowY: 'auto', minWidth: '500px' }}>
              {searchResults.length > 0 ? (
                searchResults.map((voter) => (
                  <ResultItem
                    key={voter.master_id}
                    onClick={() => handleSelectVoter(voter)}
                  >
                    <ResultName>{voter.name}</ResultName>
                    <ResultDetails>
                      {voter.address}
                      {formatPartyAge(voter)}
                    </ResultDetails>
                  </ResultItem>
                ))
              ) : (
                <NoResults>
                  {isSearching ? 'Searching...' : 'No results found'}
                </NoResults>
              )}
            </div>
          )}
        >
          <div style={{ width: '100%' }}>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.currentTarget.value)}
              placeholder="Enter voter name (Last, First)"
              startEnhancer={<Search size={20} />}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch();
                }
              }}
              overrides={{
                Root: {
                  style: {
                    width: '100%',
                  },
                },
              }}
            />
          </div>
        </Popover>
      </SearchInput>
      
      <Button
        onClick={handleSearch}
        isLoading={isSearching}
        disabled={searchQuery.length < 2}
      >
        Search
      </Button>
    </SearchContainer>
  );
};

export default VoterSearch;