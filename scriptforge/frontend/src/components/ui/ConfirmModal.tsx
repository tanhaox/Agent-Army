import { createPortal } from 'react-dom';
import Button from './Button';

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmText?: string;
  confirmVariant?: 'danger' | 'warning' | 'primary';
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

const BORDER_MAP: Record<string, string> = {
  danger: 'border-error/40',
  warning: 'border-yellow-500/40',
  primary: 'border-brand/40',
};

export default function ConfirmModal({
  open, title, message, confirmText = '确认删除',
  confirmVariant = 'danger', loading = false, onConfirm, onCancel,
}: ConfirmModalProps) {
  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-[8px]" onClick={onCancel} />
      <div
        className={`relative bg-bg-card border ${BORDER_MAP[confirmVariant] || BORDER_MAP.danger} rounded-xl w-[400px] p-6 space-y-4 animate-[scaleIn_150ms_ease]`}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold text-text-primary">{title}</h3>
        <p className="text-sm text-text-secondary leading-relaxed">{message}</p>
        <div className="flex gap-3 justify-end">
          <Button variant="secondary" size="sm" onClick={onCancel}>取消</Button>
          <Button variant={confirmVariant === 'primary' ? 'primary' : 'danger'} size="sm" loading={loading} onClick={onConfirm}>
            {confirmText}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
