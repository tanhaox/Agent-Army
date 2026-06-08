import api from '../lib/api';
import type { TaskRecord, TaskRecordDetail, TaskRecordListResponse } from '../types';

export async function listTaskRecords(params?: {
  status?: string;
  anchor_name?: string;
  page?: number;
  page_size?: number;
}): Promise<TaskRecordListResponse> {
  const { data } = await api.get<TaskRecordListResponse>('/task-records', { params });
  return data;
}

export async function getTaskRecord(taskId: string): Promise<TaskRecordDetail> {
  const { data } = await api.get<TaskRecordDetail>(`/task-records/${taskId}`);
  return data;
}
