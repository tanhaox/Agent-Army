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
