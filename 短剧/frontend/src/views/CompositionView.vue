<template>
  <div class="composition-view">
    <n-space justify="space-between" align="center" style="margin-bottom: 16px;">
      <n-h2 style="margin: 0;">合成中心</n-h2>
    </n-space>

    <!-- 合成操作区 -->
    <n-card title="合成一集视频" size="small" style="margin-bottom: 16px;">
      <n-form :model="compForm" label-placement="left" label-width="80" inline>
        <n-form-item label="剧本">
          <n-select
            v-model:value="compForm.script_id"
            :options="scriptOptions"
            placeholder="选择剧本"
            clearable
            style="width: 200px;"
            @update:value="handleScriptChange"
          />
        </n-form-item>
        <n-form-item label="集数">
          <n-input-number v-model:value="compForm.episode_no" :min="1" style="width: 100px;" />
        </n-form-item>
        <n-form-item>
          <n-button
            type="primary"
            :loading="submitting"
            :disabled="selectedStoryboardIds.length === 0"
            @click="handleCompose"
          >
            合成选中的 {{ selectedStoryboardIds.length }} 个分镜
          </n-button>
        </n-form-item>
      </n-form>

      <!-- 分镜选择列表 -->
      <n-spin :show="loadingStoryboards">
        <n-empty v-if="availableStoryboards.length === 0" description="请先选择剧本并确保有已生成视频的分镜" size="small" />
        <n-data-table
          v-else
          :columns="selectColumns"
          :data="availableStoryboards"
          :bordered="false"
          size="small"
          :row-key="(row: SelectableStoryboard) => row.id"
          :checked-row-keys="selectedStoryboardIds"
          @update:checked-row-keys="handleCheck"
        />
      </n-spin>
    </n-card>

    <!-- 合成任务历史 -->
    <n-card title="合成任务历史" size="small">
      <n-spin :show="loadingTasks">
        <n-empty v-if="tasks.length === 0" description="暂无合成任务" size="small" />
        <n-data-table
          v-else
          :columns="taskColumns"
          :data="tasks"
          :bordered="false"
          size="small"
          :row-key="(row: CompositionResponse) => row.id"
        />
      </n-spin>
    </n-card>

    <!-- 合成任务详情弹窗 -->
    <n-modal
      v-model:show="showDetailModal"
      preset="dialog"
      title="合成任务详情"
      :show-icon="false"
    >
      <template v-if="currentTask">
        <n-spin :show="pollingStatus">
          <n-descriptions bordered :column="1" label-placement="left" size="small">
            <n-descriptions-item label="任务 ID">{{ currentTask.id.slice(0, 8) }}</n-descriptions-item>
            <n-descriptions-item label="集数">{{ currentTask.episode_no }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="statusTagType" size="small">{{ statusText }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item v-if="currentTask.progress" label="进度">
              {{ currentTask.progress }}
            </n-descriptions-item>
            <n-descriptions-item v-if="currentTask.output_url" label="视频">
              <n-button text type="primary" size="small" @click="previewVideo(currentTask.output_url!)">
                预览视频
              </n-button>
              <n-button text type="info" size="small" style="margin-left: 8px;" @click="downloadVideo(currentTask.output_url!)">
                下载
              </n-button>
            </n-descriptions-item>
            <n-descriptions-item v-if="currentTask.error_message" label="错误信息">
              <n-text type="error">{{ currentTask.error_message }}</n-text>
            </n-descriptions-item>
          </n-descriptions>
        </n-spin>
      </template>
    </n-modal>

    <!-- 视频预览弹窗 -->
    <n-modal
      v-model:show="showPreviewModal"
      preset="dialog"
      title="视频预览"
      style="width: 720px;"
      :show-icon="false"
    >
      <video
        v-if="previewUrl"
        :src="previewUrl"
        controls
        style="width: 100%; max-height: 480px;"
      />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  NButton, NCard, NDataTable, NDescriptions, NDescriptionsItem, NEmpty,
  NForm, NFormItem, NH2, NInputNumber, NModal, NSelect, NSpace, NSpin,
  NTag, NText, useMessage,
  type DataTableColumns,
} from 'naive-ui'
import {
  compositionApi,
  type CompositionResponse,
} from '../api/composition'
import {
  storyboardsApi,
  scriptsApi,
  type StoryboardResponse,
  type ScriptResponse,
} from '../api/storyboards'

const message = useMessage()

// --- 状态 ---
const submitting = ref(false)
const loadingStoryboards = ref(false)
const loadingTasks = ref(false)
const pollingStatus = ref(false)
const scripts = ref<ScriptResponse[]>([])
const storyboards = ref<StoryboardResponse[]>([])
const tasks = ref<CompositionResponse[]>([])
const selectedStoryboardIds = ref<string[]>([])
const showDetailModal = ref(false)
const showPreviewModal = ref(false)
const currentTask = ref<CompositionResponse | null>(null)
const previewUrl = ref<string | null>(null)
let pollTimer: ReturnType<typeof setInterval> | null = null

const compForm = reactive({
  script_id: null as string | null,
  episode_no: 1,
})

interface SelectableStoryboard {
  id: string
  episode_no: number
  shot_no: number
  shot_type: string
  action: string
  dialogue: string | null
  has_video: boolean
}

// --- 计算属性 ---
const scriptOptions = computed(() =>
  scripts.value.map((s) => ({
    label: s.project_name || s.theme?.slice(0, 20) || s.id.slice(0, 8),
    value: s.id,
  }))
)

const availableStoryboards = computed<SelectableStoryboard[]>(() =>
  storyboards.value.map((sb) => ({
    id: sb.id,
    episode_no: sb.episode_no,
    shot_no: sb.shot_no,
    shot_type: sb.shot_type,
    action: sb.action,
    dialogue: sb.dialogue,
    has_video: false, // 后面异步填充
  }))
)

const statusText = computed(() => {
  if (!currentTask.value) return ''
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '合成中',
    success: '已完成',
    failed: '失败',
  }
  return map[currentTask.value.status] || currentTask.value.status
})

const statusTagType = computed(() => {
  if (!currentTask.value) return 'default' as const
  const map: Record<string, 'default' | 'info' | 'success' | 'error'> = {
    pending: 'default',
    processing: 'info',
    success: 'success',
    failed: 'error',
  }
  return map[currentTask.value.status] || 'default'
})

// --- 表格列 ---
const selectColumns: DataTableColumns<SelectableStoryboard> = [
  { type: 'selection' },
  { title: '集', key: 'episode_no', width: 50, align: 'center' },
  { title: '镜', key: 'shot_no', width: 50, align: 'center' },
  { title: '景别', key: 'shot_type', width: 60 },
  { title: '动作', key: 'action', ellipsis: { tooltip: true } },
  { title: '对话', key: 'dialogue', ellipsis: { tooltip: true }, render: (row) => row.dialogue || '-' },
]

const taskColumns: DataTableColumns<CompositionResponse> = [
  { title: '任务 ID', key: 'id', width: 100, render: (row) => row.id.slice(0, 8) },
  { title: '集数', key: 'episode_no', width: 60, align: 'center' },
  {
    title: '状态', key: 'status', width: 80,
    render: (row) => {
      const typeMap: Record<string, 'default' | 'info' | 'success' | 'error'> = {
        pending: 'default', processing: 'info', success: 'success', failed: 'error',
      }
      const textMap: Record<string, string> = {
        pending: '等待中', processing: '合成中', success: '已完成', failed: '失败',
      }
      return h(NTag, { type: typeMap[row.status] || 'default', size: 'small' }, { default: () => textMap[row.status] || row.status })
    },
  },
  { title: '进度', key: 'progress', ellipsis: { tooltip: true }, render: (row) => row.progress || '-' },
  {
    title: '操作', key: 'actions', width: 150,
    render: (row) => h(NSpace, { size: 4 }, {
      default: () => [
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => handleViewTask(row) }, { default: () => '详情' }),
        row.output_url
          ? h(NButton, { size: 'tiny', quaternary: true, type: 'primary', onClick: () => previewVideo(row.output_url!) }, { default: () => '预览' })
          : null,
      ],
    }),
  },
]

// --- 数据加载 ---
async function fetchScripts() {
  try {
    const resp = await scriptsApi.list()
    scripts.value = resp.data
  } catch {
    message.error('加载剧本列表失败')
  }
}

async function fetchTasks() {
  loadingTasks.value = true
  try {
    const resp = await compositionApi.list()
    tasks.value = resp.data
  } catch {
    // 合成任务列表获取失败不影响页面
  } finally {
    loadingTasks.value = false
  }
}

async function handleScriptChange(scriptId: string | null) {
  compForm.script_id = scriptId
  selectedStoryboardIds.value = []
  if (!scriptId) {
    storyboards.value = []
    return
  }
  loadingStoryboards.value = true
  try {
    const resp = await storyboardsApi.list(scriptId)
    storyboards.value = resp.data
  } catch {
    message.error('加载分镜列表失败')
  } finally {
    loadingStoryboards.value = false
  }
}

function handleCheck(keys: Array<string | number>) {
  selectedStoryboardIds.value = keys as string[]
}

// --- 合成操作 ---
async function handleCompose() {
  if (selectedStoryboardIds.value.length === 0) {
    message.warning('请先选择要合成的分镜')
    return
  }
  submitting.value = true
  try {
    const resp = await compositionApi.generateEpisode({
      script_id: compForm.script_id || undefined,
      episode_no: compForm.episode_no,
      storyboard_ids: selectedStoryboardIds.value,
    })
    message.success('合成任务已提交')
    currentTask.value = resp.data
    showDetailModal.value = true
    startPoll(resp.data.id)
    await fetchTasks()
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '提交合成任务失败'
    message.error(detail)
  } finally {
    submitting.value = false
  }
}

async function handleViewTask(task: CompositionResponse) {
  currentTask.value = task
  showDetailModal.value = true
  if (task.status === 'processing' || task.status === 'pending') {
    startPoll(task.id)
  }
}

function startPoll(taskId: string) {
  stopPoll()
  pollingStatus.value = true
  pollTimer = setInterval(async () => {
    try {
      const resp = await compositionApi.getTask(taskId)
      currentTask.value = resp.data
      if (resp.data.status === 'success' || resp.data.status === 'failed') {
        stopPoll()
        await fetchTasks()
        if (resp.data.status === 'success') {
          message.success('合成完成！')
        } else {
          message.error('合成失败')
        }
      }
    } catch {
      stopPoll()
    }
  }, 5000)
}

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  pollingStatus.value = false
}

function previewVideo(url: string) {
  previewUrl.value = url
  showPreviewModal.value = true
}

function downloadVideo(url: string) {
  const a = document.createElement('a')
  a.href = url
  a.download = `episode_video.mp4`
  a.click()
}

onMounted(async () => {
  await Promise.all([fetchScripts(), fetchTasks()])
})

onUnmounted(() => {
  stopPoll()
})
</script>

<style scoped>
.composition-view {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
