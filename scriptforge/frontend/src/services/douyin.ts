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

// ── Async task mode ──

export interface DouyinTaskSubmitResponse {
  task_id: string;
  status: 'queued';
  message: string;
}

export interface DouyinTaskStatus {
  task_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  step?: string;
  message?: string;
  current?: number;
  total?: number;
  progress_pct?: number;
  meta?: Record<string, any>;
  profile?: AnchorProfile | null;
  follower_count?: number;
  partial_success?: boolean;
  successful_count?: number;
  total_count?: number;
  failed_count?: number;
  failed_videos?: Array<{ desc: string; error: string }>;
  result?: DouyinTaskResult | null;
  result_summary?: {
    persona_id?: string;
    persona_name?: string;
    video_count?: number;
    follower_count?: number;
    successful_count?: number;
    total_count?: number;
    failed_count?: number;
  };
  error?: string;
}

export interface DouyinTaskResult {
  status: string;
  partial_success?: boolean;
  persona_id: string | null;
  profile: AnchorProfile | null;
  analysis: Record<string, any> | null;
  narrative: Record<string, any> | null;
  strategies: { extracted: number; results: any[] };
  materials: any[];
  follower_count: number;
  enhanced_data: boolean;
  successful_count?: number;
  total_count?: number;
  failed_count?: number;
  failed_videos?: Array<{ desc: string; error: string }>;
}

export async function submitDouyinUserTask(
  url: string,
  count: number = 5,
): Promise<DouyinTaskSubmitResponse> {
  const { data } = await api.post(
    '/import/douyin-user/task',
    { url, count },
    { timeout: 30000 },
  );
  return data;
}

export async function getDouyinTaskStatus(taskId: string): Promise<DouyinTaskStatus> {
  const { data } = await api.get(`/import/task/${taskId}`);
  return data;
}

export async function listDouyinTasks(): Promise<{ tasks: any[]; count: number }> {
  const { data } = await api.get('/import/douyin-user/tasks');
  return data;
}
