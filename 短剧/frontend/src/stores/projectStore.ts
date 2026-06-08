/**
 * 项目工作区状态管理。
 *
 * 集中管理 ProjectWorkspace 页面的核心数据：
 * 项目信息、仪表盘、剧本、角色、分镜。
 * 各 tab 组件可直接读取 store 数据，避免 prop drilling。
 */

import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import {
  projectsApi,
  type ProjectResponse,
  type ProjectCharacterResponse,
  type SnapshotBriefResponse,
} from '../api/projects'
import {
  scriptsApi,
  type ScriptResponse,
} from '../api/scripts'
import {
  storyboardsApi,
  type StoryboardResponse,
} from '../api/storyboards'
import {
  charactersApi,
  type CharacterResponse,
} from '../api/characters'

export const useProjectStore = defineStore('projectWorkspace', () => {
  // ── 项目基本信息 ──
  const project = ref<ProjectResponse | null>(null)
  const loading = ref(false)

  // ── 仪表盘 ──
  const dashboard = reactive({
    script_count: 0,
    storyboard_count: 0,
    character_count: 0,
    video_task_count: 0,
  })

  // ── 剧本 ──
  const loadingScript = ref(false)
  const currentScript = ref<ScriptResponse | null>(null)

  // ── 角色 ──
  const loadingChars = ref(false)
  const loadingAllChars = ref(false)
  const projectCharacters = ref<ProjectCharacterResponse[]>([])
  const allCharacters = ref<CharacterResponse[]>([])
  const charRoleNames = reactive<Record<string, string>>({})

  // ── 分镜 ──
  const loadingStoryboards = ref(false)
  const generatingStoryboards = ref(false)
  const projectStoryboards = ref<StoryboardResponse[]>([])

  // ── 快照 ──
  const loadingSnapshots = ref(false)
  const snapshots = ref<SnapshotBriefResponse[]>([])

  // ── 数据加载方法 ──

  async function fetchProject(projectId: string) {
    loading.value = true
    try {
      const resp = await projectsApi.getById(projectId)
      project.value = resp.data
    } finally {
      loading.value = false
    }
  }

  async function fetchDashboard(projectId: string) {
    try {
      const resp = await projectsApi.getDashboard(projectId)
      dashboard.script_count = resp.data.script_count
      dashboard.storyboard_count = resp.data.storyboard_count
      dashboard.character_count = resp.data.character_count
      dashboard.video_task_count = resp.data.video_task_count
    } catch { /* ignore */ }
  }

  async function fetchScript(_pid: string) {
    loadingScript.value = true
    try {
      if (project.value?.current_script_id) {
        const resp = await scriptsApi.getById(project.value.current_script_id)
        currentScript.value = resp.data
      }
    } catch { /* ignore */ } finally {
      loadingScript.value = false
    }
  }

  async function fetchProjectCharacters(projectId: string) {
    loadingChars.value = true
    try {
      const resp = await projectsApi.listProjectCharacters(projectId)
      projectCharacters.value = resp.data
    } catch { /* ignore */ } finally {
      loadingChars.value = false
    }
  }

  async function fetchAllCharacters() {
    loadingAllChars.value = true
    try {
      const resp = await charactersApi.list()
      allCharacters.value = resp.data
    } catch { /* ignore */ } finally {
      loadingAllChars.value = false
    }
  }

  async function fetchStoryboards(projectId: string) {
    loadingStoryboards.value = true
    try {
      const resp = await storyboardsApi.list(undefined, projectId)
      projectStoryboards.value = resp.data
    } catch { /* ignore */ } finally {
      loadingStoryboards.value = false
    }
  }

  async function fetchSnapshots(projectId: string) {
    loadingSnapshots.value = true
    try {
      const resp = await projectsApi.listSnapshots(projectId)
      snapshots.value = resp.data
    } catch { /* ignore */ } finally {
      loadingSnapshots.value = false
    }
  }

  /** 加载项目全部核心数据。 */
  async function loadAll(pid: string) {
    await fetchProject(pid)
    await Promise.all([
      fetchDashboard(pid),
      fetchScript(pid),
      fetchProjectCharacters(pid),
      fetchStoryboards(pid),
      fetchSnapshots(pid),
    ])
  }

  /** 更新项目信息后刷新。 */
  function setProject(data: ProjectResponse) {
    project.value = data
  }

  /** 更新剧本后刷新。 */
  function setScript(data: ScriptResponse | null) {
    currentScript.value = data
  }

  return {
    // State
    project, loading,
    dashboard,
    loadingScript, currentScript,
    loadingChars, loadingAllChars, projectCharacters, allCharacters, charRoleNames,
    loadingStoryboards, generatingStoryboards, projectStoryboards,
    loadingSnapshots, snapshots,
    // Actions
    fetchProject, fetchDashboard, fetchScript,
    fetchProjectCharacters, fetchAllCharacters,
    fetchStoryboards, fetchSnapshots,
    loadAll, setProject, setScript,
  }
})
