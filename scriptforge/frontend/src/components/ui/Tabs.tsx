import { ReactNode } from 'react';

interface Tab {
  key: string;
  label: string;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
  className?: string;
}

export default function Tabs({ tabs, active, onChange, className = '' }: TabsProps) {
  return (
    <div className={`flex gap-1 border-b border-border-default ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-4 py-2.5 text-sm font-medium transition-colors duration-150 ease-[cubic-bezier(0.4,0,0.2,1)] relative cursor-pointer
            ${active === tab.key ? 'text-brand' : 'text-text-secondary hover:text-text-primary'}`}
        >
          {tab.label}
          {active === tab.key && (
            <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-brand rounded-full" />
          )}
        </button>
      ))}
    </div>
  );
}
