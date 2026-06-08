/**
 * 分镜相关 API 调用封装。
 */

import apiClient from './index'

/** 分镜响应体。 */
export interface StoryboardResponse {
  id: string
  script_id: string | null
  project_id: string | null
  episode_no: number
  shot_no: number
  shot_type: string
  camera_move: string
  action: string
  dialogue: string | null
  emotion: string
  vfx: string
  environment: string
  lighting: string
  prompt_text: string | null
  negative_prompt: string | null
  reference_image_url: string | null
  approved: boolean
  duration_seconds: number
  is_key_moment: boolean
  pregen_materials: Record<string, unknown> | null
  video_url: string | null
  video_status: string
  video_task_id: string | null
  audio_config: AudioConfig | null
  director_analysis: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

/** 音频配置。 */
export interface AudioConfig {
  voiceover?: string
  sound_effects?: string[]
  bgm?: string
}

/** 更新分镜请求体。 */
export interface StoryboardUpdate {
  script_id?: string | null
  episode_no?: number
  shot_no?: number
  shot_type?: string
  camera_move?: string
  action?: string
  dialogue?: string | null
  emotion?: string
  vfx?: string | null
  environment?: string
  lighting?: string
  prompt_text?: string | null
  negative_prompt?: string | null
  reference_image_url?: string | null
  approved?: boolean
  duration_seconds?: number
  is_key_moment?: boolean
  pregen_materials?: Record<string, unknown> | null
  video_url?: string | null
  video_status?: string | null
  video_task_id?: string | null
  audio_config?: AudioConfig | null
}

/** 创建分镜请求体。 */
export interface StoryboardCreate {
  script_id?: string | null
  project_id?: string | null
  episode_no: number
  shot_no: number
  shot_type: string
  camera_move: string
  action: string
  dialogue?: string | null
  emotion: string
  vfx?: string
  environment: string
  lighting: string
  prompt_text?: string | null
  negative_prompt?: string | null
  reference_image_url?: string | null
  duration_seconds?: number
  is_key_moment?: boolean
}

/** 生成提示词请求体。 */
export interface PromptGenerateRequest {
  shot_type: string
  camera_move: string
  action: string
  emotion: string
  environment: string
  lighting: string
  vfx?: string
}

/** 剧本响应体（简化）。 */
export interface ScriptResponse {
  id: string
  project_name: string
  theme: string
  created_at: string
}

export const storyboardsApi = {
  /** 创建分镜。 */
  create: (data: StoryboardCreate) =>
    apiClient.post<StoryboardResponse>('/storyboards', data),

  /** 获取分镜列表。 */
  list: (scriptId?: string, projectId?: string) =>
    apiClient.get<StoryboardResponse[]>('/storyboards', {
      params: {
        ...(scriptId ? { script_id: scriptId } : {}),
        ...(projectId ? { project_id: projectId } : {}),
      },
    }),

  /** 获取分镜详情。 */
  getById: (id: string) =>
    apiClient.get<StoryboardResponse>(`/storyboards/${id}`),

  /** 更新分镜。 */
  update: (id: string, data: StoryboardUpdate) =>
    apiClient.put<StoryboardResponse>(`/storyboards/${id}`, data),

  /** 删除分镜。 */
  delete: (id: string) =>
    apiClient.delete(`/storyboards/${id}`),

  /** 生成视频提示词（不保存）。 */
  generatePrompt: (data: PromptGenerateRequest) =>
    apiClient.post<{ prompt_text: string }>('/storyboards/generate-prompt', data),

  /** 重新生成并保存视频提示词。 */
  regeneratePrompt: (id: string) =>
    apiClient.post<StoryboardResponse>(`/storyboards/${id}/regenerate-prompt`),

  /** DeepSeek 增强提示词。 */
  enhancePrompt: (id: string) =>
    apiClient.post<{ standard: string; enhanced: string; negative_prompt: string }>(`/storyboards/${id}/enhance-prompt`),

  /** 自动分配时长。 */
  autoAssignDurations: (projectId: string, targetDuration?: number) =>
    apiClient.post<{ detail: string; updated_count: number }>('/storyboards/auto-assign-durations', null, {
      params: { project_id: projectId, target_duration: targetDuration || 75 },
    }),

  /** 节奏分析。 */
  rhythmAnalysis: (projectId: string) =>
    apiClient.get<{
      overall_score: number
      per_episode: Record<number, {
        episode_no: number
        shot_count: number
        total_duration: number
        key_moment_count: number
        emotion_peak: number
        has_suspense_ending: boolean
        score: number
        issues: string[]
        suggestions: string[]
      }>
      global_suggestions: string[]
    }>(`/storyboards/rhythm-analysis/${projectId}`),

  /** 素材预生成。 */
  pregenMaterials: (id: string) =>
    apiClient.post<StoryboardResponse>(`/storyboards/${id}/pregen-materials`),

  /** 生成单个素材图片。 */
  generateMaterial: (id: string, reqId: string, prompt: string) =>
    apiClient.post<StoryboardResponse>(`/storyboards/${id}/materials/${reqId}/generate`, { prompt }),

  /** 更新素材提示词。 */
  updateMaterialPrompt: (id: string, reqId: string, prompt: string) =>
    apiClient.put<StoryboardResponse>(`/storyboards/${id}/materials/${reqId}/prompt`, { prompt }),

  /** 上传素材图片。 */
  uploadMaterial: (id: string, file: File, materialType: string = 'background', materialId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    const params = new URLSearchParams({ material_type: materialType })
    if (materialId) params.set('material_id', materialId)
    return apiClient.post<StoryboardResponse>(
      `/storyboards/${id}/upload-material?${params.toString()}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  /** 生成镜头视频。 */
  generateVideo: (id: string) =>
    apiClient.post<{ task_id: string; storyboard_id: string; status: string }>(`/storyboards/${id}/generate-video`),

  /** 查询视频生成状态。 */
  getVideoStatus: (id: string) =>
    apiClient.get<{ status: string; video_url: string | null; task_id?: string }>(`/storyboards/${id}/video-status`),

  /** 更新音频配置。 */
  updateAudioConfig: (id: string, audioConfig: AudioConfig) =>
    apiClient.put<StoryboardResponse>(`/storyboards/${id}/audio-config`, { audio_config: audioConfig }),

  /** 智能导演规划。 */
  directorPlan: (id: string, regenerate: boolean = false) =>
    apiClient.post<Record<string, unknown>>(`/storyboards/${id}/director-plan`, { regenerate }),

  /** 更新导演分析结果（如删除素材引用后保存）。 */
  updateDirectorAnalysis: (id: string, directorAnalysis: Record<string, unknown>) =>
    apiClient.put<StoryboardResponse>(`/storyboards/${id}/director-analysis`, { director_analysis: directorAnalysis }),

  /** 获取候选视频列表。 */
  getVideoCandidates: (id: string) =>
    apiClient.get<VideoCandidate[]>(`/storyboards/${id}/video-candidates`),

  /** 触发下载候选视频（浏览器新标签页下载）。 */
  downloadVideo: (id: string, taskId: string) => {
    window.open(`/api/storyboards/${id}/video-candidates/${taskId}/download`, '_blank')
  },

  /** 批量生成视频。 */
  batchGenerate: (storyboardIds: string[], concurrency: number = 3) =>
    apiClient.post<BatchGenerateResult[]>('/storyboards/batch-generate-videos', {
      storyboard_ids: storyboardIds,
      concurrency,
    }),

  /** 批量查询视频状态。 */
  batchStatus: (storyboardIds: string[]) =>
    apiClient.get<BatchStatusItem[]>('/storyboards/batch-status', {
      params: { storyboard_ids: storyboardIds.join(',') },
    }),
}

export const scriptsApi = {
  /** 获取剧本列表。 */
  list: () =>
    apiClient.get<ScriptResponse[]>('/scripts'),
}

/** 视频候选。 */
export interface VideoCandidate {
  task_id: string
  video_url: string
  created_at: string | null
  duration: string
  mode: string
  aspect_ratio: string
}

/** 批量生成单项结果。 */
export interface BatchGenerateResult {
  storyboard_id: string
  task_id?: string
  status: string
  detail?: string
}

/** 批量状态查询单项。 */
export interface BatchStatusItem {
  storyboard_id: string
  episode_no: number
  shot_no: number
  video_status: string
  video_url: string | null
  video_task_id: string | null
  task_status?: string
  detail?: string
}

/** 可引用素材项。 */
export interface ReferenceableItem {
  id: string
  name: string
  type: string
  thumbnail_url: string
  reference_mark: string
}

/** 可引用素材分类响应。 */
export interface ReferenceableMaterials {
  characters: ReferenceableItem[]
  scenes: ReferenceableItem[]
  props: ReferenceableItem[]
  generated_materials: ReferenceableItem[]
}

export const referenceApi = {
  /** 获取项目可引用素材列表（角色 + 场景 + 道具 + 已生成素材）。 */
  list: (projectId: string) =>
    apiClient.get<ReferenceableMaterials>(`/projects/${projectId}/referenceable-materials`),
}
