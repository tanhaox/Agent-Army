/**
 * 合成任务相关 API 调用封装。
 */

import apiClient from './index'

/** 合成任务响应体。 */
export interface CompositionResponse {
  id: string
  script_id: string | null
  episode_no: number
  status: 'pending' | 'processing' | 'success' | 'failed'
  output_url: string | null
  error_message: string | null
  progress: string | null
}

/** 合成请求体。 */
export interface CompositionRequest {
  script_id?: string
  project_id?: string
  episode_no: number
  storyboard_ids: string[]
}

export const compositionApi = {
  /** 提交合成任务。 */
  generateEpisode: (data: CompositionRequest) =>
    apiClient.post<CompositionResponse>('/composition/generate-episode', data),

  /** 查询合成任务状态。 */
  getTask: (taskId: string) =>
    apiClient.get<CompositionResponse>(`/composition/task/${taskId}`),

  /** 获取所有合成任务，可选按项目过滤。 */
  list: (projectId?: string) =>
    apiClient.get<CompositionResponse[]>('/composition', {
      params: projectId ? { project_id: projectId } : {},
    }),
}
