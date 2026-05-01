import api from '../lib/api';

export interface ImportTaskResult {
  source_url: string;
  audio_path: string;
  transcription: {
    text: string;
    segments: { start: number; end: number; text: string }[];
    duration: number;
  };
}

export interface ImportTaskStatus {
  task_id: string;
  status: 'pending' | 'processing' | 'success' | 'failed';
  meta?: { stage?: string; url?: string };
  result?: ImportTaskResult | null;
  error?: string | null;
}

export async function importFromUrl(url: string): Promise<{ task_id: string; status: string; message: string; result?: any }> {
  const { data } = await api.post('/import/url', { url }, { timeout: 180000 });
  return data;
}

export async function getImportTaskStatus(taskId: string): Promise<ImportTaskStatus> {
  const { data } = await api.get(`/import/task/${taskId}`);
  return data;
}
