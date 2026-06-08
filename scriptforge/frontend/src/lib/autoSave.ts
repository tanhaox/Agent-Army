/**
 * Auto-save draft for LearnPage — persists editing progress to localStorage
 * so users don't lose work on accidental page refresh.
 */

export interface LineData {
  timestamp: string;
  seconds: number;
  text: string;
  role: string;
  emotion: string;
  materialId: string;
}

interface DraftData {
  timestamp: number;
  materials: { id: string; editedText: string; selected: boolean }[];
  lineData: LineData[];
  anchorName?: string;
}

const STORAGE_KEY = 'scriptforge_learn_draft';
const EXPIRE_MS = 24 * 60 * 60 * 1000; // 24 hours
const MAX_BYTES = 4 * 1024 * 1024; // 4 MB safety limit (localStorage ~5 MB)

function byteSize(str: string): number {
  return new Blob([str]).size;
}

export function saveDraft(data: DraftData): void {
  try {
    const payload: DraftData = { ...data, timestamp: Date.now() };
    let json = JSON.stringify(payload);

    // If too large, trim to only the last 3 materials
    if (byteSize(json) > MAX_BYTES && payload.materials.length > 3) {
      payload.materials = payload.materials.slice(-3);
      json = JSON.stringify(payload);
    }

    localStorage.setItem(STORAGE_KEY, json);
  } catch {
    // localStorage full or unavailable — fail silently
  }
}

export function loadDraft(): DraftData | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;

    const data: DraftData = JSON.parse(raw);
    if (Date.now() - data.timestamp > EXPIRE_MS) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

export function clearDraft(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

// ─── Director Mode Draft ─────────────────────────────────────

interface DirectorDraftData {
  timestamp: number;
  roles: { role_type: string; name: string; position?: string; function?: string; persona_id?: string; storyline?: string; perspective?: string; sort_order?: number }[];
  acts: { title: string; task: string; participants: string[]; sort_order?: number }[];
  stepOne: { toneId: string; customTone: string; sceneType: string; topic: string };
}

const DIRECTOR_KEY = 'scriptforge_director_draft';
const DIRECTOR_EXPIRE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days

export function saveDirectorDraft(data: DirectorDraftData): void {
  try {
    const payload: DirectorDraftData = { ...data, timestamp: Date.now() };
    let json = JSON.stringify(payload);

    if (byteSize(json) > MAX_BYTES && payload.roles.length > 5) {
      payload.roles = payload.roles.slice(-5);
      json = JSON.stringify(payload);
    }

    localStorage.setItem(DIRECTOR_KEY, json);
  } catch {
    // localStorage full or unavailable
  }
}

export function loadDirectorDraft(): DirectorDraftData | null {
  try {
    const raw = localStorage.getItem(DIRECTOR_KEY);
    if (!raw) return null;

    const data: DirectorDraftData = JSON.parse(raw);
    if (Date.now() - data.timestamp > DIRECTOR_EXPIRE_MS) {
      localStorage.removeItem(DIRECTOR_KEY);
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

export function clearDirectorDraft(): void {
  try {
    localStorage.removeItem(DIRECTOR_KEY);
  } catch {
    // ignore
  }
}
