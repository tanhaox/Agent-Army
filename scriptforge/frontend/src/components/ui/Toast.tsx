import { ReactNode, useEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { X, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning';

interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

let toastId = 0;
const listeners: Set<(toasts: ToastItem[]) => void> = new Set();
let currentToasts: ToastItem[] = [];

function emitChange() {
  listeners.forEach((fn) => fn([...currentToasts]));
}

export function toast(type: ToastType, message: string) {
  const id = ++toastId;
  currentToasts = [...currentToasts, { id, type, message }];
  emitChange();
  setTimeout(() => {
    currentToasts = currentToasts.filter((t) => t.id !== id);
    emitChange();
  }, 3000);
}

const ICON_MAP: Record<ToastType, ReactNode> = {
  success: <CheckCircle className="w-4 h-4 text-success" />,
  error: <XCircle className="w-4 h-4 text-error" />,
  warning: <AlertTriangle className="w-4 h-4 text-warning" />,
};

const BORDER_MAP: Record<ToastType, string> = {
  success: 'border-l-success',
  error: 'border-l-error',
  warning: 'border-l-warning',
};

function ToastContainer({ toasts }: { toasts: ToastItem[] }) {
  return createPortal(
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-3 bg-bg-card border border-border-default border-l-[3px] ${BORDER_MAP[t.type]} rounded-md px-4 py-3 shadow-lg animate-[slideInRight_200ms_ease]`}
        >
          {ICON_MAP[t.type]}
          <span className="text-sm text-text-primary">{t.message}</span>
          <button
            onClick={() => {
              currentToasts = currentToasts.filter((x) => x.id !== t.id);
              emitChange();
            }}
            className="ml-2 text-text-muted hover:text-text-primary"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>,
    document.body
  );
}

export default function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const handleChange = useCallback((t: ToastItem[]) => setToasts(t), []);

  useEffect(() => {
    listeners.add(handleChange);
    return () => {
      listeners.delete(handleChange);
    };
  }, [handleChange]);

  return (
    <>
      {children}
      <ToastContainer toasts={toasts} />
    </>
  );
}
