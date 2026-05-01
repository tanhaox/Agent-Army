import api from '../lib/api';

export interface StrategyItem {
  id: string;
  pattern_type: string;
  description: string;
  sentence_templates: string[];
  emotional_curve: string;
  tags: string[];
  quality_score: number;
}

export interface ExtractResult {
  extracted: number;
  strategies: StrategyItem[];
}

export interface StrategyListItem {
  id: string;
  title: string;
  category: string;
  pattern_type: string | null;
  extracted_pattern: string;
  tags: string[] | null;
  quality_score: number;
  usage_count: number;
  created_at: string | null;
}

export interface StrategyListResponse {
  total: number;
  page: number;
  page_size: number;
  items: StrategyListItem[];
}

export async function extractStrategies(
  text: string,
  category: string,
  materialId?: string,
): Promise<ExtractResult> {
  const { data } = await api.post<ExtractResult>('/strategies/extract', {
    text,
    category,
    material_id: materialId,
  }, { timeout: 120000 });
  return data;
}

export async function batchExtractStrategies(
  items: { text: string; category: string; materialId?: string }[],
): Promise<{ total_extracted: number; results: ExtractResult[] }> {
  const { data } = await api.post('/strategies/batch-extract', {
    items: items.map((i) => ({
      text: i.text,
      category: i.category,
      material_id: i.materialId,
    })),
  }, { timeout: 180000 });
  return data;
}

export interface StrategyDetail {
  id: string;
  title: string;
  category: string;
  pattern_type: string | null;
  extracted_pattern: string;
  emotional_curve: Record<string, string> | null;
  sentence_templates: string[] | null;
  tags: string[] | null;
  quality_score: number;
  usage_count: number;
  source_text: string | null;
  created_at: string | null;
}

export async function getStrategy(id: string): Promise<StrategyDetail> {
  const { data } = await api.get<StrategyDetail>(`/strategies/${id}`);
  return data;
}

export async function listStrategies(
  page = 1,
  pageSize = 20,
  category?: string,
  patternType?: string,
): Promise<StrategyListResponse> {
  const params: Record<string, any> = { page, page_size: pageSize };
  if (category) params.category = category;
  if (patternType) params.pattern_type = patternType;
  const { data } = await api.get<StrategyListResponse>('/strategies/', { params });
  return data;
}

export async function deleteStrategy(id: string) {
  const { data } = await api.delete(`/strategies/${id}`);
  return data;
}
