import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AuthState, User, LoginCredentials, AuthResponse } from '../types/auth';
import * as authService from '../services/auth';

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  token: localStorage.getItem('access_token'),
};

export const loginWithGoogle = createAsyncThunk(
  'auth/loginWithGoogle',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      const response = await authService.loginWithGoogle(credentials);
      return response;
    } catch (error: any) {
      console.error('Google login error:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        return rejectWithValue(error.response.data.detail || 'Authentication failed');
      }
      return rejectWithValue('Network error occurred');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await authService.logout();
});

export const refreshToken = createAsyncThunk('auth/refresh', async () => {
  const response = await authService.refreshToken();
  return response;
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    },
    setToken: (state, action: PayloadAction<string | null>) => {
      state.token = action.payload;
      if (action.payload) {
        localStorage.setItem('access_token', action.payload);
      } else {
        localStorage.removeItem('access_token');
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginWithGoogle.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginWithGoogle.fulfilled, (state, action) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        localStorage.setItem('access_token', action.payload.access_token);
        if (action.payload.refresh_token) {
          localStorage.setItem('refresh_token', action.payload.refresh_token);
        }
      })
      .addCase(loginWithGoogle.rejected, (state, action: any) => {
        state.isLoading = false;
        state.error = action.payload || action.error.message || 'Login failed';
        state.isAuthenticated = false;
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      })
      .addCase(refreshToken.pending, (state) => {
        state.isLoading = true;
      })
      .addCase(refreshToken.fulfilled, (state, action) => {
        state.token = action.payload.access_token;
        state.user = action.payload.user;
        state.isAuthenticated = true;
        state.isLoading = false;
        localStorage.setItem('access_token', action.payload.access_token);
        if (action.payload.refresh_token) {
          localStorage.setItem('refresh_token', action.payload.refresh_token);
        }
      })
      .addCase(refreshToken.rejected, (state) => {
        state.isLoading = false;
        state.isAuthenticated = false;
        state.token = null;
        state.user = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      });
  },
});

export const { setUser, setToken, clearError } = authSlice.actions;
export default authSlice.reducer;