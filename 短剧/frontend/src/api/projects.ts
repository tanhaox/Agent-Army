/**
 * 项目与快照相关 API 调用封装。
 */

import apiClient from './index'

/** 项目响应体。 */
export interface ProjectResponse {
  id: string
  name: string
  description: string | null
  current_script_id: string | null
  status: string
  created_at: string
  updated_at: string
}

/** 创建项目请求体。 */
export interface ProjectCreateRequest {
  name: string
  description?: string
}

/** 更新项目请求体。 */
export interface ProjectUpdateRequest {
  name?: string
  description?: string
  current_script_id?: string
  status?: string
}

/** 项目仪表盘响应体。 */
export interface ProjectDashboardResponse {
  project: ProjectResponse
  script_count: number
  storyboard_count: number
  character_count: number
  video_task_count: number
  recent_scripts: Record<string, unknown>[]
  recent_video_tasks: Record<string, unknown>[]
}

/** AI 生成分镜响应体。 */
export interface GenerateStoryboardsResponse {
  generated_count: number
  storyboards: Record<string, unknown>[]
}

/** 项目角色关联响应体。 */
export interface ProjectCharacterResponse {
  character_id: string
  character_name: string
  role_name: string | null
  traits: Record<string, unknown>
  reference_images: string[]
  created_at: string
}

/** 添加角色到项目请求体。 */
export interface ProjectCharacterRequest {
  character_id: string
  role_name?: string
}

/** 快照简要信息。 */
export interface SnapshotBriefResponse {
  id: string
  project_id: string
  snapshot_name: string
  created_at: string
  snapshot_meta: Record<string, unknown> | null
}

/** 快照详情。 */
export interface SnapshotDetailResponse {
  id: string
  project_id: string
  snapshot_name: string
  script_snapshot: Record<string, unknown> | null
  storyboards_snapshot: Record<string, unknown>[] | null
  snapshot_meta: Record<string, unknown> | null
  created_at: string
}

/** 快照对比结果。 */
export interface CompareResponse {
  snapshot_1_name: string
  snapshot_2_name: string
  script_diff: Record<string, unknown>
  storyboards_diff: Record<string, unknown>
}

export const projectsApi = {
  /** 创建项目。 */
  create: (data: ProjectCreateRequest) =>
    apiClient.post<ProjectResponse>('/projects', data),

  /** 获取项目列表。 */
  list: () =>
    apiClient.get<ProjectResponse[]>('/projects'),

  /** 获取项目详情。 */
  getById: (id: string) =>
    apiClient.get<ProjectResponse>(`/projects/${id}`),

  /** 更新项目。 */
  update: (id: string, data: ProjectUpdateRequest) =>
    apiClient.put<ProjectResponse>(`/projects/${id}`, data),

  /** 删除项目。 */
  delete: (id: string) =>
    apiClient.delete(`/projects/${id}`),

  /** 创建快照。 */
  createSnapshot: (projectId: string, data?: { snapshot_name?: string; remark?: string }) =>
    apiClient.post<SnapshotDetailResponse>(`/projects/${projectId}/snapshots`, data || {}),

  /** 获取快照列表。 */
  listSnapshots: (projectId: string) =>
    apiClient.get<SnapshotBriefResponse[]>(`/projects/${projectId}/snapshots`),

  /** 获取快照详情。 */
  getSnapshot: (projectId: string, snapshotId: string) =>
    apiClient.get<SnapshotDetailResponse>(`/projects/${projectId}/snapshots/${snapshotId}`),

  /** 从快照恢复。 */
  restoreSnapshot: (projectId: string, snapshotId: string) =>
    apiClient.post<ProjectResponse>(`/projects/${projectId}/snapshots/${snapshotId}/restore`),

  /** 对比两个快照。 */
  compareSnapshots: (projectId: string, snapshotId1: string, snapshotId2: string) =>
    apiClient.post<CompareResponse>(`/projects/${projectId}/snapshots/compare`, {
      snapshot_id_1: snapshotId1,
      snapshot_id_2: snapshotId2,
    }),

  // ========== 仪表盘 ==========

  /** 获取项目仪表盘。 */
  getDashboard: (id: string) =>
    apiClient.get<ProjectDashboardResponse>(`/projects/${id}/dashboard`),

  // ========== 项目角色管理 ==========

  /** 获取项目角色列表。 */
  listProjectCharacters: (projectId: string) =>
    apiClient.get<ProjectCharacterResponse[]>(`/projects/${projectId}/characters`),

  /** 添加角色到项目。 */
  addProjectCharacter: (projectId: string, data: ProjectCharacterRequest) =>
    apiClient.post<ProjectCharacterResponse>(`/projects/${projectId}/characters`, data),

  /** 从项目移除角色。 */
  removeProjectCharacter: (projectId: string, characterId: string) =>
    apiClient.delete(`/projects/${projectId}/characters/${characterId}`),

  // ========== AI 生成分镜 ==========

  /** AI 自动生成分镜。 */
  generateStoryboards: (projectId: string, regenerate: boolean = false) =>
    apiClient.post<GenerateStoryboardsResponse>(`/projects/${projectId}/generate-storyboards`, {
      regenerate,
    }),

  /** 从剧本自动生成角色。 */
  generateCharacters: (projectId: string, visualSettings?: Record<string, string>) =>
    apiClient.post(`/projects/${projectId}/generate-characters`, {
      visual_settings: visualSettings || null,
    }),

  /** 生成角色合照 prompt。 */
  generateGroupPrompt: (projectId: string) =>
    apiClient.post<{ group_prompt: string }>(`/projects/${projectId}/generate-group-prompt`),

  /** 节奏分析驱动的自动分镜优化。 */
  optimizeByRhythm: (projectId: string) =>
    apiClient.post<{ changes: Array<{ type: string; episode_no: number; shot_no: number; detail: string }>; total_added: number; total_modified: number }>(`/projects/${projectId}/optimize-storyboards-by-rhythm`),

  /** 分镜审核（爆款标准）。 */
  reviewStoryboards: (projectId: string) =>
    apiClient.get<{
      overall_score: number
      episodes: Array<{
        episode: number
        shot_count: number
        total_duration: number
        score: number
        dimensions: Record<string, number>
        issues: string[]
        suggestions: string[]
      }>
      global_suggestions: string[]
    }>(`/projects/${projectId}/review-storyboards`),

  /** 审核驱动的自动优化。 */
  optimizeByReview: (projectId: string) =>
    apiClient.post<{ changes: Array<{ type: string; episode_no: number; shot_no: number; detail: string }>; total_added: number; total_modified: number }>(`/projects/${projectId}/optimize-storyboards-by-review`),

  /** 自动添加高潮镜头。 */
  addClimaxShots: (projectId: string) =>
    apiClient.post<{ changes: Array<{ type: string; episode_no: number; shot_no: number; detail: string }>; total_added: number; total_modified: number }>(`/projects/${projectId}/add-climax-shots`),

  /** 爆款分镜重构预览（不写入数据库）。 */
  reconstructStoryboardsPreview: (projectId: string) =>
    apiClient.post<{
      preview: boolean
      changes: Array<{
        type: string
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
        note: string
      }>
      total_episodes: number
      total_shots: number
      old_shot_count: number
      principles_applied: Array<{ id: string; name: string; weight: number; description: string }>
    }>(`/projects/${projectId}/reconstruct-storyboards?apply=false`),

  /** 爆款分镜重构应用（写入数据库，自动快照）。 */
  reconstructStoryboardsApply: (projectId: string) =>
    apiClient.post<{
      preview: boolean
      snapshot_id: string | null
      changes: Array<{ type: string; episode_no: number; shot_no: number; detail: string; note: string }>
      total_episodes: number
      total_shots: number
      principles_applied: Array<{ id: string; name: string; weight: number; description: string }>
    }>(`/projects/${projectId}/reconstruct-storyboards?apply=true`),
}

/** 视觉预设（内置，无 DB）。 */
export interface VisualPreset {
  id: string
  name: string
  description: string
  settings: Record<string, string>
}

export const visualPresetsApi = {
  /** 获取预设列表。 */
  list: () =>
    apiClient.get<VisualPreset[]>('/visual-presets'),

  /** 获取单个预设。 */
  getById: (id: string) =>
    apiClient.get<VisualPreset>(`/visual-presets/${id}`),
}

/** 视觉模板（DB 存储，含系统预设 + 用户自定义）。 */
export interface VisualTemplate {
  id: string
  name: string
  description: string | null
  settings: Record<string, string>
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface TemplateCreateRequest {
  name: string
  description?: string
  settings: Record<string, string>
}

export const visualTemplatesApi = {
  /** 获取模板列表（系统 + 用户）。 */
  list: () =>
    apiClient.get<VisualTemplate[]>('/visual-templates'),

  /** 创建用户模板。 */
  create: (data: TemplateCreateRequest) =>
    apiClient.post<VisualTemplate>('/visual-templates', data),

  /** 更新模板（系统模板不允许）。 */
  update: (id: string, data: Partial<TemplateCreateRequest>) =>
    apiClient.put<VisualTemplate>(`/visual-templates/${id}`, data),

  /** 删除模板（系统模板不允许）。 */
  delete: (id: string) =>
    apiClient.delete(`/visual-templates/${id}`),
}
