import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider as StyletronProvider } from 'styletron-react';
import { Client as Styletron } from 'styletron-engine-monolithic';
import { BaseProvider, LightTheme } from 'baseui';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import App from './App';
import { store } from './store';
import './styles/global.css';

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

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <StyletronProvider value={engine}>
          <BaseProvider theme={LightTheme}>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </BaseProvider>
        </StyletronProvider>
      </QueryClientProvider>
    </Provider>
  </React.StrictMode>
);