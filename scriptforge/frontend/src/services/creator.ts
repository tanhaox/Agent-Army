import api from '../lib/api';

export interface CreatorPersonaResult {
  persona_name: string;
  global_style: string;
  language_style: Record<string, number>;
  catchphrases: string[];
  reaction_patterns: Record<string, string>;
  sentence_templates: string[];
  core_values: string[];
  tone_adaptation: Record<string, number>;
  style_summary: string;
  recommended_scenarios?: string[];
}

export interface GuestCard {
  name: string;
  age_range: string;
  occupation: string;
  personality: string;
  core_issue: string;
  speaking_style: string;
  tags: string[];
  expected_reaction: string;
}

export async function createPersona(requirements: string): Promise<{ status: string; persona: CreatorPersonaResult }> {
  const { data } = await api.post('/creator/persona', { requirements }, { timeout: 120000 });
  return data;
}

export async function createGuests(topic: string, count = 20): Promise<{ status: string; count: number; guests: GuestCard[] }> {
  const { data } = await api.post('/creator/guests', { topic, count }, { timeout: 120000 });
  return data;
}

export async function fusePersonas(
  personaIdA: string,
  personaIdB: string,
  ratio = 0.5,
): Promise<{ status: string; persona: CreatorPersonaResult }> {
  const { data } = await api.post('/creator/fusion', { persona_id_a: personaIdA, persona_id_b: personaIdB, ratio }, { timeout: 120000 });
  return data;
}

export async function savePersona(generatedData: any): Promise<{ status: string; persona_id: string }> {
  const { data } = await api.post('/creator/save', { generated_data: generatedData });
  return data;
}
