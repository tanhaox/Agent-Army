<template>
  <div class="angle-generator">
    <n-space vertical :size="12">
      <n-space align="center">
        <n-text strong>步骤 2：生成多角度参考图</n-text>
        <n-tag v-if="baseImageUrl" type="success" size="small">基准图已设置</n-tag>
      </n-space>

      <!-- 基准图预览 -->
      <div v-if="baseImageUrl" class="base-preview">
        <img :src="toUrl(baseImageUrl)" alt="基准图" />
      </div>
      <n-text v-else type="warning" style="font-size: 13px">请先在步骤 1 中选择基准图</n-text>

      <!-- 角度选择 -->
      <n-checkbox-group v-model:value="selectedAngles">
        <n-space :size="8">
          <n-checkbox v-for="opt in angleOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
        </n-space>
      </n-checkbox-group>

      <!-- 生成按钮 -->
      <n-button
        type="primary"
        block
        :disabled="!baseImageUrl || selectedAngles.length === 0"
        :loading="generating"
        @click="handleGenerate"
      >
        {{ generating ? '生成中...' : `生成 ${selectedAngles.length} 个角度` }}
      </n-button>

      <!-- 结果网格 -->
      <n-grid v-if="Object.keys(results).length > 0" :cols="2" :x-gap="8" :y-gap="8">
        <n-gi v-for="(url, angle) in results" :key="angle">
          <n-card size="small">
            <template #header>
              <n-text style="font-size: 13px">{{ getLabel(angle as string) }}</n-text>
            </template>
            <img :src="toUrl(url as string)" alt="" style="width: 100%; border-radius: 4px;" />
          </n-card>
        </n-gi>
      </n-grid>
    </n-space>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { NButton, NCard, NCheckbox, NCheckboxGroup, NGi, NGrid, NSpace, NTag, NText, useMessage } from 'naive-ui'
import { charactersApi } from '../api/characters'

const props = defineProps<{
  characterId: string
  baseImageUrl?: string | null
}>()
const emit = defineEmits<{ (e: 'angles-generated'): void }>()
const message = useMessage()

const angleOptions = [
  { label: '左侧面', value: 'left_side' },
  { label: '右侧面', value: 'right_side' },
  { label: '背面', value: 'back' },
  { label: '正面特写', value: 'closeup_face' },
  { label: '正面全身', value: 'front_full' },
]

const selectedAngles = ref<string[]>(['left_side', 'right_side', 'back', 'closeup_face'])
const generating = ref(false)
const results = ref<Record<string, string>>({})

// 加载已保存的多角度结果
onMounted(async () => {
  try {
    const resp = await charactersApi.getById(props.characterId)
    const saved = resp.data.traits?.angle_images
    if (saved && typeof saved === 'object') {
      results.value = saved as Record<string, string>
    }
  } catch { /* ignore */ }
})

async function handleGenerate(): Promise<void> {
  if (selectedAngles.value.length === 0) return
  generating.value = true
  try {
    const resp = await charactersApi.generateAngles(props.characterId, { angles: selectedAngles.value })
    results.value = { ...results.value, ...resp.data.angles }
    message.success(`成功生成 ${resp.data.count} 个角度`)
    emit('angles-generated')
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
    message.error(detail)
  } finally {
    generating.value = false
  }
}

function getLabel(angle: string): string {
  return angleOptions.find(o => o.value === angle)?.label || angle
}

function toUrl(url: string): string {
  if (url.startsWith('http')) return url
  return `http://localhost:8000${url}`
}
</script>

<style scoped>
.base-preview img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 2px solid #e0e0e0;
}
</style>
