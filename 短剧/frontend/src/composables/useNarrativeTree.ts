/**
 * 叙事树 composable — 从 ProjectWorkspace 中提取的叙事树逻辑。
 *
 * 管理叙事树生成、分支选择、概要生成、剧本生成等完整创作流程。
 */

import { ref, type Ref } from 'vue'
import { useMessage } from 'naive-ui'
import { narrativeTreesApi, type NarrativeTreeResponse, type NarrativeTreeNode, type NarrativeOutlineResponse, type OutlineItem } from '../api/narrativeTrees'
import { scriptsApi } from '../api/scripts'

interface HistoryTree {
  tree: NarrativeTreeResponse
  outlines: NarrativeOutlineResponse[]
}

export function useNarrativeTree(projectId: string, opts: {
  currentScript: Ref<any>
  onScriptGenerated?: () => Promise<void>
}) {
  const message = useMessage()

  const narrativeTree = ref<NarrativeTreeResponse | null>(null)
  const generatingTree = ref(false)
  const generatingScriptFromTree = ref(false)
  const treeTheme = ref('')
  const selectedBranchIds = ref<string[]>([])
  const outlines = ref<OutlineItem[]>([])
  const selectedOutline = ref<OutlineItem | null>(null)
  const generatingOutlines = ref(false)
  const outlineStoryline = ref('')
  const expandingNodeId = ref<string | null>(null)

  const scriptSubTab = ref('create')
  const loadingCreativeHistory = ref(false)
  const creativeHistory = ref<HistoryTree[]>([])

  const TAG_COLORS: Record<string, string> = {
    '严重': 'error', '普通': 'default', '脑洞': 'purple',
    '反转': 'warning', '狗血': 'magenta', '甜蜜': 'success', '虐心': 'error',
    '高概念': 'info', '爽文': 'success', '悬疑': 'purple',
  }

  function tagColor(tag: string): string {
    return TAG_COLORS[tag] || 'default'
  }

  // ── 树结构工具函数 ──

  function buildParentMap(node: NarrativeTreeNode | undefined, parent: NarrativeTreeNode | null = null, map: Map<string, string> = new Map()): Map<string, string> {
    if (!node) return map
    if (parent) map.set(node.id, parent.id)
    for (const child of node.children || []) buildParentMap(child, node, map)
    return map
  }

  function collectDescendantIds(node: NarrativeTreeNode): string[] {
    const ids: string[] = []
    for (const child of node.children || []) {
      ids.push(child.id)
      ids.push(...collectDescendantIds(child))
    }
    return ids
  }

  function findNodeById(node: NarrativeTreeNode | undefined, id: string): NarrativeTreeNode | null {
    if (!node) return null
    if (node.id === id) return node
    for (const child of node.children || []) {
      const found = findNodeById(child, id)
      if (found) return found
    }
    return null
  }

  function isBranchSelected(nodeId: string): boolean {
    return selectedBranchIds.value.includes(nodeId)
  }

  function toggleBranch(nodeId: string): void {
    const root = narrativeTree.value?.tree_data?.root
    if (!root) return

    const idx = selectedBranchIds.value.indexOf(nodeId)
    if (idx >= 0) {
      const node = findNodeById(root, nodeId)
      const descendants = node ? collectDescendantIds(node) : []
      selectedBranchIds.value = selectedBranchIds.value.filter(
        id => id !== nodeId && !descendants.includes(id),
      )
    } else {
      const parentMap = buildParentMap(root)
      const toAdd: string[] = [nodeId]
      let current = nodeId
      while (parentMap.has(current)) {
        const parentId = parentMap.get(current)!
        if (!selectedBranchIds.value.includes(parentId)) toAdd.push(parentId)
        current = parentId
      }
      selectedBranchIds.value.push(...toAdd)
    }
  }

  function flattenNodes(node: NarrativeTreeNode | undefined, depth: number = 0): { node: NarrativeTreeNode; depth: number }[] {
    if (!node) return []
    const result: { node: NarrativeTreeNode; depth: number }[] = [{ node, depth }]
    for (const child of node.children || []) {
      result.push(...flattenNodes(child, depth + 1))
    }
    return result
  }

  // ── API 调用 ──

  async function handleExpandNode(nodeId: string) {
    if (!narrativeTree.value || expandingNodeId.value) return
    expandingNodeId.value = nodeId
    try {
      const resp = await narrativeTreesApi.expandNode(projectId, narrativeTree.value.id, nodeId, 3)
      narrativeTree.value = resp.data
      message.success('已扩展新分支')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '扩展失败'
      message.error(detail)
    } finally {
      expandingNodeId.value = null
    }
  }

  async function handleGenerateTree() {
    if (!treeTheme.value) { message.warning('请输入创意主题'); return }
    generatingTree.value = true
    try {
      const resp = await narrativeTreesApi.generate(projectId, {
        theme: treeTheme.value,
        max_breadth: 5,
        max_depth: 2,
      })
      narrativeTree.value = resp.data
      selectedBranchIds.value = []
      message.success('叙事树生成成功！请选择分支')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
      message.error(detail)
    } finally {
      generatingTree.value = false
    }
  }

  async function handleGenerateScriptFromTree() {
    if (!selectedOutline.value) {
      message.warning('请先选择一个剧情版本')
      return
    }
    generatingScriptFromTree.value = true
    try {
      const resp = await scriptsApi.generateFromOutline({
        outline_text: selectedOutline.value.text,
        style: selectedOutline.value.style,
        project_id: projectId,
        source_narrative_tree_id: narrativeTree.value?.id || undefined,
        source_outline_id: selectedOutline.value.id || undefined,
      })
      opts.currentScript.value = resp.data
      if (opts.onScriptGenerated) await opts.onScriptGenerated()
      message.success(`「${selectedOutline.value.style}」剧本生成成功！`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
      message.error(detail)
    } finally {
      generatingScriptFromTree.value = false
    }
  }

  async function handleGenerateOutlines() {
    if (!narrativeTree.value) return
    if (selectedBranchIds.value.length < 2) {
      message.warning('请至少选择根节点和一个分支节点')
      return
    }
    generatingOutlines.value = true
    outlines.value = []
    selectedOutline.value = null
    try {
      const resp = await narrativeTreesApi.generateOutlines(
        projectId,
        narrativeTree.value.id,
        { selected_branch_ids: selectedBranchIds.value },
      )
      outlines.value = resp.data.outlines
      outlineStoryline.value = resp.data.storyline
      message.success(`已生成 ${resp.data.outlines.length} 个版本概要`)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
      message.error(detail)
    } finally {
      generatingOutlines.value = false
    }
  }

  function handleSelectOutline(outline: OutlineItem) {
    if (selectedOutline.value?.version === outline.version) return
    selectedOutline.value = outline
    message.success(`已选择「${outline.style}」版本`)
  }

  async function fetchNarrativeTree() {
    try {
      const resp = await narrativeTreesApi.list(projectId)
      const trees = resp.data
      if (trees.length > 0) {
        narrativeTree.value = trees[0]
        selectedBranchIds.value = trees[0].selected_branch_ids || []
      }
    } catch { /* ignore */ }
  }

  async function fetchCreativeHistory() {
    loadingCreativeHistory.value = true
    try {
      const resp = await narrativeTreesApi.list(projectId)
      const trees = resp.data
      const items: HistoryTree[] = []
      for (const tree of trees) {
        let ols: NarrativeOutlineResponse[] = []
        try {
          const oResp = await narrativeTreesApi.listOutlines(projectId, tree.id)
          ols = oResp.data
        } catch { /* ignore */ }
        items.push({ tree, outlines: ols })
      }
      creativeHistory.value = items
    } catch { /* ignore */ } finally {
      loadingCreativeHistory.value = false
    }
  }

  function handleReuseOutline(outline: NarrativeOutlineResponse) {
    selectedOutline.value = {
      id: outline.id,
      style: outline.style,
      text: outline.outline_text,
      version: outline.version_label,
    }
    scriptSubTab.value = 'create'
    message.info(`已加载「${outline.style}」概要，点击生成剧本按钮即可`)
  }

  return {
    // State
    narrativeTree, generatingTree, generatingScriptFromTree,
    treeTheme, selectedBranchIds, outlines, selectedOutline,
    generatingOutlines, outlineStoryline, expandingNodeId,
    scriptSubTab, loadingCreativeHistory, creativeHistory,
    // Helpers
    tagColor, isBranchSelected, toggleBranch, flattenNodes,
    // Actions
    handleExpandNode, handleGenerateTree, handleGenerateScriptFromTree,
    handleGenerateOutlines, handleSelectOutline,
    fetchNarrativeTree, fetchCreativeHistory, handleReuseOutline,
  }
}
