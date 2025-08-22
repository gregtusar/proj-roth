import { createSlice } from '@reduxjs/toolkit';

interface SettingsState {
  isDarkMode: boolean;
  fontSize: 'small' | 'medium' | 'large';
  notifications: {
    email: boolean;
    push: boolean;
  };
}

const initialState: SettingsState = {
  isDarkMode: localStorage.getItem('darkMode') === 'true',
  fontSize: 'medium',
  notifications: {
    email: false,
    push: false,
  },
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    toggleDarkMode: (state) => {
      state.isDarkMode = !state.isDarkMode;
      localStorage.setItem('darkMode', state.isDarkMode.toString());
      
      // Apply dark mode to document root for global styling
      if (state.isDarkMode) {
        document.documentElement.classList.add('dark-mode');
      } else {
        document.documentElement.classList.remove('dark-mode');
      }
    },
    setFontSize: (state, action) => {
      state.fontSize = action.payload;
      localStorage.setItem('fontSize', action.payload);
    },
    toggleEmailNotifications: (state) => {
      state.notifications.email = !state.notifications.email;
    },
    togglePushNotifications: (state) => {
      state.notifications.push = !state.notifications.push;
    },
  },
});

export const {
  toggleDarkMode,
  setFontSize,
  toggleEmailNotifications,
  togglePushNotifications,
} = settingsSlice.actions;

export default settingsSlice.reducer;