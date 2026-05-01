import api from '../lib/api';

export interface SensitiveWordItem {
  id: string;
  word: string;
  category: string | null;
  severity: string;
  is_active: boolean;
  created_at: string | null;
}

export interface SensitiveWordListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SensitiveWordItem[];
}

export async function listSensitiveWords(
  page = 1,
  pageSize = 50,
  category?: string,
  severity?: string,
  search?: string,
): Promise<SensitiveWordListResponse> {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (category) params.category = category;
  if (severity) params.severity = severity;
  if (search) params.search = search;
  const { data } = await api.get<SensitiveWordListResponse>('/sensitive-words/', { params });
  return data;
}

export async function addSensitiveWord(
  word: string,
  category = '其他',
  severity = 'medium',
): Promise<{ id: string; word: string; category: string; severity: string }> {
  const { data } = await api.post('/sensitive-words/', { word, category, severity });
  return data;
}

export async function batchImportWords(
  words: { word: string; category?: string; severity?: string }[],
): Promise<{ added: number; skipped: number }> {
  const { data } = await api.post('/sensitive-words/batch-import', {
    words: words.map((w) => ({
      word: w.word,
      category: w.category || '其他',
      severity: w.severity || 'medium',
    })),
  });
  return data;
}

export async function deleteSensitiveWord(id: string) {
  const { data } = await api.delete(`/sensitive-words/${id}`);
  return data;
}
