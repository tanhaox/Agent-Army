<template>
  <div>
    <n-page-header :title="providerData?.display_name || '加载中...'" :subtitle="providerData?.description || ''">
      <template #header>
        <n-button quaternary @click="router.push('/system-settings')">
          ← 返回
        </n-button>
      </template>
      <template #extra>
        <n-button type="primary" :loading="saving" :disabled="!providerData" @click="handleSave">
          保存配置
        </n-button>
      </template>
    </n-page-header>

    <n-spin :show="loading" style="margin-top: 16px;">
      <n-space vertical size="large">
        <!-- 配置表单 -->
        <n-card v-if="providerData" title="配置参数">
          <n-form label-placement="left" label-width="180" :show-feedback="false">
            <n-grid :cols="1" :y-gap="20">
              <n-form-item-gi
                v-for="field in providerData.fields"
                :key="field.key"
                :label="field.label"
              >
                <template #label>
                  <div>
                    <div>{{ field.label }}</div>
                    <n-text v-if="field.description" depth="3" style="font-size: 12px;">{{ field.description }}</n-text>
                  </div>
                </template>
                <!-- 敏感字段 -->
                <n-input
                  v-if="field.sensitive"
                  :value="formValues[field.key] || ''"
                  @update:value="(v: string) => formValues[field.key] = v"
                  type="password"
                  show-password-on="click"
                  :placeholder="String(providerData.configs[field.key] || '未配置')"
                  clearable
                />
                <!-- 数字字段 -->
                <n-input-number
                  v-else-if="field.type === 'number'"
                  :value="formValues[field.key] !== undefined && formValues[field.key] !== '' ? Number(formValues[field.key]) : ((providerData.configs[field.key] as number) ?? (field.default as number))"
                  @update:value="(v: number | null) => formValues[field.key] = v == null ? '' : String(v)"
                  style="width: 100%;"
                />
                <!-- 文本字段 -->
                <n-input
                  v-else
                  :value="formValues[field.key] || ''"
                  @update:value="(v: string) => formValues[field.key] = v"
                  :placeholder="String(providerData.configs[field.key] || field.default || '')"
                  clearable
                />
              </n-form-item-gi>
            </n-grid>
          </n-form>
        </n-card>

        <!-- 获取教程 -->
        <n-card
          v-if="providerData?.tutorial?.length"
          title="如何获取 API Key？"
          style="margin-top: 8px;"
        >
          <n-steps vertical>
            <n-step
              v-for="item in providerData.tutorial"
              :key="item.step"
              :title="`${item.step}. ${item.title}`"
            >
              <n-text style="margin-top: 4px; display: block;">{{ item.content }}</n-text>
              <n-button
                v-if="item.link"
                tag="a"
                :href="item.link"
                target="_blank"
                size="small"
                type="primary"
                secondary
                style="margin-top: 8px;"
              >
                {{ item.link_text || '前往' }} ↗
              </n-button>
            </n-step>
          </n-steps>
        </n-card>
      </n-space>
    </n-spin>

    <n-modal
      v-model:show="showRestartTip"
      preset="card"
      title="配置已保存"
      style="max-width: 400px;"
      :closable="true"
    >
      <n-alert type="warning" title="需要重启服务">
        配置已更新，部分服务需要重启后端才能生效。
      </n-alert>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NPageHeader,
  NButton,
  NSpin,
  NSpace,
  NCard,
  NForm,
  NGrid,
  NFormItemGi,
  NInput,
  NInputNumber,
  NModal,
  NAlert,
  NText,
  NSteps,
  NStep,
  useMessage,
} from 'naive-ui'
import apiClient from '../api'

const router = useRouter()
const route = useRoute()
const message = useMessage()

interface FieldSchema {
  key: string
  label: string
  type: 'text' | 'password' | 'number'
  required: boolean
  sensitive: boolean
  default?: unknown
  description: string
}

interface TutorialStep {
  step: number
  title: string
  content: string
  link?: string
  link_text?: string
}

interface ProviderDetail {
  provider: string
  display_name: string
  description: string
  fields: FieldSchema[]
  tutorial: TutorialStep[]
  configs: Record<string, unknown>
}

const loading = ref(false)
const saving = ref(false)
const providerData = ref<ProviderDetail | null>(null)
const formValues = reactive<Record<string, string>>({})
const showRestartTip = ref(false)

function resetForm(): void {
  for (const key of Object.keys(formValues)) {
    delete formValues[key]
  }
}

async function fetchConfig(): Promise<void> {
  const provider = route.params.provider as string
  if (!provider) return

  loading.value = true
  resetForm()
  try {
    const resp = await apiClient.get<ProviderDetail>(`/system-settings/providers/${provider}`)
    providerData.value = resp.data
  } catch {
    message.error('加载配置失败')
    providerData.value = null
  } finally {
    loading.value = false
  }
}

async function handleSave(): Promise<void> {
  if (!providerData.value) return
  const provider = providerData.value.provider

  const updates: Record<string, string> = {}
  for (const [k, v] of Object.entries(formValues)) {
    if (v !== '') {
      updates[k] = v
    }
  }

  if (Object.keys(updates).length === 0) {
    message.info('没有需要更新的配置')
    return
  }

  saving.value = true
  try {
    const resp = await apiClient.put(`/system-settings/providers/${provider}`, { configs: updates })
    message.success(`${resp.data.display_name} 配置已更新`)
    resetForm()
    showRestartTip.value = true
    await fetchConfig()
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(fetchConfig)
watch(() => route.params.provider, () => fetchConfig())
</script>
