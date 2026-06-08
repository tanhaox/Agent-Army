/**
 * 角色相关 API 调用封装。
 */

import apiClient from './index'

/** 角色特征类型。 */
export interface CharacterTraits {
  age?: number
  personality?: string
  appearance?: string
  [key: string]: unknown
}

/** 创建角色请求体。 */
export interface CharacterCreate {
  name: string
  traits: CharacterTraits
  voice_id?: string
  platform_bindings?: Record<string, string>
}

/** 更新角色请求体。 */
export interface CharacterUpdate {
  name?: string
  traits?: CharacterTraits
  voice_id?: string
  platform_bindings?: Record<string, string>
}

/** 参考图项。 */
export interface ReferenceImageItem {
  id: string
  url: string
  angle: string
  pose: string
  is_primary: boolean
  created_at: string
}

/** 角色响应体。 */
export interface CharacterResponse {
  id: string
  name: string
  traits: CharacterTraits
  reference_images: ReferenceImageItem[] | string[]
  voice_id: string | null
  base_image_url: string | null
  platform_bindings: Record<string, string>
  created_at: string
  updated_at: string
}

/** 生成候选照请求体。 */
export interface GenerateCandidatesRequest {
  count?: number
  prompt_hint?: string
}

/** 设置基准图请求体。 */
export interface SetBaseImageRequest {
  image_url: string
}

/** 生成多角度请求体。 */
export interface GenerateAnglesRequest {
  angles?: string[]
}

/** 候选照响应体。 */
export interface GenerateCandidatesResponse {
  character_id: string
  candidates: string[]
  count: number
}

/** 多角度响应体。 */
export interface GenerateAnglesResponse {
  character_id: string
  angles: Record<string, string>
  count: number
}

export const charactersApi = {
  /** 创建角色。 */
  create: (data: CharacterCreate) =>
    apiClient.post<CharacterResponse>('/characters', data),

  /** 获取角色列表。 */
  list: () =>
    apiClient.get<CharacterResponse[]>('/characters'),

  /** 获取角色详情。 */
  getById: (id: string) =>
    apiClient.get<CharacterResponse>(`/characters/${id}`),

  /** 更新角色。 */
  update: (id: string, data: CharacterUpdate) =>
    apiClient.put<CharacterResponse>(`/characters/${id}`, data),

  /** 上传参考图。 */
  uploadImage: (id: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post<CharacterResponse>(`/characters/${id}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 删除角色。 */
  delete: (id: string) =>
    apiClient.delete(`/characters/${id}`),

  /** AI 生成角色参考图。 */
  generateImage: (id: string, angle: string = 'front') =>
    apiClient.post<CharacterResponse>(`/characters/${id}/generate-image`, { angle }),

  /** 上传结构化参考图。 */
  uploadReferenceImage: (id: string, file: File, angle: string = 'front', pose: string = 'standing', isPrimary: boolean = false) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('angle', angle)
    formData.append('pose', pose)
    formData.append('is_primary', String(isPrimary))
    return apiClient.post<ReferenceImageItem>(`/characters/${id}/reference-images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /** 更新参考图元数据。 */
  updateReferenceImage: (id: string, imageId: string, data: { angle?: string; pose?: string; is_primary?: boolean }) =>
    apiClient.put<ReferenceImageItem>(`/characters/${id}/reference-images/${imageId}`, data),

  /** 删除参考图。 */
  deleteReferenceImage: (id: string, imageId: string) =>
    apiClient.post<CharacterResponse>(`/characters/${id}/delete-reference-image`, { image_id: imageId }),

  /** 生成多角度提示词。 */
  generateAnglePrompts: (id: string, angles?: string[]) =>
    apiClient.post<Record<string, string>>(`/characters/${id}/generate-angle-prompts`, { angles }),

  /** Seedream: 生成角色候选正面照。 */
  generateCandidates: (id: string, data: GenerateCandidatesRequest = {}) =>
    apiClient.post<GenerateCandidatesResponse>(`/characters/${id}/generate-candidates`, data),

  /** Seedream: 设置角色基准图。 */
  setBaseImage: (id: string, data: SetBaseImageRequest) =>
    apiClient.post<CharacterResponse>(`/characters/${id}/set-base-image`, data),

  /** Seedream: 用 image_prompt 直接生成角色肖像。 */
  generatePortrait: (id: string) =>
    apiClient.post<CharacterResponse>(`/characters/${id}/generate-portrait`),

  /** Seedream: 从基准图生成多角度参考图。 */
  generateAngles: (id: string, data: GenerateAnglesRequest = {}) =>
    apiClient.post<GenerateAnglesResponse>(`/characters/${id}/generate-angles`, data),
}
