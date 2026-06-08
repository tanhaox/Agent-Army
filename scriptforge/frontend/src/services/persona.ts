import api from '../lib/api';
import type { AnalyzeRequest, PersonaAnalysisResult, PersonaDetail, PersonaListResponse } from '../types';

export async function analyzePersona(req: AnalyzeRequest): Promise<PersonaAnalysisResult> {
  const { data } = await api.post<PersonaAnalysisResult>('/persona/analyze', req);
  return data;
}

export async function getPersona(id: string): Promise<PersonaDetail> {
  const { data } = await api.get<PersonaDetail>(`/persona/${id}`);
  return data;
}

export async function listPersonas(skip = 0, limit = 20): Promise<PersonaListResponse> {
  const { data } = await api.get<PersonaListResponse>('/persona/', { params: { skip, limit } });
  return data;
}

export async function appendSlices(
  personaId: string,
  texts: string[],
  metadata?: { emotion_tag?: string; action_desc?: string }
) {
  const { data } = await api.post(`/persona/${personaId}/append`, {
    texts,
    ...metadata,
  });
  return data;
}

export async function getPersonaSlices(personaId: string) {
  const { data } = await api.get(`/persona/${personaId}/slices`);
  return data;
}

export async function patchPersona(
  id: string,
  fields: {
    global_style?: string;
    catchphrases?: string[];
    reaction_patterns?: Record<string, string>;
    sentence_templates?: string[];
    core_values?: string[];
    language_style?: Record<string, number>;
    language_style_v2?: Record<string, unknown>;
    lingo_map?: Record<string, unknown>;
    tone_adaptation?: Record<string, number>;
    is_template?: boolean;
    is_active?: boolean;
    tags?: string[];
  }
) {
  const { data } = await api.patch(`/persona/${id}`, fields);
  return data;
}

export async function deletePersonaSlice(personaId: string, sliceId: string) {
  const { data } = await api.delete(`/persona/${personaId}/slices/${sliceId}`);
  return data;
}

export async function rollbackPersona(personaId: string, targetVersion: number) {
  const { data } = await api.post(`/persona/${personaId}/rollback`, { target_version: targetVersion });
  return data;
}

export async function getAnchorsWithoutPersona(): Promise<{ anchor_name: string; transcript_count: number }[]> {
  const { data } = await api.get('/persona/anchors-without-persona');
  return data;
}

export async function generatePersonaFromAssets(anchorName: string): Promise<{
  id: string; name: string; source_anchor_name: string; slice_count: number; completeness_score: number;
}> {
  const { data } = await api.post('/persona/generate-from-assets', null, { params: { anchor_name: anchorName } });
  return data;
}

export async function deletePersona(id: string) {
  const { data } = await api.delete(`/persona/${id}`);
  return data;
}

export async function importLingo(
  personaId: string,
  file: File,
): Promise<{ imported_count: number; skipped_count: number; total_lines: number; updated_map: Record<string, string> }> {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post(`/persona/${personaId}/lingo/import`, form);
  return data;
}
