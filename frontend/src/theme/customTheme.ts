import { createTheme, lightThemePrimitives, darkThemePrimitives } from 'baseui';
import { ThemePrimitives } from 'baseui/themes';

// Use Inter font (Uber's standard) with proper fallbacks
const UBER_FONT_FAMILY = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
const UBER_MONO_FAMILY = '"JetBrains Mono", "Fira Code", Monaco, Consolas, "Courier New", monospace';

// Custom color primitives for light theme
const customLightPrimitives: Partial<ThemePrimitives> = {
  ...lightThemePrimitives,
  // Use Uber's font system
  primaryFontFamily: UBER_FONT_FAMILY,
  
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
  // Use Uber's font system
  primaryFontFamily: UBER_FONT_FAMILY,
  
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
};

// Create light theme - Base UI v14 doesn't support overrides in createTheme
// Typography will use the primaryFontFamily from primitives
export const customLightTheme = createTheme(customLightPrimitives);

// Create dark theme
export const customDarkTheme = createTheme(customDarkPrimitives);

// Terminal theme with monospace font
const terminalPrimitives: Partial<ThemePrimitives> = {
  ...darkThemePrimitives,
  primaryFontFamily: UBER_MONO_FAMILY,
  // Terminal green colors
  primary: '#00ff00',
  primary50: '#001100',
  primary100: '#003300',
  primary200: '#005500',
  primary300: '#007700',
  primary400: '#009900',
  primary500: '#00bb00',
  primary600: '#00dd00',
  primary700: '#00ff00',
};

export const terminalTheme = createTheme(terminalPrimitives);

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