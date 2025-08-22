import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { styled } from 'baseui';
import { Button, KIND, SIZE } from 'baseui/button';
import { Heading, HeadingLevel } from 'baseui/heading';
import { Delete } from 'baseui/icon';
import { RootState, AppDispatch } from '../../store';
import {
  fetchUserLists,
  setSelectedList,
  setModalOpen,
  deleteList,
} from '../../store/listsSlice';
import ListModal from './ListModal';
import ResultsTable from './ResultsTable';
import QueryEditor from './QueryEditor';
import ConfirmModal from '../Common/ConfirmModal';

const Container = styled('div', {
  height: '100%',
  display: 'flex',
  flexDirection: 'row',
  backgroundColor: '#f5f5f5',
  width: '100%',
});

const LeftPanel = styled('div', {
  width: '450px',
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
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
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

const ListContent = styled('div', {
  flex: 1,
});

const DeleteButton = styled('button', {
  background: 'transparent',
  border: 'none',
  color: '#dc2626',
  cursor: 'pointer',
  padding: '4px',
  borderRadius: '4px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  transition: 'all 0.2s ease',
  ':hover': {
    backgroundColor: '#fee2e2',
  },
});

const MainContent = styled('div', {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  backgroundColor: '#ffffff',
});

const ContentHeader = styled('div', {
  padding: '20px',
  backgroundColor: '#ffffff',
  borderBottom: '1px solid #e0e0e0',
});

const ContentBody = styled('div', {
  flex: 1,
  padding: '24px 40px',
  overflowY: 'auto',
  maxWidth: '1200px',
  margin: '0 auto',
  width: '100%',
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
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [listToDelete, setListToDelete] = useState<any>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    dispatch(fetchUserLists());
  }, [dispatch]);

  const handleListSelect = (list: any) => {
    dispatch(setSelectedList(list));
  };

  const handleCreateList = () => {
    dispatch(setModalOpen(true));
  };

  const handleDeleteClick = (e: React.MouseEvent, list: any) => {
    e.stopPropagation(); // Prevent selecting the list
    setListToDelete(list);
    setDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (listToDelete) {
      setIsDeleting(true);
      try {
        await dispatch(deleteList(listToDelete.id)).unwrap();
        // Refresh the list after successful deletion
        await dispatch(fetchUserLists());
        setDeleteModalOpen(false);
        setListToDelete(null);
      } catch (error) {
        console.error('Failed to delete list:', error);
        alert('Failed to delete list. Please try again.');
      } finally {
        setIsDeleting(false);
      }
    }
  };

  return (
    <>
      <Container>
        <LeftPanel>
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
                  <ListContent>
                    <ListTitle>{list.name}</ListTitle>
                    {list.description && (
                      <ListDescription>{list.description}</ListDescription>
                    )}
                    <ListMeta>
                      {list.row_count ? `${list.row_count.toLocaleString()} rows • ` : ''}
                      Updated {new Date(list.updated_at).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        year: 'numeric' 
                      })}
                      {list.user_email && (
                        <>
                          <br />
                          <span style={{ fontSize: '10px' }}>{list.user_email}</span>
                        </>
                      )}
                    </ListMeta>
                  </ListContent>
                  <DeleteButton
                    onClick={(e) => handleDeleteClick(e, list)}
                    title="Delete list"
                  >
                    <Delete size={20} />
                  </DeleteButton>
                </ListItem>
              ))
            )}
          </ListContainer>
        </LeftPanel>

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
              <HeadingLevel>
                <Heading styleLevel={5}>Select a list to view</Heading>
              </HeadingLevel>
              <p style={{ marginTop: '8px' }}>
                Choose a list from the sidebar or create a new one
              </p>
            </EmptyState>
          )}
        </MainContent>
      </Container>

      {isModalOpen && <ListModal />}
      
      <ConfirmModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setListToDelete(null);
        }}
        onConfirm={handleConfirmDelete}
        title="Delete List"
        message={`Are you sure you want to delete "${listToDelete?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={isDeleting}
      />
    </>
  );
};

export default ListManager;