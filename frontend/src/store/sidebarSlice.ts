import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Project {
  id: string;
  name: string;
  icon?: string;
  children?: Project[];
  expanded?: boolean;
}

interface SidebarState {
  isOpen: boolean;
  activeSection: 'chats' | 'projects' | 'tools';
  projects: Project[];
  expandedProjects: string[];
}

const initialState: SidebarState = {
  isOpen: true,
  activeSection: 'chats',
  projects: [],
  expandedProjects: [],
};

const sidebarSlice = createSlice({
  name: 'sidebar',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.isOpen = !state.isOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.isOpen = action.payload;
    },
    setActiveSection: (
      state,
      action: PayloadAction<'chats' | 'projects' | 'tools'>
    ) => {
      state.activeSection = action.payload;
    },
    toggleProjectExpanded: (state, action: PayloadAction<string>) => {
      const projectId = action.payload;
      const index = state.expandedProjects.indexOf(projectId);
      if (index > -1) {
        state.expandedProjects.splice(index, 1);
      } else {
        state.expandedProjects.push(projectId);
      }
    },
    setProjects: (state, action: PayloadAction<Project[]>) => {
      state.projects = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  setActiveSection,
  toggleProjectExpanded,
  setProjects,
} = sidebarSlice.actions;

export default sidebarSlice.reducer;