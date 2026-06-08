import api from '../lib/api';
import type { AssetItem, AssetListResponse, AssetGroupStats } from '../types';

export type { AssetItem, AssetListResponse, AssetGroupStats };

export async function listAssets(params?: {
  keyword?: string;
  anchor_name?: string;
  task_id?: string;
  asset_type?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}): Promise<AssetListResponse> {
  const { data } = await api.get<AssetListResponse>('/assets', { params });
  return data;
}

export async function getAsset(id: string): Promise<AssetItem> {
  const { data } = await api.get<AssetItem>(`/assets/${id}`);
  return data;
}

export async function deleteAsset(id: string) {
  const { data } = await api.delete(`/assets/${id}`);
  return data;
}

export async function getGroupStats(): Promise<AssetGroupStats[]> {
  const { data } = await api.get<AssetGroupStats[]>('/assets/stats/group-stats');
  return data;
}

export async function updateAsset(id: string, body: { transcription_text: string }): Promise<AssetItem> {
  const { data } = await api.patch<AssetItem>(`/assets/${id}`, body);
  return data;
}

export async function retranscribeAsset(id: string): Promise<{ task_id: string }> {
  const { data } = await api.post(`/assets/${id}/retranscribe`, null, { timeout: 10000 });
  return data;
}

export async function buildVoiceProfile(anchorName: string): Promise<{ status: string; audio_count: number; embedding_dim: number }> {
  const { data } = await api.post('/assets/build-voice-profile', null, { params: { anchor_name: anchorName }, timeout: 300000 });
  return data;
}

export async function batchRetranscribe(anchorName: string): Promise<{
  status: string;
  task_id: string;
  anchor_name: string;
  total: number;
  voice_profile_used: boolean;
}> {
  const { data } = await api.post('/assets/batch-retranscribe', null, { params: { anchor_name: anchorName } });
  return data;
}

export async function getBatchRetranscribeStatus(taskId: string): Promise<{
  task_id: string;
  status: string;
  anchor_name: string;
  total: number;
  progress: number;
  error_message: string | null;
  result_summary: { current_step?: string; message?: string; progress_pct?: number } | null;
}> {
  const { data } = await api.get('/assets/batch-retranscribe-status', { params: { task_id: taskId } });
  return data;
}

export async function listVoiceProfiles(): Promise<{ profiles: { anchor_name: string; audio_count: number; embedding_dim: number }[] }> {
  const { data } = await api.get('/assets/voice-profiles');
  return data;
}
