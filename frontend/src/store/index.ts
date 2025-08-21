import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import chatReducer from './chatSlice';
import listsReducer from './listsSlice';
import sidebarReducer from './sidebarSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    lists: listsReducer,
    sidebar: sidebarReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;