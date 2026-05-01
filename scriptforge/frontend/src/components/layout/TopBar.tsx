import { useLocation, Link } from 'react-router-dom';
import { CircleDot, ChevronRight } from 'lucide-react';

const ROUTE_META: Record<string, { label: string; parent?: string }> = {
  '/': { label: '脚本工作室' },
  '/learn': { label: '学习中心' },
  '/personas': { label: '人设工坊' },
  '/scripts': { label: '脚本工作室' },
  '/creator': { label: '角色工坊' },
  '/settings': { label: '系统设置' },
};

export default function TopBar() {
  const location = useLocation();
  const meta = ROUTE_META[location.pathname];
  const label = meta?.label || '页面不存在';

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-border-default bg-bg-primary shrink-0">
      <div className="flex items-center gap-1.5 text-sm">
        <Link to="/" className="text-text-muted hover:text-text-secondary transition-colors">ScriptForge</Link>
        <ChevronRight className="w-3.5 h-3.5 text-text-muted" />
        <span className="text-text-primary font-medium">{label}</span>
      </div>
      <div className="flex items-center gap-2 text-xs text-success">
        <CircleDot className="w-3 h-3 fill-success" />
        <span>系统就绪</span>
      </div>
    </header>
  );
}
