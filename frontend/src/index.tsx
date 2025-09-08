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
import './styles/global.css';
import './styles/darkmode.css';
import './styles/terminal.css';

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
      
      // Update document classes for CSS styling
      document.documentElement.classList.remove('dark-mode', 'terminal-mode');
      if (storedTheme === ThemeType.DARK) {
        document.documentElement.classList.add('dark-mode');
      } else if (storedTheme === ThemeType.TERMINAL) {
        document.documentElement.classList.add('terminal-mode');
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