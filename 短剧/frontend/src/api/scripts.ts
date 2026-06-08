/**
 * 剧本相关 API 调用封装。
 */

import apiClient from './index'

/** 从概要生成剧本请求体。 */
export interface GenerateFromOutlineRequest {
  outline_text: string
  style: string
  project_id: string
  source_narrative_tree_id?: string
  source_outline_id?: string
}

/** 剧本响应体。 */
export interface ScriptResponse {
  id: string
  project_name: string
  theme: string
  content: ScriptContent
  created_at: string
  updated_at: string
}

/** 剧本结构化内容。 */
export interface ScriptContent {
  title: string
  episodes: Episode[]
  total_episodes: number
  metadata: {
    theme: string
    episodes_hint: number | null
    actual_episodes: number
  }
}

/** 单集数据。 */
export interface Episode {
  episode: number
  hook: string
  scenes: Scene[]
  cliffhanger: string
}

/** 单场景数据。 */
export interface Scene {
  shot_type: string
  action: string
  dialogue: string
  emotion: string
}

export const scriptsApi = {
  /** 从剧情概要生成剧本。 */
  generateFromOutline: (data: GenerateFromOutlineRequest) =>
    apiClient.post<ScriptResponse>('/scripts/generate-from-outline', data),

  /** 根据 ID 获取剧本。 */
  getById: (id: string) =>
    apiClient.get<ScriptResponse>(`/scripts/${id}`),

  /** 更新剧本内容。 */
  update: (id: string, content: ScriptContent) =>
    apiClient.put<ScriptResponse>(`/scripts/${id}`, { content }),

  /** 获取剧本列表。 */
  list: () =>
    apiClient.get<ScriptResponse[]>('/scripts/'),
}
