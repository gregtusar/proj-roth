import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { ListsState, VoterList, QueryResult } from '../types/lists';
import * as listsService from '../services/lists';

const initialState: ListsState = {
  userLists: [],
  selectedList: null,
  queryResults: null,
  isLoading: false,
  isModalOpen: false,
  error: null,
};

export const fetchUserLists = createAsyncThunk(
  'lists/fetchUserLists',
  async () => {
    const response = await listsService.getUserLists();
    return response;
  }
);

export const createList = createAsyncThunk(
  'lists/create',
  async (list: Partial<VoterList>) => {
    const response = await listsService.createList(list);
    return response;
  }
);

export const runQuery = createAsyncThunk(
  'lists/runQuery',
  async (listId: string) => {
    const response = await listsService.runListQuery(listId);
    return response;
  }
);

export const deleteList = createAsyncThunk(
  'lists/delete',
  async (listId: string) => {
    await listsService.deleteList(listId);
    return listId;
  }
);

const listsSlice = createSlice({
  name: 'lists',
  initialState,
  reducers: {
    setSelectedList: (state, action: PayloadAction<VoterList | null>) => {
      state.selectedList = action.payload;
    },
    setModalOpen: (state, action: PayloadAction<boolean>) => {
      state.isModalOpen = action.payload;
    },
    clearQueryResults: (state) => {
      state.queryResults = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUserLists.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(fetchUserLists.fulfilled, (state, action) => {
        state.isLoading = false;
        state.userLists = action.payload;
      })
      .addCase(fetchUserLists.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch lists';
      })
      .addCase(createList.fulfilled, (state, action) => {
        state.userLists.push(action.payload);
        state.isModalOpen = false;
      })
      .addCase(runQuery.pending, (state) => {
        state.isLoading = true;
        state.queryResults = null;
      })
      .addCase(runQuery.fulfilled, (state, action) => {
        state.isLoading = false;
        state.queryResults = action.payload;
      })
      .addCase(runQuery.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Query failed';
      })
      .addCase(deleteList.fulfilled, (state, action) => {
        state.userLists = state.userLists.filter(
          (list) => list.id !== action.payload
        );
        if (state.selectedList?.id === action.payload) {
          state.selectedList = null;
          state.queryResults = null;
        }
      });
  },
});

export const { setSelectedList, setModalOpen, clearQueryResults } =
  listsSlice.actions;

export default listsSlice.reducer;