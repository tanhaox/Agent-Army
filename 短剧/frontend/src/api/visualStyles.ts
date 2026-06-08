/**
 * 项目视觉风格 API — 风格锁定配置。
 */

import apiClient from './index'

export interface VisualStyle {
  project_id: string
  style_reference_image: string | null
  color_palette: string[] | null
  lighting_rule: string | null
  camera_style: string | null
  art_style: string | null
}

export interface VisualStyleUpdate {
  style_reference_image?: string | null
  color_palette?: string[] | null
  lighting_rule?: string | null
  camera_style?: string | null
  art_style?: string | null
}

export async function getVisualStyle(projectId: string): Promise<VisualStyle> {
  const { data } = await apiClient.get(`/projects/${projectId}/visual-style`)
  return data
}

export async function updateVisualStyle(projectId: string, update: VisualStyleUpdate): Promise<VisualStyle> {
  const { data } = await apiClient.put(`/projects/${projectId}/visual-style`, update)
  return data
}

export async function uploadStyleReference(projectId: string, file: File): Promise<VisualStyle> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await apiClient.post(
    `/projects/${projectId}/visual-style/upload-reference`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}
