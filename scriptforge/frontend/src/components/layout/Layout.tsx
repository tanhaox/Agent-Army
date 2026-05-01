import { Outlet } from 'react-router-dom';
import ErrorBoundary from '../ui/ErrorBoundary';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import RouteProgress from './RouteProgress';

export default function Layout() {
  return (
    <div className="flex min-h-screen w-full">
      <RouteProgress />
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-auto p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
