// 人设分析请求
export interface AnalyzeRequest {
  persona_name?: string;
  slices: { text: string; source_url?: string }[];
  force_new?: boolean;
}

// 人设分析结果
export interface PersonaAnalysisResult {
  action: 'created' | 'updated';
  persona_id: string;
  version: number;
}

export interface NarrativeStyle {
  opening_pattern: {
    style: string;
    avg_rounds_to_first_hook: number;
    typical_phrase: string;
  };
  reversal_pattern: {
    timing: string;
    method: string;
    signals: string[];
  };
  rhythm_anchors: {
    climax_interval: string;
    post_climax_behavior: string;
    breathing_control: string;
  };
  closing_pattern: {
    style: string;
    typical_signal: string;
  };
  narrative_units: Array<{
    name: string;
    steps: string[];
    usage_frequency: string;
  }>;
  pacing_summary: string;
}

// 人设详情
export interface PersonaDetail {
  id: string;
  name: string;
  global_style: string;
  catchphrases: string[] | null;
  reaction_patterns: Record<string, string> | null;
  sentence_templates: string[] | null;
  core_values: string[] | null;
  language_style: Record<string, string | number> | null;
  tone_adaptation: Record<string, string> | null;
  narrative_style: NarrativeStyle | null;
  version: number;
  is_active: boolean;
  created_at: string | null;
  slice_count: number;
  version_notes: { version: number; summary: string; added_slices: number }[] | null;
}

// 人设列表
export interface PersonaListItem {
  id: string;
  name: string;
  global_style: string;
  version: number;
  is_active: boolean;
  created_at: string | null;
}

export interface PersonaListResponse {
  total: number;
  skip: number;
  limit: number;
  items: PersonaListItem[];
}

// 转写结果
export interface TranscriptionResult {
  text: string;
  segments: { start: number; end: number; text: string }[];
  duration: number;
}

// 任务状态
export interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILURE';
  result?: TranscriptionResult[] | null;
  error?: string | null;
}

// 脚本
export interface Dialogue {
  turn: number;
  speaker: string;
  text: string;
  emotion: string;
  is_highlight: boolean;
  highlight_title: string;
}

export interface Script {
  id: string;
  title: string;
  dialogues: Dialogue[];
}

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

export interface AnchorProfile {
  anchor_name: string;
  anchor_id: string;
  follower_count: number;
  like_count: number;
  homepage_url: string;
  avatar_url?: string | null;
  bio?: string | null;
}
