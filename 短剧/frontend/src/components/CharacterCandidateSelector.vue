<template>
  <div class="candidate-selector">
    <n-space vertical :size="12">
      <n-space align="center" justify="space-between">
        <n-space align="center">
          <n-text strong>步骤 1：生成候选正面照</n-text>
          <n-tag v-if="candidates.length > 0" type="success" size="small">{{ candidates.length }}张</n-tag>
        </n-space>
        <n-space align="center">
          <n-input-number v-model:value="candidateCount" :min="1" :max="8" size="small" style="width: 80px" />
          <n-text depth="3" style="font-size: 12px">张</n-text>
          <n-button
            type="primary"
            size="small"
            :loading="generating"
            :disabled="generating"
            @click="handleGenerate"
          >
            {{ generating ? '生成中...' : '生成候选照' }}
          </n-button>
        </n-space>
      </n-space>

      <n-spin :show="generating" description="Seedream 5.0 生成中，每张约 30 秒...">
        <n-grid v-if="candidates.length > 0" :cols="4" :x-gap="8" :y-gap="8">
          <n-gi v-for="(url, idx) in candidates" :key="idx">
            <div
              :class="['candidate-card', { selected: selectedIdx === idx }]"
              @click="openPreview(idx)"
            >
              <img :src="toUrl(url)" alt="" />
              <div v-if="selectedIdx === idx" class="badge">已选</div>
            </div>
          </n-gi>
        </n-grid>
        <n-text v-else depth="3" style="font-size: 13px">点击"生成候选照"开始</n-text>
      </n-spin>

      <n-button
        v-if="selectedIdx !== null"
        type="success"
        block
        :loading="settingBase"
        @click="handleSetBase"
      >
        {{ settingBase ? '设置中...' : '选为基准图' }}
      </n-button>
    </n-space>

    <!-- 放大预览弹窗 -->
    <n-modal v-model:show="previewVisible" preset="card" style="max-width: 600px;" :bordered="false" :closable="true">
      <template #header>
        <n-text>候选照 {{ (previewIdx ?? 0) + 1 }} / {{ candidates.length }}</n-text>
      </template>
      <div v-if="previewIdx !== null" class="preview-content">
        <img :src="toUrl(candidates[previewIdx])" class="preview-img" />
        <n-space justify="center" style="margin-top: 16px;">
          <n-button @click="navigatePreview(-1)" :disabled="previewIdx <= 0">上一张</n-button>
          <n-button type="success" @click="confirmAsBase">选为基准图</n-button>
          <n-button @click="navigatePreview(1)" :disabled="previewIdx >= candidates.length - 1">下一张</n-button>
        </n-space>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NGi, NGrid, NInputNumber, NModal, NSpace, NSpin, NTag, NText, useMessage } from 'naive-ui'
import { charactersApi } from '../api/characters'

const props = defineProps<{ characterId: string }>()
const emit = defineEmits<{ (e: 'base-image-set', url: string): void }>()

const message = useMessage()
const candidateCount = ref(4)
const candidates = ref<string[]>([])
const selectedIdx = ref<number | null>(null)
const generating = ref(false)
const settingBase = ref(false)
const previewVisible = ref(false)
const previewIdx = ref<number | null>(null)

// 加载已保存的候选照
onMounted(async () => {
  try {
    const resp = await charactersApi.getById(props.characterId)
    const saved = resp.data.traits?.candidate_images
    if (Array.isArray(saved) && saved.length > 0) {
      candidates.value = saved
    }
  } catch { /* ignore */ }
})

async function handleGenerate(): Promise<void> {
  generating.value = true
  try {
    const resp = await charactersApi.generateCandidates(props.characterId, { count: candidateCount.value })
    candidates.value = resp.data.candidates
    selectedIdx.value = null
    message.success(`生成 ${resp.data.count} 张候选照`)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
    message.error(detail)
  } finally {
    generating.value = false
  }
}

function openPreview(idx: number): void {
  previewIdx.value = idx
  previewVisible.value = true
}

function navigatePreview(delta: number): void {
  if (previewIdx.value === null) return
  previewIdx.value += delta
}

async function confirmAsBase(): Promise<void> {
  if (previewIdx.value === null) return
  selectedIdx.value = previewIdx.value
  previewVisible.value = false
  await handleSetBase()
}

async function handleSetBase(): Promise<void> {
  if (selectedIdx.value === null) return
  settingBase.value = true
  try {
    const url = candidates.value[selectedIdx.value]
    await charactersApi.setBaseImage(props.characterId, { image_url: url })
    message.success('基准图设置成功')
    emit('base-image-set', url)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '设置失败'
    message.error(detail)
  } finally {
    settingBase.value = false
  }
}

function toUrl(url: string): string {
  if (url.startsWith('http')) return url
  return `http://localhost:8000${url}`
}
</script>

<style scoped>
.candidate-card {
  position: relative;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}
.candidate-card:hover { border-color: #e0e0e0; }
.candidate-card.selected { border-color: #18a058; }
.candidate-card img {
  width: 100%;
  height: 160px;
  object-fit: cover;
  display: block;
}
.badge {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(24, 160, 88, 0.9);
  color: white;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}
.preview-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.preview-img {
  max-width: 100%;
  max-height: 70vh;
  border-radius: 8px;
  display: block;
}
</style>
