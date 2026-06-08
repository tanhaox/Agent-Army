<template>
  <div>
    <n-page-header title="系统设置" subtitle="管理各服务的 API Key 与配置参数" />

    <n-spin :show="loading" style="margin-top: 16px;">
      <n-grid :cols="2" :x-gap="16" :y-gap="16" responsive="screen">
        <n-gi v-for="provider in providers" :key="provider.provider">
          <n-card
            hoverable
            style="cursor: pointer;"
            @click="goProvider(provider.provider)"
          >
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="provider-icon">{{ iconMap[provider.icon] || '⚙' }}</span>
                <span>{{ provider.display_name }}</span>
              </div>
            </template>
            <template #header-extra>
              <n-tag :type="provider.configured ? 'success' : 'warning'" size="small">
                {{ provider.configured ? '已配置' : '未配置' }}
              </n-tag>
            </template>
            <n-text depth="3" style="font-size: 13px;">{{ provider.description }}</n-text>
            <div style="margin-top: 12px; display: flex; flex-wrap: wrap; gap: 6px;">
              <n-tag v-for="field in provider.fields" :key="field.key" size="tiny" :bordered="false" :type="field.sensitive ? 'error' : 'default'">
                {{ field.label }}
              </n-tag>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPageHeader,
  NSpin,
  NGrid,
  NGi,
  NCard,
  NTag,
  NText,
  useMessage,
} from 'naive-ui'
import apiClient from '../api'

const router = useRouter()
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

interface ProviderInfo {
  provider: string
  display_name: string
  description: string
  icon: string
  configured: boolean
  configs: Record<string, unknown>
  fields: FieldSchema[]
}

const loading = ref(false)
const providers = ref<ProviderInfo[]>([])

const iconMap: Record<string, string> = {
  brain: '🧠',
  fire: '🔥',
  video: '🎬',
  image: '🎨',
}

function goProvider(provider: string): void {
  router.push(`/system-settings/${provider}`)
}

async function fetchProviders(): Promise<void> {
  loading.value = true
  try {
    const resp = await apiClient.get<ProviderInfo[]>('/system-settings/providers')
    providers.value = resp.data
  } catch {
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchProviders)
</script>
