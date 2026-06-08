import type { LucideIcon } from 'lucide-react';
import Button from './Button';

interface Action {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
}

interface Props {
  icon: LucideIcon;
  title: string;
  description?: string;
  actions?: Action[];
}

export default function EmptyState({ icon: Icon, title, description, actions }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon className="w-12 h-12 text-text-muted mb-3" />
      <h3 className="text-base font-semibold text-text-primary">{title}</h3>
      {description && (
        <p className="text-sm text-text-secondary mt-1.5 max-w-[400px] leading-relaxed">{description}</p>
      )}
      {actions && actions.length > 0 && (
        <div className="flex gap-3 mt-4">
          {actions.map((a, i) => (
            <Button key={i} variant={a.variant || 'secondary'} size="sm" onClick={a.onClick}>
              {a.label}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
