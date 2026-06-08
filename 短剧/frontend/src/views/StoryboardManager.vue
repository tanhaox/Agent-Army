<template>
  <div class="storyboard-manager">
    <!-- 顶部操作栏 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 16px;">
      <n-h2 style="margin: 0;">分镜设计</n-h2>
      <n-button type="primary" @click="openCreateModal">新增分镜</n-button>
    </n-space>

    <n-spin :show="loading">
      <n-grid :cols="24" :x-gap="16">
        <!-- 左栏：剧本列表 -->
        <n-gi :span="6">
          <n-card title="剧本列表" size="small" hoverable>
            <n-empty v-if="scripts.length === 0" description="暂无剧本" size="small" />
            <n-menu
              v-else
              :options="scriptMenuOptions"
              :value="selectedScriptId"
              @update:value="handleSelectScript"
            />
          </n-card>
        </n-gi>

        <!-- 右栏：分镜列表 -->
        <n-gi :span="18">
          <n-card :title="currentTitle" size="small">
            <template #header-extra>
              <n-text v-if="storyboards.length > 0" depth="3" style="font-size: 13px;">
                共 {{ storyboards.length }} 个分镜
              </n-text>
            </template>
            <n-empty v-if="storyboards.length === 0 && !loading" description="暂无分镜，点击右上角新增" />
            <n-data-table
              v-else
              :columns="columns"
              :data="storyboards"
              :bordered="false"
              size="small"
              :row-key="(row: StoryboardResponse) => row.id"
            />
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- 创建/编辑分镜对话框 -->
    <n-modal
      v-model:show="showModal"
      preset="dialog"
      :title="editingId ? '编辑分镜' : '新增分镜'"
      positive-text="保存"
      negative-text="取消"
      :loading="saving"
      @positive-click="handleSave"
    >
      <n-form ref="formRef" :model="form" label-placement="top">
        <n-grid :cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="集数" required>
              <n-input-number v-model:value="form.episode_no" :min="1" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="镜头序号" required>
              <n-input-number v-model:value="form.shot_no" :min="1" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="景别" required>
              <n-select v-model:value="form.shot_type" :options="shotTypeOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="运镜" required>
              <n-select v-model:value="form.camera_move" :options="cameraMoveOptions" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="动作描述" required>
          <n-input v-model:value="form.action" type="textarea" :rows="2" placeholder="描述角色的动作和表演" />
        </n-form-item>
        <n-form-item label="对话内容">
          <n-input v-model:value="form.dialogue" type="textarea" :rows="2" placeholder="可选，角色的对白" />
        </n-form-item>
        <n-grid :cols="3" :x-gap="12">
          <n-gi>
            <n-form-item label="情绪" required>
              <n-select v-model:value="form.emotion" :options="emotionOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="特效">
              <n-select v-model:value="form.vfx" :options="vfxOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="光线" required>
              <n-input v-model:value="form.lighting" placeholder="例如：逆光、柔和" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="环境/背景" required>
          <n-input v-model:value="form.environment" type="textarea" :rows="2" placeholder="描述场景的环境和背景" />
        </n-form-item>
        <n-form-item label="视频提示词">
          <n-space vertical style="width: 100%;">
            <n-input
              v-model:value="form.prompt_text"
              type="textarea"
              :rows="3"
              placeholder="点击生成或手动输入英文提示词"
            />
            <n-button size="small" :loading="generating" @click="handleGeneratePrompt">
              生成提示词
            </n-button>
          </n-space>
        </n-form-item>
        <n-form-item v-if="form.negative_prompt" label="负面提示词">
          <n-input
            v-model:value="form.negative_prompt"
            type="textarea"
            :rows="2"
            placeholder="避免出现的内容"
          />
        </n-form-item>
        <n-grid :cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="时长(秒)">
              <n-input-number v-model:value="form.duration_seconds" :min="1" :max="30" style="width: 100%;" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="关键镜头">
              <n-checkbox v-model:checked="form.is_key_moment">高潮/反转镜头</n-checkbox>
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
    </n-modal>

    <!-- 视频生成对话框 -->
    <n-modal
      v-model:show="showVideoModal"
      preset="dialog"
      title="生成视频"
      positive-text="提交生成"
      negative-text="取消"
      :loading="submittingVideo"
      @positive-click="handleSubmitVideo"
    >
      <n-form :model="videoForm" label-placement="top">
        <n-form-item label="视频提示词">
          <n-input
            v-model:value="videoForm.prompt"
            type="textarea"
            :rows="3"
            placeholder="英文视频提示词"
          />
        </n-form-item>
        <n-grid :cols="3" :x-gap="12">
          <n-gi>
            <n-form-item label="生成模式">
              <n-select v-model:value="videoForm.mode" :options="modeOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="时长">
              <n-select v-model:value="videoForm.duration" :options="durationOptions" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="画面比例">
              <n-select v-model:value="videoForm.aspect_ratio" :options="ratioOptions" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
    </n-modal>

    <!-- 视频状态查看对话框 -->
    <n-modal
      v-model:show="showVideoStatusModal"
      preset="dialog"
      title="视频生成状态"
      :show-icon="false"
    >
      <n-spin :show="loadingVideoStatus">
        <template v-if="currentVideoTask">
          <n-descriptions bordered :column="1" label-placement="left" size="small">
            <n-descriptions-item label="任务 ID">{{ currentVideoTask.id.slice(0, 8) }}</n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="videoStatusTagType" size="small">{{ videoStatusText }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="提示词">{{ truncate(currentVideoTask.prompt, 80) }}</n-descriptions-item>
            <n-descriptions-item v-if="currentVideoTask.video_url" label="视频">
              <n-button text type="primary" size="small" @click="openVideoUrl(currentVideoTask.video_url!)">
                查看视频
              </n-button>
            </n-descriptions-item>
            <n-descriptions-item v-if="currentVideoTask.error_message" label="错误信息">
              <n-text type="error">{{ currentVideoTask.error_message }}</n-text>
            </n-descriptions-item>
          </n-descriptions>
        </template>
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  NButton, NCard, NCheckbox, NDataTable, NDescriptions, NDescriptionsItem, NEmpty, NForm, NFormItem,
  NGi, NGrid, NH2, NInput, NInputNumber, NMenu, NModal, NSelect, NSpace, NSpin,
  NTag, NText, useMessage,
  type DataTableColumns, type MenuOption, type SelectOption,
} from 'naive-ui'
import {
  storyboardsApi,
  scriptsApi,
  type StoryboardResponse,
  type StoryboardCreate,
  type ScriptResponse,
} from '../api/storyboards'
import {
  videoTasksApi,
  type VideoTaskResponse,
  type VideoGenerateRequest,
} from '../api/videoTasks'

const message = useMessage()

// --- 状态 ---
const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const submittingVideo = ref(false)
const loadingVideoStatus = ref(false)
const scripts = ref<ScriptResponse[]>([])
const storyboards = ref<StoryboardResponse[]>([])
const selectedScriptId = ref<string | null>(null)
const showModal = ref(false)
const showVideoModal = ref(false)
const showVideoStatusModal = ref(false)
const editingId = ref<string | null>(null)
const videoStoryboardId = ref<string | null>(null)
const currentVideoTask = ref<VideoTaskResponse | null>(null)
let statusPollTimer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  episode_no: 1,
  shot_no: 1,
  shot_type: '中景',
  camera_move: '固定',
  action: '',
  dialogue: '',
  emotion: '',
  vfx: '无',
  environment: '',
  lighting: '',
  prompt_text: '',
  negative_prompt: '',
  duration_seconds: 5,
  is_key_moment: false,
})

const videoForm = reactive({
  prompt: '',
  mode: 'std',
  duration: '5',
  aspect_ratio: '16:9',
})

// --- 选项配置 ---
const shotTypeOptions: SelectOption[] = [
  { label: '远景', value: '远景' },
  { label: '全景', value: '全景' },
  { label: '中景', value: '中景' },
  { label: '近景', value: '近景' },
  { label: '特写', value: '特写' },
]

const cameraMoveOptions: SelectOption[] = [
  { label: '固定', value: '固定' },
  { label: '推', value: '推' },
  { label: '拉', value: '拉' },
  { label: '摇', value: '摇' },
  { label: '移', value: '移' },
  { label: '跟', value: '跟' },
]

const emotionOptions: SelectOption[] = [
  { label: '平静', value: '平静' },
  { label: '紧张', value: '紧张' },
  { label: '愤怒', value: '愤怒' },
  { label: '悲伤', value: '悲伤' },
  { label: '喜悦', value: '喜悦' },
  { label: '甜蜜', value: '甜蜜' },
  { label: '恐惧', value: '恐惧' },
  { label: '期待', value: '期待' },
  { label: '感动', value: '感动' },
  { label: '困惑', value: '困惑' },
]

const vfxOptions: SelectOption[] = [
  { label: '无', value: '无' },
  { label: '光效', value: '光效' },
  { label: '粒子特效', value: '粒子特效' },
  { label: '镜头特效', value: '镜头特效' },
  { label: '色彩滤镜', value: '色彩滤镜' },
  { label: '动态模糊', value: '动态模糊' },
  { label: '转场特效', value: '转场特效' },
]

const modeOptions: SelectOption[] = [
  { label: '标准模式', value: 'std' },
  { label: '专业模式', value: 'pro' },
]

const durationOptions: SelectOption[] = [
  { label: '5 秒', value: '5' },
  { label: '10 秒', value: '10' },
]

const ratioOptions: SelectOption[] = [
  { label: '16:9（横屏）', value: '16:9' },
  { label: '9:16（竖屏）', value: '9:16' },
  { label: '1:1（方形）', value: '1:1' },
]

// --- 计算属性 ---
const scriptMenuOptions = computed<MenuOption[]>(() =>
  scripts.value.map((s) => ({
    label: s.project_name || s.theme?.slice(0, 20) || s.id.slice(0, 8),
    key: s.id,
  }))
)

const currentTitle = computed(() => {
  if (!selectedScriptId.value) return '全部分镜'
  const script = scripts.value.find((s) => s.id === selectedScriptId.value)
  return script ? `${script.project_name} - 分镜列表` : '分镜列表'
})

const videoStatusText = computed(() => {
  if (!currentVideoTask.value) return ''
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '生成中',
    success: '已完成',
    failed: '失败',
  }
  return map[currentVideoTask.value.status] || currentVideoTask.value.status
})

const videoStatusTagType = computed(() => {
  if (!currentVideoTask.value) return 'default' as const
  const map: Record<string, 'default' | 'info' | 'success' | 'error'> = {
    pending: 'default',
    processing: 'info',
    success: 'success',
    failed: 'error',
  }
  return map[currentVideoTask.value.status] || 'default'
})

// --- 表格列 ---
const regeneratingPromptId = ref<string | null>(null)
const enhancingPromptId = ref<string | null>(null)
const expandedPromptId = ref<string | null>(null)
const editingDurationId = ref<string | null>(null)
const columns: DataTableColumns<StoryboardResponse> = [
  { title: '集', key: 'episode_no', width: 35, align: 'center' },
  { title: '镜', key: 'shot_no', width: 35, align: 'center' },
  { title: '景别', key: 'shot_type', width: 45 },
  { title: '运镜', key: 'camera_move', width: 45 },
  {
    title: '时长(s)', key: 'duration_seconds', width: 60, align: 'center',
    render: (row) => h(NSpace, { size: 2, align: 'center', justify: 'center' }, {
      default: () => [
        h('span', {
          style: `font-size: 13px; font-weight: bold; cursor: pointer; color: ${row.is_key_moment ? '#d03050' : '#333'};`,
          onClick: () => { editingDurationId.value = row.id },
        }, `${row.duration_seconds || 5}`),
        editingDurationId.value === row.id
          ? h('input', {
              type: 'number',
              min: 1, max: 30,
              value: row.duration_seconds,
              style: 'width: 40px; font-size: 12px; text-align: center; border: 1px solid #4098fc; border-radius: 3px; outline: none;',
              autofocus: true,
              onBlur: (e: FocusEvent) => {
                const v = parseInt((e.target as HTMLInputElement).value)
                if (v && v >= 1 && v <= 30) handleUpdateDuration(row, v)
                editingDurationId.value = null
              },
              onKeydown: (e: KeyboardEvent) => { if (e.key === 'Enter') (e.target as HTMLElement).blur() },
            })
          : null,
      ],
    }),
  },
  {
    title: '动作',
    key: 'action',
    ellipsis: { tooltip: true },
    render: (row) => h('span', truncate(row.action, 20)),
  },
  {
    title: '情绪',
    key: 'emotion',
    width: 55,
    render: (row) => h(NTag, {
      size: 'tiny', bordered: false,
      type: row.is_key_moment ? 'error' : 'default',
    }, { default: () => row.emotion }),
  },
  {
    title: '特效',
    key: 'vfx',
    width: 50,
    render: (row) => row.vfx && row.vfx !== '无'
      ? h(NTag, { size: 'tiny', type: 'warning', bordered: false }, { default: () => row.vfx })
      : h(NText, { depth: 3 }, { default: () => '-' }),
  },
  {
    title: '提示词',
    key: 'prompt_text',
    width: 220,
    render: (row) => {
      if (!row.prompt_text) return h(NText, { depth: 3 }, { default: () => '未生成' })
      const expanded = expandedPromptId.value === row.id
      const displayText = expanded ? row.prompt_text : (row.prompt_text.length > 50 ? row.prompt_text.slice(0, 50) + '...' : row.prompt_text)
      return h(NSpace, { size: 4, align: 'start', vertical: true }, {
        default: () => [
          h(NSpace, { size: 4, align: 'center' }, {
            default: () => [
              h('span', {
                style: 'font-size: 12px; cursor: pointer; color: #4098fc;',
                onClick: () => { expandedPromptId.value = expanded ? null : row.id },
              }, expanded ? '收起' : '展开'),
              h(NButton, {
                size: 'tiny', quaternary: true,
                onClick: () => { navigator.clipboard.writeText(row.prompt_text || ''); message.success('已复制') },
              }, { default: () => '📋' }),
              row.negative_prompt ? h('span', {
                style: 'font-size: 11px; color: #d03050; cursor: help;',
                title: row.negative_prompt,
              }, '⛔负面') : null,
            ],
          }),
          h('div', { style: 'font-size: 12px; line-height: 1.5; word-break: break-all; white-space: pre-wrap;' }, displayText),
        ],
      })
    },
  },
  {
    title: '关键', key: 'is_key_moment', width: 35, align: 'center',
    render: (row) => h(NText, { type: row.is_key_moment ? 'error' : 'default' }, { default: () => row.is_key_moment ? '★' : '' }),
  },
  {
    title: '定稿',
    key: 'approved',
    width: 35,
    align: 'center',
    render: (row) => h(NText, { type: row.approved ? 'success' : 'default' }, {
      default: () => row.approved ? '✓' : '',
    }),
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render: (row) => h(NSpace, { size: 4 }, {
      default: () => [
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => openEditModal(row) }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', quaternary: true, type: 'info', loading: regeneratingPromptId.value === row.id, onClick: () => handleRegeneratePrompt(row) }, { default: () => '提示词' }),
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          type: 'warning',
          loading: enhancingPromptId.value === row.id,
          onClick: () => handleEnhancePrompt(row),
        }, { default: () => '增强' }),
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          type: 'primary',
          disabled: !row.prompt_text,
          onClick: () => openVideoGenModal(row),
        }, { default: () => '生视频' }),
        h(NButton, { size: 'tiny', quaternary: true, type: 'info', onClick: () => handleViewVideoStatus(row) }, { default: () => '视频状态' }),
        h(NButton, { size: 'tiny', quaternary: true, type: 'error', onClick: () => handleDelete(row) }, { default: () => '删除' }),
      ],
    }),
  },
]

// --- 数据加载 ---
async function fetchScripts(): Promise<void> {
  try {
    const resp = await scriptsApi.list()
    scripts.value = resp.data
  } catch {
    message.error('加载剧本列表失败')
  }
}

async function fetchStoryboards(): Promise<void> {
  loading.value = true
  try {
    const resp = await storyboardsApi.list(selectedScriptId.value || undefined)
    storyboards.value = resp.data
  } catch {
    message.error('加载分镜列表失败')
  } finally {
    loading.value = false
  }
}

// --- 交互处理 ---
function handleSelectScript(key: string): void {
  selectedScriptId.value = key === '__all__' ? null : key
  fetchStoryboards()
}

function resetForm(): void {
  form.episode_no = 1
  form.shot_no = storyboards.value.length + 1
  form.shot_type = '中景'
  form.camera_move = '固定'
  form.action = ''
  form.dialogue = ''
  form.emotion = ''
  form.vfx = '无'
  form.environment = ''
  form.lighting = ''
  form.prompt_text = ''
  form.negative_prompt = ''
  form.duration_seconds = 5
  form.is_key_moment = false
  editingId.value = null
}

function openCreateModal(): void {
  resetForm()
  showModal.value = true
}

function openEditModal(row: StoryboardResponse): void {
  editingId.value = row.id
  form.episode_no = row.episode_no
  form.shot_no = row.shot_no
  form.shot_type = row.shot_type
  form.camera_move = row.camera_move
  form.action = row.action
  form.dialogue = row.dialogue || ''
  form.emotion = row.emotion
  form.vfx = row.vfx || '无'
  form.environment = row.environment
  form.lighting = row.lighting
  form.prompt_text = row.prompt_text || ''
  form.negative_prompt = row.negative_prompt || ''
  form.duration_seconds = row.duration_seconds || 5
  form.is_key_moment = row.is_key_moment || false
  showModal.value = true
}

async function handleSave(): Promise<boolean> {
  if (!form.action || !form.emotion || !form.environment || !form.lighting) {
    message.warning('请填写必填字段')
    return false
  }
  saving.value = true
  try {
    const payload: StoryboardCreate = {
      ...form,
      script_id: selectedScriptId.value,
      dialogue: form.dialogue || null,
      prompt_text: form.prompt_text || null,
    }
    if (editingId.value) {
      await storyboardsApi.update(editingId.value, payload)
      message.success('分镜已更新')
    } else {
      await storyboardsApi.create(payload)
      message.success('分镜已创建')
    }
    await fetchStoryboards()
    return true
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存失败'
    message.error(detail)
    return false
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: StoryboardResponse): Promise<void> {
  try {
    await storyboardsApi.delete(row.id)
    message.success(`第${row.episode_no}集 第${row.shot_no}镜 已删除`)
    await fetchStoryboards()
  } catch {
    message.error('删除失败')
  }
}

async function handleRegeneratePrompt(row: StoryboardResponse): Promise<void> {
  regeneratingPromptId.value = row.id
  try {
    const resp = await storyboardsApi.regeneratePrompt(row.id)
    const idx = storyboards.value.findIndex(s => s.id === row.id)
    if (idx >= 0) storyboards.value[idx] = resp.data
    message.success('提示词已重新生成')
  } catch {
    message.error('生成提示词失败')
  } finally {
    regeneratingPromptId.value = null
  }
}

async function handleEnhancePrompt(row: StoryboardResponse): Promise<void> {
  enhancingPromptId.value = row.id
  try {
    const resp = await storyboardsApi.enhancePrompt(row.id)
    message.success(`提示词增强成功（标准${resp.data.standard.length}字，增强${resp.data.enhanced.length}字）`)
    await fetchStoryboards()
  } catch {
    message.error('增强提示词失败，请检查 DeepSeek 配置')
  } finally {
    enhancingPromptId.value = null
  }
}

async function handleUpdateDuration(row: StoryboardResponse, val: number): Promise<void> {
  try {
    await storyboardsApi.update(row.id, { duration_seconds: val })
    row.duration_seconds = val
  } catch {
    message.error('更新时长失败')
  }
}

async function handleGeneratePrompt(): Promise<void> {
  if (!form.action || !form.emotion || !form.environment || !form.lighting) {
    message.warning('请先填写动作、情绪、环境和光线')
    return
  }
  generating.value = true
  try {
    const resp = await storyboardsApi.generatePrompt({
      shot_type: form.shot_type,
      camera_move: form.camera_move,
      action: form.action,
      emotion: form.emotion,
      environment: form.environment,
      lighting: form.lighting,
      vfx: form.vfx,
    })
    form.prompt_text = resp.data.prompt_text
    message.success('提示词已生成')
  } catch {
    message.error('生成提示词失败')
  } finally {
    generating.value = false
  }
}

// --- 视频生成 ---
function openVideoGenModal(row: StoryboardResponse): void {
  videoStoryboardId.value = row.id
  videoForm.prompt = row.prompt_text || ''
  videoForm.mode = 'std'
  videoForm.duration = '5'
  videoForm.aspect_ratio = '16:9'
  showVideoModal.value = true
}

async function handleSubmitVideo(): Promise<boolean> {
  if (!videoForm.prompt || !videoStoryboardId.value) {
    message.warning('请填写视频提示词')
    return false
  }
  submittingVideo.value = true
  try {
    const payload: VideoGenerateRequest = {
      storyboard_id: videoStoryboardId.value,
      prompt: videoForm.prompt,
      mode: videoForm.mode,
      duration: videoForm.duration,
      aspect_ratio: videoForm.aspect_ratio,
    }
    const resp = await videoTasksApi.create(payload)
    currentVideoTask.value = resp.data
    message.success('视频生成任务已提交')
    showVideoModal.value = false
    showVideoStatusModal.value = true
    startStatusPoll(resp.data.id)
    return true
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '提交视频生成任务失败'
    message.error(detail)
    return false
  } finally {
    submittingVideo.value = false
  }
}

async function handleViewVideoStatus(row: StoryboardResponse): Promise<void> {
  loadingVideoStatus.value = true
  showVideoStatusModal.value = true
  try {
    const resp = await videoTasksApi.list(row.id)
    if (resp.data.length > 0) {
      currentVideoTask.value = resp.data[0]
      if (currentVideoTask.value.status === 'processing' || currentVideoTask.value.status === 'pending') {
        startStatusPoll(currentVideoTask.value.id)
      }
    } else {
      currentVideoTask.value = null
      message.info('该分镜暂无视频生成记录')
    }
  } catch {
    message.error('查询视频状态失败')
  } finally {
    loadingVideoStatus.value = false
  }
}

function startStatusPoll(taskId: string): void {
  stopStatusPoll()
  statusPollTimer = setInterval(async () => {
    try {
      const resp = await videoTasksApi.getById(taskId)
      currentVideoTask.value = resp.data
      if (resp.data.status === 'success' || resp.data.status === 'failed') {
        stopStatusPoll()
        if (resp.data.status === 'success') {
          message.success('视频生成完成！')
        } else {
          message.error('视频生成失败')
        }
      }
    } catch {
      stopStatusPoll()
    }
  }, 5000)
}

function stopStatusPoll(): void {
  if (statusPollTimer) {
    clearInterval(statusPollTimer)
    statusPollTimer = null
  }
}

function openVideoUrl(url: string): void {
  window.open(url, '_blank')
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text
}

onMounted(async () => {
  await fetchScripts()
  await fetchStoryboards()
})

onUnmounted(() => {
  stopStatusPoll()
})
</script>

<style scoped>
.storyboard-manager {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
