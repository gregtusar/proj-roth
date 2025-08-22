export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  googleId: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
}

export interface LoginCredentials {
  googleToken: string;
  redirectUri?: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token: string;
}