import api from '../lib/api';

export interface CookieStatus {
  status: 'configured' | 'not_configured';
  cookie_count?: number;
}

export interface CookieItem {
  name: string;
  value: string;
  domain?: string;
  path?: string;
}

export async function getDouyinCookieStatus(): Promise<CookieStatus> {
  const { data } = await api.get('/settings/douyin-cookie');
  return data;
}

export async function updateDouyinCookie(cookies: CookieItem[]): Promise<CookieStatus> {
  const { data } = await api.put('/settings/douyin-cookie', { cookies });
  return data;
}

// ── User preferences (backend-persisted) ────────────────────────

export interface UserSettings {
  emotion_curve: string;
  strategy_mix: string;
  api_base_url: string;
  api_key_configured: boolean;
  api_key_masked: string;
  plan_type: string;
  quota_total: number;
  quota_used: number;
  username: string;
  email: string | null;
}

export async function getUserSettings(): Promise<UserSettings> {
  const { data } = await api.get('/settings/');
  return data;
}

export async function updateUserSettings(
  settings: Partial<Pick<UserSettings, 'emotion_curve' | 'strategy_mix' | 'api_base_url'> & { api_key?: string }>
): Promise<UserSettings> {
  const { data } = await api.patch('/settings/', settings);
  return data;
}
