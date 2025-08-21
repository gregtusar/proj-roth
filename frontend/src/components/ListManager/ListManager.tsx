import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { Heading, HeadingLevel } from 'baseui/heading';
import { RootState, AppDispatch } from '../../store';
import {
  fetchUserLists,
  setSelectedList,
  setModalOpen,
} from '../../store/listsSlice';
import ListModal from './ListModal';
import ResultsTable from './ResultsTable';
import QueryEditor from './QueryEditor';

const Container = styled('div', {
  height: '100%',
  display: 'flex',
  backgroundColor: '#f5f5f5',
});

const Sidebar = styled('div', {
  width: '300px',
  backgroundColor: '#ffffff',
  borderRight: '1px solid #e0e0e0',
  display: 'flex',
  flexDirection: 'column',
});

const SidebarHeader = styled('div', {
  padding: '20px',
  borderBottom: '1px solid #e0e0e0',
});

const ListContainer = styled('div', {
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
});

const ListItem = styled('div', ({ $selected }: { $selected: boolean }) => ({
  padding: '12px',
  marginBottom: '8px',
  backgroundColor: $selected ? '#e3f2fd' : '#ffffff',
  border: $selected ? '2px solid #0066cc' : '1px solid #e0e0e0',
  borderRadius: '8px',
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  ':hover': {
    backgroundColor: $selected ? '#e3f2fd' : '#f5f5f5',
  },
}));

const ListTitle = styled('div', {
  fontSize: '14px',
  fontWeight: 600,
  marginBottom: '4px',
});

const ListDescription = styled('div', {
  fontSize: '12px',
  color: '#666',
  marginBottom: '4px',
});

const ListMeta = styled('div', {
  fontSize: '11px',
  color: '#999',
});

const MainContent = styled('div', {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
});

const ContentHeader = styled('div', {
  padding: '20px',
  backgroundColor: '#ffffff',
  borderBottom: '1px solid #e0e0e0',
});

const ContentBody = styled('div', {
  flex: 1,
  padding: '20px',
  overflowY: 'auto',
});

const EmptyState = styled('div', {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100%',
  color: '#666',
});

const EmptyStateIcon = styled('div', {
  fontSize: '64px',
  marginBottom: '16px',
});

const ListManager: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { userLists, selectedList, isModalOpen, queryResults } = useSelector(
    (state: RootState) => state.lists
  );

  useEffect(() => {
    dispatch(fetchUserLists());
  }, [dispatch]);

  const handleListSelect = (list: any) => {
    dispatch(setSelectedList(list));
  };

  const handleCreateList = () => {
    dispatch(setModalOpen(true));
  };

  return (
    <>
      <Container>
        <Sidebar>
          <SidebarHeader>
            <HeadingLevel>
              <Heading styleLevel={5}>My Lists</Heading>
            </HeadingLevel>
            <Button
              onClick={handleCreateList}
              kind={KIND.primary}
              size={SIZE.compact}
              overrides={{
                BaseButton: {
                  style: {
                    width: '100%',
                    marginTop: '12px',
                  },
                },
              }}
            >
              + Create New List
            </Button>
          </SidebarHeader>
          <ListContainer>
            {userLists.length === 0 ? (
              <div style={{ textAlign: 'center', color: '#666', padding: '20px' }}>
                No lists yet. Create your first list!
              </div>
            ) : (
              userLists.map((list) => (
                <ListItem
                  key={list.id}
                  $selected={selectedList?.id === list.id}
                  onClick={() => handleListSelect(list)}
                >
                  <ListTitle>{list.name}</ListTitle>
                  {list.description && (
                    <ListDescription>{list.description}</ListDescription>
                  )}
                  <ListMeta>
                    {list.row_count ? `${list.row_count} rows • ` : ''}
                    Updated {new Date(list.updated_at).toLocaleDateString()}
                  </ListMeta>
                </ListItem>
              ))
            )}
          </ListContainer>
        </Sidebar>

        <MainContent>
          {selectedList ? (
            <>
              <ContentHeader>
                <HeadingLevel>
                  <Heading styleLevel={4}>{selectedList.name}</Heading>
                  {selectedList.description && (
                    <p style={{ color: '#666', marginTop: '8px' }}>
                      {selectedList.description}
                    </p>
                  )}
                </HeadingLevel>
              </ContentHeader>
              <ContentBody>
                <QueryEditor list={selectedList} />
                {queryResults && <ResultsTable results={queryResults} />}
              </ContentBody>
            </>
          ) : (
            <EmptyState>
              <EmptyStateIcon>📋</EmptyStateIcon>
              <Heading styleLevel={5}>Select a list to view</Heading>
              <p style={{ marginTop: '8px' }}>
                Choose a list from the sidebar or create a new one
              </p>
            </EmptyState>
          )}
        </MainContent>
      </Container>

      {isModalOpen && <ListModal />}
    </>
  );
};

export default ListManager;