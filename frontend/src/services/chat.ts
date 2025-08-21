import { ChatSession, Message } from '../types/chat';
import apiClient from './api';

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<Message> {
  return apiClient.post<Message>('/chat/send', {
    message,
    session_id: sessionId,
  });
}

export async function getChatHistory(): Promise<ChatSession[]> {
  return apiClient.get<ChatSession[]>('/chat/history');
}

export async function getSession(sessionId: string): Promise<ChatSession> {
  return apiClient.get<ChatSession>(`/chat/session/${sessionId}`);
}

export async function saveSession(
  sessionId: string,
  messages: Message[]
): Promise<void> {
  return apiClient.post(`/chat/session/${sessionId}/save`, { messages });
}

export async function deleteSession(sessionId: string): Promise<void> {
  return apiClient.delete(`/chat/session/${sessionId}`);
}