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

export const loadChatSessions = createAsyncThunk(
  'chat/loadSessions',
  async () => {
    const response = await chatService.getChatSessions();
    return response.sessions;
  }
);

export const loadSession = createAsyncThunk(
  'chat/loadSession',
  async (sessionId: string) => {
    const response = await chatService.getSessionMessages(sessionId);
    return response;
  }
);

export const createNewSession = createAsyncThunk(
  'chat/createSession',
  async ({ sessionName, firstMessage }: { sessionName?: string; firstMessage?: string }) => {
    const response = await chatService.createSession(sessionName, firstMessage);
    return response;
  }
);

export const renameSession = createAsyncThunk(
  'chat/renameSession',
  async ({ sessionId, sessionName }: { sessionId: string; sessionName: string }) => {
    await chatService.updateSessionName(sessionId, sessionName);
    return { sessionId, sessionName };
  }
);

export const deleteSessionAsync = createAsyncThunk(
  'chat/deleteSession',
  async (sessionId: string) => {
    await chatService.deleteSession(sessionId);
    return sessionId;
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
          message_id: Date.now().toString(),
          session_id: state.currentSessionId || 'temp-session',
          user_id: 'current_user',
          message_type: 'assistant',
          message_text: state.streamingMessage,
          timestamp: new Date().toISOString(),
          sequence_number: state.messages.length,
        };
        state.messages.push(message);
        state.streamingMessage = null;
      }
    },
    updateSession: (state, action: PayloadAction<ChatSession>) => {
      const index = state.sessions.findIndex(s => s.session_id === action.payload.session_id);
      if (index !== -1) {
        state.sessions[index] = action.payload;
      } else {
        state.sessions.unshift(action.payload);
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
      .addCase(loadChatSessions.fulfilled, (state, action) => {
        state.sessions = action.payload;
      })
      .addCase(loadSession.fulfilled, (state, action) => {
        state.messages = action.payload.messages;
        state.currentSessionId = action.payload.session.session_id;
        // Update session in the list
        const index = state.sessions.findIndex(s => s.session_id === action.payload.session.session_id);
        if (index !== -1) {
          state.sessions[index] = action.payload.session;
        }
      })
      .addCase(createNewSession.fulfilled, (state, action) => {
        state.sessions.unshift(action.payload);
        state.currentSessionId = action.payload.session_id;
      })
      .addCase(renameSession.fulfilled, (state, action) => {
        const session = state.sessions.find(s => s.session_id === action.payload.sessionId);
        if (session) {
          session.session_name = action.payload.sessionName;
        }
      })
      .addCase(deleteSessionAsync.fulfilled, (state, action) => {
        state.sessions = state.sessions.filter(s => s.session_id !== action.payload);
        if (state.currentSessionId === action.payload) {
          state.currentSessionId = null;
          state.messages = [];
        }
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
  updateSession,
} = chatSlice.actions;

export default chatSlice.reducer;