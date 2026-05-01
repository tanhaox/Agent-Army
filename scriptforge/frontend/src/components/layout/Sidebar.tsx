import { NavLink } from 'react-router-dom';
import { BookOpen, Users, FileText, Settings, Sparkles, Wand2 } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/learn', label: '学习中心', icon: BookOpen },
  { to: '/personas', label: '人设工坊', icon: Users },
  { to: '/creator', label: '角色工坊', icon: Wand2 },
  { to: '/scripts', label: '脚本工作室', icon: FileText },
  { to: '/settings', label: '系统设置', icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="w-[240px] min-h-screen flex flex-col bg-bg-sidebar border-r border-border-default shrink-0">
      {/* Logo */}
      <div className="h-16 flex items-center gap-2.5 px-5 border-b border-border-default">
        <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center">
          <Sparkles className="w-4.5 h-4.5 text-white" />
        </div>
        <span className="text-lg font-semibold tracking-tight text-text-primary">
          ScriptForge
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] ${
                isActive
                  ? 'bg-bg-hover text-text-primary border-l-2 border-brand -ml-0.5 pl-[10px]'
                  : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
              }`
            }
          >
            <Icon className="w-[18px] h-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-border-default">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-bg-hover flex items-center justify-center text-text-muted text-xs font-medium">
            U
          </div>
          <span className="text-sm text-text-secondary">Demo User</span>
        </div>
      </div>
    </aside>
  );
}
