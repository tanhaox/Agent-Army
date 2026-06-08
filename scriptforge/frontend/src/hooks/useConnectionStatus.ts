import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from '../components/ui/Toast';

// ── Module-level state (shared across all hook instances) ────────

let _isOnline = true;
let _consecutiveFailures = 0;
const listeners = new Set<() => void>();

function emitChange() {
  for (const fn of listeners) fn();
}

/** Called from api.ts on request success — resets failure counter. */
export function reportRequestSuccess() {
  if (_consecutiveFailures > 0) _consecutiveFailures = 0;
  if (!_isOnline) {
    _isOnline = true;
    emitChange();
  }
}

/** Called from api.ts on request failure — triggers offline after 3 consecutive failures. */
export function reportRequestFailure() {
  _consecutiveFailures++;
  if (_consecutiveFailures >= 3 && _isOnline) {
    _isOnline = false;
    emitChange();
  }
}

// ── React hook ──────────────────────────────────────────────────

export function useConnectionStatus() {
  const [isOnline, setIsOnline] = useState(_isOnline);
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    const update = () => setIsOnline(_isOnline);
    listeners.add(update);
    return () => { listeners.delete(update); };
  }, []);

  // When offline, poll /api/health every 10s to detect recovery
  const checkHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/health', { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        reportRequestSuccess();
        toast('success', '服务已恢复');
      }
    } catch { /* still offline */ }
  }, []);

  useEffect(() => {
    if (isOnline) {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = undefined; }
      return;
    }
    // Immediately check once
    checkHealth();
    pollRef.current = setInterval(checkHealth, 10000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [isOnline, checkHealth]);

  return { isOnline };
}
