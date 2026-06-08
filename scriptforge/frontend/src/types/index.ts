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

export interface NarrativeModel {
  opening_style: string;
  reversal_timing: string;
  rhythm_summary: string;
  narrative_units: Array<{
    name: string;
    steps: string[];
    usage_frequency: string;
  }>;
  catchphrase_count: number;
  distinctive_features: string[];
  completeness_score: number;
}

export interface LanguageStyleV2 {
  rhetorical_question_freq: number;
  interrupt_tendency: number;
  sharpness: number;
  self_deprecation: number;
  humor_type: string;
  pace: string;
  max_pause_seconds: number;
  grab_floor_freq: number;
  monologue_length: string;
  empathy_style: string;
  emotional_volatility: number;
  emotional_triggers: string[];
  metaphor_domains: string[];
  topic_preferences: string[];
  punchline_density: number;
  opening_phrase: string | null;
  transition_phrase: string | null;
  closing_phrase: string | null;
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
  language_style_v2: LanguageStyleV2 | null;
  tone_adaptation: Record<string, string | number> | null;
  narrative_style: NarrativeStyle | null;
  version: number;
  is_active: boolean;
  is_template: boolean;
  created_at: string | null;
  slice_count: number;
  version_notes: { version: number; summary: string; added_slices: number }[] | null;
  source_anchor_name?: string | null;
  source_anchor_id?: string | null;
  source_homepage_url?: string | null;
  narrative_model?: NarrativeModel | null;
  tags?: string[] | null;
  lingo_map?: Record<string, string> | null;
  degraded?: boolean;
}

// 人设列表
export interface PersonaListItem {
  id: string;
  name: string;
  global_style: string;
  version: number;
  is_active: boolean;
  created_at: string | null;
  source_anchor_name?: string | null;
  source_anchor_id?: string | null;
  source_homepage_url?: string | null;
  source_follower_count?: number | null;
  narrative_model?: NarrativeModel | null;
  tags?: string[] | null;
  lingo_map?: Record<string, string> | null;
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

// 素材资产
export interface AssetItem {
  id: string;
  task_id: string;
  anchor_name: string;
  video_title: string;
  asset_type: 'video' | 'audio' | 'transcript';
  file_path: string;
  file_size: number;
  duration: number;
  transcription_text: string | null;
  video_url: string | null;
}

export interface AssetListResponse {
  items: AssetItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetGroupStats {
  anchor_name: string;
  persona_id: string | null;
  persona_name: string | null;
  video_count: number;
  audio_count: number;
  transcript_count: number;
  total_size: number;
}

// 任务记录
export interface TaskRecord {
  id: string;
  task_id: string;
  trigger: 'stream' | 'celery' | 'douyin_user_import' | 'batch_retranscribe' | 'batch_transcribe';
  url: string;
  anchor_name: string;
  anchor_avatar?: string | null;
  follower_count: number;
  status: 'running' | 'completed' | 'failed';
  error_message?: string | null;
  video_count: number;
  downloaded_count: number;
  transcribed_count: number;
  persona_id?: string | null;
  persona_name?: string | null;
  result_summary?: { current_step?: string; message?: string; progress_pct?: number } | null;
  created_at: string;
}

export interface TaskRecordDetail extends TaskRecord {
  result_summary: Record<string, unknown> | null;
}

export interface TaskRecordListResponse {
  items: TaskRecord[];
  total: number;
  page: number;
  page_size: number;
}

// 编导要求
export interface DirectorRole {
  id?: string;
  role_type: 'anchor' | 'caller' | 'extra';
  name: string;
  position?: string;
  function?: string;
  persona_id?: string;
  persona_name?: string;
  storyline?: string;
  perspective?: 'first_person_experience' | 'first_person_participant' | 'third_person';
  sort_order?: number;
}

export interface DirectorAct {
  id?: string;
  title: string;
  task: string;
  participants: string[];
  sort_order?: number;
}
