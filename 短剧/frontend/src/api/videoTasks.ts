/**
 * 视频任务相关 API 调用封装。
 */

import apiClient from './index'

/** 视频任务响应体。 */
export interface VideoTaskResponse {
  id: string
  storyboard_id: string
  project_id: string | null
  kling_task_id: string | null
  status: 'pending' | 'processing' | 'success' | 'failed'
  prompt: string
  mode: string
  duration: string
  aspect_ratio: string
  video_url: string | null
  error_message: string | null
  created_at: string
  updated_at: string
}

/** 视频生成请求体。 */
export interface VideoGenerateRequest {
  storyboard_id: string
  prompt: string
  mode?: string
  duration?: string
  aspect_ratio?: string
  project_id?: string
}

export const videoTasksApi = {
  /** 提交视频生成任务。 */
  create: (data: VideoGenerateRequest) =>
    apiClient.post<VideoTaskResponse>('/video-tasks', data),

  /** 获取视频任务列表。 */
  list: (storyboardId?: string, projectId?: string) =>
    apiClient.get<VideoTaskResponse[]>('/video-tasks', {
      params: {
        ...(storyboardId ? { storyboard_id: storyboardId } : {}),
        ...(projectId ? { project_id: projectId } : {}),
      },
    }),

  /** 获取视频任务详情。 */
  getById: (id: string) =>
    apiClient.get<VideoTaskResponse>(`/video-tasks/${id}`),
}
