import api from '../lib/api';
import type { Dialogue } from '../types';

export interface GenerateParams {
  tone_id: string;
  persona_id: string;
  guest_config: {
    name?: string;
    age_range?: string;
    occupation?: string;
    personality?: string;
    core_issue: string;
  };
  emotion_curve?: string;
  strategy_mix?: string;
  hot_topic?: string;
  multi_version?: boolean;
  scene_type?: string;
  enable_caller_enhancement?: boolean;
}

export interface ScriptVersionItem {
  version_id: string;
  version_name: string;
  dialogues: Dialogue[];
  highlights: { turn: number; title: string; reason: string }[];
  compliance: { passed: boolean; hits: any[]; hit_count: number; suggestion: string };
  word_count: number;
  emotion_curve_actual: string[];
  overall_style_note: string;
}

export interface ScriptResult {
  script_id: string;
  title?: string;
  dialogues: Dialogue[];
  compliance: { passed: boolean; hits: any[]; hit_count: number; suggestion: string };
  highlights: { turn: number; title: string; reason: string }[];
  word_count: number;
  emotion_curve_actual: string[];
  overall_style_note: string;
  multi_version?: boolean;
  versions?: ScriptVersionItem[];
  recommended_version?: number;
}

export interface ScriptDetail {
  id: string;
  title: string;
  tone_id: string | null;
  persona_id: string | null;
  script_content: any;
  emotion_curve: string | null;
  strategy_mix: string | null;
  multi_version: boolean;
  word_count: number | null;
  sensitive_hits: any[];
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface ScriptListItem {
  id: string;
  title: string;
  emotion_curve: string | null;
  word_count: number | null;
  status: string;
  created_at: string | null;
}

export async function generateScript(params: GenerateParams): Promise<ScriptResult> {
  const { data } = await api.post<ScriptResult>('/scripts/generate', params, { timeout: 120000 });
  return data;
}

export async function getScript(id: string): Promise<ScriptDetail> {
  const { data } = await api.get<ScriptDetail>(`/scripts/${id}`);
  return data;
}

export async function listScripts(skip = 0, limit = 20) {
  const { data } = await api.get('/scripts/', { params: { skip, limit } });
  return data;
}

export async function updateScript(id: string, scriptContent: any) {
  const { data } = await api.patch(`/scripts/${id}`, { script_content: scriptContent });
  return data;
}

export async function archiveScript(id: string) {
  const { data } = await api.delete(`/scripts/${id}`);
  return data;
}

export async function regeneratePart(id: string, speaker: string) {
  const { data } = await api.post(`/scripts/${id}/regenerate`, { regenerate_speaker: speaker });
  return data;
}
