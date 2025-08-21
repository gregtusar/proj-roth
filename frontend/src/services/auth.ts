import { AuthResponse, LoginCredentials, User } from '../types/auth';
import apiClient from './api';

export async function loginWithGoogle(
  credentials: LoginCredentials
): Promise<AuthResponse> {
  return apiClient.post<AuthResponse>('/auth/google/callback', credentials);
}

export async function logout(): Promise<void> {
  return apiClient.post('/auth/logout');
}

export async function refreshToken(): Promise<AuthResponse> {
  const refresh_token = localStorage.getItem('refresh_token');
  return apiClient.post<AuthResponse>('/auth/refresh', { refresh_token });
}

export async function getCurrentUser(): Promise<User> {
  return apiClient.get<User>('/auth/me');
}