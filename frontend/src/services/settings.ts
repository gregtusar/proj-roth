import api from './api';

export interface UserSettings {
  custom_prompt?: string;
  user_id: string;
}

export const getSettings = async (): Promise<UserSettings> => {
  const response = await api.get('/settings/');
  return response.data;
};

export const saveCustomPrompt = async (customPrompt: string): Promise<void> => {
  await api.post('/settings/custom-prompt', {
    custom_prompt: customPrompt,
  });
};

export const deleteCustomPrompt = async (): Promise<void> => {
  await api.delete('/settings/custom-prompt');
};