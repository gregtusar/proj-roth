import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider as StyletronProvider } from 'styletron-react';
import { Client as Styletron } from 'styletron-engine-monolithic';
import { BaseProvider } from 'baseui';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import App from './App';
import { store } from './store';
import { getTheme, ThemeType } from './theme/customTheme';
import { injectThemeStyles, watchAndEnforceTheme } from './utils/themeInjector';
import './styles/global.css';
import './styles/darkmode.css';
import './styles/terminal.css';
import './styles/theme-override.css';

const engine = new Styletron();
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Theme selector hook
const ThemeWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = React.useState(() => {
    // Get theme from localStorage, with migration from old darkMode setting
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme && Object.values(ThemeType).includes(storedTheme as ThemeType)) {
      return getTheme(storedTheme as ThemeType);
    }
    // Migrate from old darkMode setting
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
      localStorage.setItem('theme', ThemeType.DARK);
      return getTheme(ThemeType.DARK);
    }
    return getTheme(ThemeType.LIGHT);
  });

  React.useEffect(() => {
    const updateTheme = () => {
      const storedTheme = localStorage.getItem('theme') as ThemeType;
      const newTheme = getTheme(storedTheme || ThemeType.LIGHT);
      setTheme(newTheme);
      
      // Update document classes for CSS styling on HTML element for maximum specificity
      document.documentElement.classList.remove('light-mode', 'dark-mode', 'terminal-mode');
      document.body.classList.remove('light-mode', 'dark-mode', 'terminal-mode');
      
      if (storedTheme === ThemeType.DARK) {
        document.documentElement.classList.add('dark-mode');
        document.body.classList.add('dark-mode');
        // Force style recalculation
        document.body.style.backgroundColor = '#1a1a1a';
        document.body.style.color = '#ffffff';
      } else if (storedTheme === ThemeType.TERMINAL) {
        document.documentElement.classList.add('terminal-mode');
        document.body.classList.add('terminal-mode');
        // Force style recalculation
        document.body.style.backgroundColor = '#0a0a0a';
        document.body.style.color = '#00ff00';
        document.body.style.fontFamily = '"Courier New", Monaco, Consolas, monospace';
      } else {
        document.documentElement.classList.add('light-mode');
        document.body.classList.add('light-mode');
        // Reset to light mode
        document.body.style.backgroundColor = '#ffffff';
        document.body.style.color = '#000000';
        document.body.style.fontFamily = '';
      }
      
      // Force a reflow to ensure styles are applied
      void document.body.offsetHeight;
      
      // Inject override styles to force theme
      injectThemeStyles(storedTheme as 'light' | 'dark' | 'terminal' || 'light');
      
      // Start watching for DOM changes
      const disconnect = watchAndEnforceTheme(storedTheme as 'light' | 'dark' | 'terminal' || 'light');
      
      // Clean up after a short delay if disconnect function exists
      if (disconnect) {
        setTimeout(() => disconnect(), 5000);
      }
    };

    // Initial setup
    updateTheme();

    // Listen for storage changes
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'theme') {
        updateTheme();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    
    // Watch for custom theme change event
    const handleThemeChange = () => {
      updateTheme();
    };
    
    window.addEventListener('themeChange', handleThemeChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('themeChange', handleThemeChange);
    };
  }, []);

  return <BaseProvider theme={theme}>{children}</BaseProvider>;
};

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <StyletronProvider value={engine}>
          <ThemeWrapper>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </ThemeWrapper>
        </StyletronProvider>
      </QueryClientProvider>
    </Provider>
  </React.StrictMode>
);