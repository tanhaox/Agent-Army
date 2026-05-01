import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center space-y-5 max-w-sm">
        <p className="text-6xl font-bold text-text-muted">404</p>
        <h2 className="text-xl font-semibold text-text-primary">页面不存在</h2>
        <p className="text-sm text-text-secondary">你访问的页面不存在或已被移除</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand text-white rounded-lg text-sm font-medium hover:bg-brand-hover transition-colors"
        >
          <Home className="w-4 h-4" />
          返回首页
        </Link>
      </div>
    </div>
  );
}
