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

export async function getChatSessions(): Promise<{ sessions: ChatSession[] }> {
  return apiClient.get<{ sessions: ChatSession[] }>('/sessions/');
}

export async function createSession(
  sessionName?: string,
  firstMessage?: string
): Promise<ChatSession> {
  return apiClient.post<ChatSession>('/sessions/', {
    session_name: sessionName,
    first_message: firstMessage,
  });
}

export async function getSessionMessages(sessionId: string): Promise<{
  session: ChatSession;
  messages: Message[];
}> {
  return apiClient.get<{ session: ChatSession; messages: Message[] }>(
    `/sessions/${sessionId}`
  );
}

export async function updateSessionName(
  sessionId: string,
  sessionName: string
): Promise<{ success: boolean }> {
  return apiClient.put<{ success: boolean }>(`/sessions/${sessionId}`, {
    session_name: sessionName,
  });
}

export async function deleteSession(sessionId: string): Promise<{ success: boolean }> {
  return apiClient.delete<{ success: boolean }>(`/sessions/${sessionId}`);
}