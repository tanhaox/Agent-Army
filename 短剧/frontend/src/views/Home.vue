<template>
  <div class="home-view">
    <!-- 欢迎卡片 -->
    <n-card title="欢迎使用 短剧AI - 智能制片工厂" style="margin-bottom: 24px;">
      <n-text depth="2">
        从创意到成片的全流程 AI 短剧生产系统。选择下方功能模块开始创作。
      </n-text>
    </n-card>

    <!-- 功能入口 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-gi>
        <n-card hoverable class="feature-card" @click="handleFeature('创建项目')">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="48" height="48">
              <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
            </svg>
          </div>
          <n-h3 style="margin: 12px 0 8px;">创建项目</n-h3>
          <n-text depth="3">
            从创意到剧本的全流程创作：叙事树 → 多版本概要 → 质量检测剧本。
          </n-text>
          <template #action>
            <n-button type="primary" block>开始创作</n-button>
          </template>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card hoverable class="feature-card" @click="handleFeature('角色设计')">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="48" height="48">
              <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
            </svg>
          </div>
          <n-h3 style="margin: 12px 0 8px;">角色设计</n-h3>
          <n-text depth="3">
            创建数字演员，管理角色卡、参考图、关系图谱，保证跨镜头一致性。
          </n-text>
          <template #action>
            <n-button type="primary" block>创建角色</n-button>
          </template>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card hoverable class="feature-card" @click="handleFeature('分镜设计')">
          <div class="feature-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="48" height="48">
              <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z" />
            </svg>
          </div>
          <n-h3 style="margin: 12px 0 8px;">分镜设计</n-h3>
          <n-text depth="3">
            自动拆解剧本为分镜卡，指定景别、运镜、动作，生成视频提示词。
          </n-text>
          <template #action>
            <n-button type="primary" block>生成分镜</n-button>
          </template>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 系统状态 -->
    <n-card title="系统状态" style="margin-top: 24px;">
      <n-space>
        <n-tag :type="backendStatus === 'ok' ? 'success' : 'error'">
          后端服务: {{ backendStatus === 'ok' ? '在线' : '离线' }}
        </n-tag>
        <n-tag :type="deepseekStatus === 'ok' ? 'success' : 'warning'">
          DeepSeek: {{ deepseekStatus === 'ok' ? '在线' : '离线' }}
        </n-tag>
      </n-space>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NGrid,
  NGi,
  NH3,
  NText,
  NButton,
  NSpace,
  NTag,
  useMessage,
} from 'naive-ui'
import axios from 'axios'

const message = useMessage()
const router = useRouter()
const backendStatus = ref<string>('checking')
const deepseekStatus = ref<string>('checking')

/**
 * 功能入口点击处理。
 * 创建项目跳转到项目列表，其余显示开发中。
 */
function handleFeature(name: string): void {
  if (name === '创建项目') {
    router.push('/projects')
  } else {
    message.info(`${name} 功能开发中，敬请期待...`)
  }
}

/**
 * 页面加载时检查后端状态。
 */
async function checkSystemStatus(): Promise<void> {
  // 检查后端 — /health 不带 /api 前缀，用裸 axios 避免 baseURL 拼接
  try {
    const resp = await axios.get('/health', { timeout: 10000 })
    backendStatus.value = resp.data?.status === 'ok' ? 'ok' : 'error'
    deepseekStatus.value = resp.data?.deepseek?.status === 'ok' ? 'ok' : 'error'
  } catch {
    backendStatus.value = 'error'
    deepseekStatus.value = 'error'
  }
}

onMounted(() => {
  checkSystemStatus()
})
</script>

<style scoped>
.feature-card {
  cursor: pointer;
  text-align: center;
  transition: transform 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.feature-icon {
  color: #667eea;
  display: flex;
  justify-content: center;
}
</style>
