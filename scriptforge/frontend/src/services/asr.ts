import api from '../lib/api';
import type { TranscriptionResult, TaskStatus } from '../types';

export async function transcribeFile(file: File): Promise<TranscriptionResult> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post<TranscriptionResult>('/asr/transcribe', form);
  return data;
}

export async function batchTranscribe(files: File[]): Promise<{ task_id: string; status: string; file_count: number }> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const { data } = await api.post('/asr/batch', form);
  return data;
}

export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const { data } = await api.get<TaskStatus>(`/asr/task/${taskId}`);
  return data;
}
