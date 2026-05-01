import { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  hoverable?: boolean;
  className?: string;
  onClick?: () => void;
}

export default function Card({ children, hoverable = false, className = '', onClick }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`bg-bg-card border border-border-default rounded-lg p-4 transition-all duration-150 ease-[cubic-bezier(0.4,0,0.2,1)]
        ${hoverable ? 'hover:border-border-focus cursor-pointer' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}`}
    >
      {children}
    </div>
  );
}
