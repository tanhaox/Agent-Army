<template>
  <div class="project-list">
    <n-space justify="space-between" align="center" style="margin-bottom: 16px;">
      <n-h2 style="margin: 0;">项目管理</n-h2>
      <n-button type="primary" @click="showCreateModal = true">新建项目</n-button>
    </n-space>

    <n-spin :show="loading">
      <n-empty v-if="projects.length === 0 && !loading" description="暂无项目，点击右上角新建" />

      <n-grid :cols="3" :x-gap="16" :y-gap="16">
        <n-gi v-for="proj in projects" :key="proj.id">
          <n-card :title="proj.name" hoverable size="small" @click="goDetail(proj.id)" style="cursor: pointer;">
            <template #header-extra>
              <n-dropdown :options="cardActions(proj.id)" @select="handleAction($event, proj)">
                <n-button quaternary circle size="small">
                  <template #icon>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="1em" height="1em">
                      <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                    </svg>
                  </template>
                </n-button>
              </n-dropdown>
            </template>
            <n-text depth="3">{{ proj.description || '暂无描述' }}</n-text>
            <template #footer>
              <n-space justify="space-between" align="center">
                <n-text depth="3" style="font-size: 12px;">{{ formatDate(proj.created_at) }}</n-text>
                <n-button size="small" @click.stop="goDetail(proj.id)">进入项目</n-button>
              </n-space>
            </template>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- 新建项目弹窗 -->
    <n-modal
      v-model:show="showCreateModal"
      preset="dialog"
      title="新建项目"
      positive-text="创建"
      negative-text="取消"
      @positive-click="handleCreate"
    >
      <n-form label-placement="top">
        <n-form-item label="项目名称" required>
          <n-input v-model:value="createForm.name" placeholder="请输入项目名称" />
        </n-form-item>
        <n-form-item label="项目描述">
          <n-input v-model:value="createForm.description" type="textarea" :rows="3" placeholder="可选，描述项目内容" />
        </n-form-item>
      </n-form>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NCard, NDropdown, NEmpty, NForm, NFormItem, NGi, NGrid,
  NH2, NInput, NModal, NSpace, NSpin, NText, useMessage,
} from 'naive-ui'
import {
  projectsApi,
  type ProjectResponse,
} from '../api/projects'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const projects = ref<ProjectResponse[]>([])
const showCreateModal = ref(false)

const createForm = reactive({ name: '', description: '' })

function cardActions(_projectId: string) {
  return [
    { label: '编辑', key: 'edit' },
    { label: '删除', key: 'delete' },
  ]
}

async function fetchProjects() {
  loading.value = true
  try {
    const resp = await projectsApi.list()
    projects.value = resp.data
  } catch {
    message.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

function goDetail(projectId: string) {
  router.push(`/projects/${projectId}`)
}

async function handleCreate(): Promise<boolean> {
  if (!createForm.name.trim()) {
    message.warning('请输入项目名称')
    return false
  }
  try {
    await projectsApi.create({ name: createForm.name, description: createForm.description || undefined })
    message.success('项目已创建')
    createForm.name = ''
    createForm.description = ''
    await fetchProjects()
    return true
  } catch {
    message.error('创建项目失败')
    return false
  }
}

async function handleAction(action: string, proj: ProjectResponse) {
  if (action === 'delete') {
    try {
      await projectsApi.delete(proj.id)
      message.success(`项目"${proj.name}"已删除`)
      await fetchProjects()
    } catch {
      message.error('删除失败')
    }
  } else if (action === 'edit') {
    goDetail(proj.id)
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(() => fetchProjects())
</script>

<style scoped>
.project-list {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
