/**
 * 叙事树相关 API 调用封装。
 */

import apiClient from './index'

/** 叙事树节点。 */
export interface NarrativeTreeNode {
  id: string
  text: string
  type?: string
  tags?: string[]
  score?: number | null
  pros?: string | null
  cons?: string | null
  children?: NarrativeTreeNode[]
}

/** 叙事树响应体。 */
export interface NarrativeTreeResponse {
  id: string
  project_id: string
  user_theme: string
  tree_data: { root: NarrativeTreeNode }
  selected_branch_ids: string[] | null
  status: 'draft' | 'confirmed' | 'converted'
  created_at: string
  updated_at: string
}

/** 生成叙事树请求体。 */
export interface GenerateNarrativeTreeRequest {
  theme: string
  max_breadth?: number
  max_depth?: number
}

/** 从叙事树生成剧本请求体。 */
export interface GenerateScriptFromTreeRequest {
  selected_branch_ids: string[]
}

/** 从叙事树生成剧本响应体。 */
export interface GenerateScriptFromTreeResponse {
  script: Record<string, unknown>
  storyline: string
}

/** 单个风格的剧情概要。 */
export interface OutlineItem {
  id: string | null
  style: string
  text: string
  version: string
}

/** 叙事概要持久化记录。 */
export interface NarrativeOutlineResponse {
  id: string
  narrative_tree_id: string
  style: string
  outline_text: string
  version_label: string
  storyline: string | null
  created_at: string
}

/** 生成概要请求体。 */
export interface GenerateOutlinesRequest {
  selected_branch_ids: string[]
  styles?: string[]
}

/** 生成概要响应体。 */
export interface GenerateOutlinesResponse {
  outlines: OutlineItem[]
  storyline: string
}

export const narrativeTreesApi = {
  /** 生成叙事树。 */
  generate: (projectId: string, data: GenerateNarrativeTreeRequest) =>
    apiClient.post<NarrativeTreeResponse>(`/projects/${projectId}/narrative-trees`, data),

  /** 获取叙事树列表。 */
  list: (projectId: string) =>
    apiClient.get<NarrativeTreeResponse[]>(`/projects/${projectId}/narrative-trees`),

  /** 获取叙事树详情。 */
  getById: (projectId: string, treeId: string) =>
    apiClient.get<NarrativeTreeResponse>(`/projects/${projectId}/narrative-trees/${treeId}`),

  /** 确认分支选择。 */
  confirmBranches: (projectId: string, treeId: string, selectedBranchIds: string[]) =>
    apiClient.put<NarrativeTreeResponse>(
      `/projects/${projectId}/narrative-trees/${treeId}/confirm`,
      { selected_branch_ids: selectedBranchIds },
    ),

  /** 生成多版本剧情概要。 */
  generateOutlines: (projectId: string, treeId: string, data: GenerateOutlinesRequest) =>
    apiClient.post<GenerateOutlinesResponse>(
      `/projects/${projectId}/narrative-trees/${treeId}/generate-outlines`,
      data,
    ),

  /** 从叙事树生成剧本。 */
  generateScript: (projectId: string, treeId: string, data: GenerateScriptFromTreeRequest) =>
    apiClient.post<GenerateScriptFromTreeResponse>(
      `/projects/${projectId}/narrative-trees/${treeId}/generate-script`,
      data,
    ),

  /** 获取叙事树的所有概要。 */
  listOutlines: (projectId: string, treeId: string) =>
    apiClient.get<NarrativeOutlineResponse[]>(
      `/projects/${projectId}/narrative-trees/${treeId}/outlines`,
    ),

  /** 扩展节点分支。 */
  expandNode: (projectId: string, treeId: string, nodeId: string, count: number = 3) =>
    apiClient.post<NarrativeTreeResponse>(
      `/projects/${projectId}/narrative-trees/${treeId}/expand-node`,
      { node_id: nodeId, count },
    ),
}
