import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { ChatState, Message, ChatSession } from '../types/chat';
import * as chatService from '../services/chat';

const initialState: ChatState = {
  messages: [],
  sessions: [],
  currentSessionId: null,
  isLoading: false,
  streamingMessage: null,
  error: null,
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ message, sessionId }: { message: string; sessionId?: string }) => {
    const response = await chatService.sendMessage(message, sessionId);
    return response;
  }
);

export const loadChatHistory = createAsyncThunk(
  'chat/loadHistory',
  async () => {
    const response = await chatService.getChatHistory();
    return response;
  }
);

export const loadSession = createAsyncThunk(
  'chat/loadSession',
  async (sessionId: string) => {
    const response = await chatService.getSession(sessionId);
    return response;
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    setStreamingMessage: (state, action: PayloadAction<string | null>) => {
      state.streamingMessage = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
      state.currentSessionId = null;
    },
    setCurrentSession: (state, action: PayloadAction<string | null>) => {
      state.currentSessionId = action.payload;
    },
    updateStreamingMessage: (state, action: PayloadAction<string>) => {
      if (state.streamingMessage !== null) {
        state.streamingMessage += action.payload;
      }
    },
    finalizeStreamingMessage: (state) => {
      if (state.streamingMessage !== null) {
        const message: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: state.streamingMessage,
          timestamp: new Date().toISOString(),
        };
        state.messages.push(message);
        state.streamingMessage = null;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false;
        // Response will be handled via WebSocket
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to send message';
      })
      .addCase(loadChatHistory.fulfilled, (state, action) => {
        state.sessions = action.payload;
      })
      .addCase(loadSession.fulfilled, (state, action) => {
        state.messages = action.payload.messages;
        state.currentSessionId = action.payload.id;
      });
  },
});

export const {
  addMessage,
  setStreamingMessage,
  clearMessages,
  setCurrentSession,
  updateStreamingMessage,
  finalizeStreamingMessage,
} = chatSlice.actions;

export default chatSlice.reducer;