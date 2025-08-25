import { ChatSession, Message } from '../types/chat';
import apiClient from './api';

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<Message> {
  console.log('[chatService] sendMessage called:', { message, sessionId });
  const result = await apiClient.post<Message>('/chat/send', {
    message,
    session_id: sessionId,
  });
  console.log('[chatService] sendMessage result:', result);
  return result;
}

export async function getChatSessions(): Promise<{ sessions: ChatSession[] }> {
  console.log('[chatService] getChatSessions called');
  const result = await apiClient.get<{ sessions: ChatSession[] }>('/sessions/');
  console.log('[chatService] getChatSessions result:', result);
  return result;
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
  console.log('[chatService] getSessionMessages called with sessionId:', sessionId);
  const result = await apiClient.get<{ session: ChatSession; messages: Message[] }>(
    `/sessions/${sessionId}`
  );
  console.log('[chatService] getSessionMessages result:', result);
  return result;
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