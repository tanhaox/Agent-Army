import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/layout/Layout';
import LearnPage from './pages/LearnPage';
import PersonasPage from './pages/PersonasPage';
import ScriptsPage from './pages/ScriptsPage';
import SettingsPage from './pages/SettingsPage';
import CreatorPage from './pages/CreatorPage';
import NotFoundPage from './pages/NotFoundPage';
import ToastProvider from './components/ui/Toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<ScriptsPage />} />
              <Route path="/learn" element={<LearnPage />} />
              <Route path="/personas" element={<PersonasPage />} />
              <Route path="/scripts" element={<ScriptsPage />} />
              <Route path="/creator" element={<CreatorPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
