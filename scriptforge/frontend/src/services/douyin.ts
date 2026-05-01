import api from '../lib/api';
import type { AnchorProfile } from '../types';

export interface DouyinVideoResult {
  index: number;
  aweme_id: string;
  desc: string;
  source_url: string;
  author: string;
  duration: number;
  audio_path?: string;
  status: 'downloaded' | 'failed';
  error?: string;
}

export interface DouyinUserImportResponse {
  total: number;
  downloaded: DouyinVideoResult[];
  failed: DouyinVideoResult[];
}

export async function importDouyinUser(
  url: string,
  count: number = 5,
): Promise<DouyinUserImportResponse> {
  const { data } = await api.post(
    '/import/douyin-user',
    { url, count },
    { timeout: 300000 },
  );
  return data;
}

export async function getUserProfile(url: string): Promise<AnchorProfile> {
  const { data } = await api.post(
    '/import/douyin-user-profile',
    { url },
    { timeout: 60000 },
  );
  return data;
}
