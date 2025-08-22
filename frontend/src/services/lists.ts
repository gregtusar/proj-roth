import { VoterList, QueryResult } from '../types/lists';
import apiClient from './api';

export async function getUserLists(): Promise<VoterList[]> {
  return apiClient.get<VoterList[]>('/lists');
}

export async function getList(listId: string): Promise<VoterList> {
  return apiClient.get<VoterList>(`/lists/${listId}`);
}

export async function createList(
  list: Partial<VoterList>
): Promise<VoterList> {
  return apiClient.post<VoterList>('/lists', list);
}

export async function updateList(
  listId: string,
  list: Partial<VoterList>
): Promise<VoterList> {
  return apiClient.put<VoterList>(`/lists/${listId}`, list);
}

export async function deleteList(listId: string): Promise<void> {
  return apiClient.delete(`/lists/${listId}`);
}

export async function runListQuery(listId: string): Promise<QueryResult> {
  return apiClient.post<QueryResult>(`/lists/${listId}/run`);
}

export async function exportListToCsv(listId: string): Promise<Blob> {
  const response = await apiClient.get(`/lists/${listId}/export`, {
    responseType: 'blob',
  });
  return response as unknown as Blob;
}

export async function regenerateSqlQuery(listId: string): Promise<{ query: string }> {
  return apiClient.post<{ query: string }>(`/lists/${listId}/regenerate-sql`);
}