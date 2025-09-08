import { createTheme, lightThemePrimitives, darkThemePrimitives } from 'baseui';
import { ThemePrimitives } from 'baseui/themes';

// Custom color primitives for light theme
const customLightPrimitives: Partial<ThemePrimitives> = {
  ...lightThemePrimitives,
  // Brand colors
  primary: '#1a73e8',
  primary50: '#e8f0fe',
  primary100: '#d2e3fc',
  primary200: '#aecbfa',
  primary300: '#8ab4f8',
  primary400: '#669df6',
  primary500: '#4285f4',
  primary600: '#1a73e8',
  primary700: '#1967d2',
  
  // Accent colors
  accent: '#f0f4f8',
  accent50: '#fafbfc',
  accent100: '#f5f7fa',
  accent200: '#e4e7eb',
  accent300: '#d1d9e0',
  accent400: '#b2bdcd',
  accent500: '#889ab5',
  accent600: '#5e6c82',
  accent700: '#3e4556',
};

// Custom color primitives for dark theme
const customDarkPrimitives: Partial<ThemePrimitives> = {
  ...darkThemePrimitives,
  // Brand colors for dark mode
  primary: '#4285f4',
  primary50: '#1a1a2e',
  primary100: '#16213e',
  primary200: '#0f1929',
  primary300: '#2663a0',
  primary400: '#2663a0',
  primary500: '#4285f4',
  primary600: '#669df6',
  primary700: '#8ab4f8',
  
  // Use standard Base UI background properties
  // backgroundPrimary: '#1a1a1a', - not supported
  // backgroundSecondary: '#252525', - not supported
  // backgroundTertiary: '#2f2f2f', - not supported
};

// Create light theme with your custom overrides
export const customLightTheme = createTheme(customLightPrimitives);

// Create dark theme  
export const customDarkTheme = createTheme(customDarkPrimitives);

// TODO: Your theme overrides need to be applied differently in Base UI v14
// The second parameter to createTheme is no longer supported
// We'll need to use component overrides or CSS-in-JS to apply custom styling

// Export design tokens for use in styled components
export const tokens = {
  spacing: customLightTheme.sizing,
  borders: customLightTheme.borders,
  animation: customLightTheme.animation,
  zIndex: customLightTheme.zIndex,
};

// Simple terminal theme (fallback)
export const terminalTheme = createTheme({
  ...darkThemePrimitives,
  primaryFontFamily: 'Monaco, Consolas, "Courier New", monospace',
});

// Theme type enum
export enum ThemeType {
  LIGHT = 'light',
  DARK = 'dark',
  TERMINAL = 'terminal',
}

// Get theme by type
export const getTheme = (type: ThemeType) => {
  switch (type) {
    case ThemeType.LIGHT:
      return customLightTheme;
    case ThemeType.DARK:
      return customDarkTheme;
    case ThemeType.TERMINAL:
      return terminalTheme;
    default:
      return customLightTheme;
  }
};