<template>
  <div class="project-detail">
    <n-spin :show="loading">
      <template v-if="project">
        <!-- 顶部信息栏 -->
        <n-page-header @back="router.push('/projects')">
          <template #title>{{ project.name }}</template>
          <template #extra>
            <n-space>
              <n-button size="small" @click="showEditModal = true">编辑信息</n-button>
              <n-button type="primary" size="small" @click="handleCreateSnapshot">创建快照</n-button>
            </n-space>
          </template>
        </n-page-header>
        <n-text depth="3" style="margin-top: 4px; display: block;">{{ project.description || '暂无描述' }}</n-text>

        <!-- 标签页 -->
        <n-tabs type="line" style="margin-top: 20px;" v-model:value="activeTab">
          <n-tab-pane name="overview" tab="剧本与分镜">
            <n-card size="small">
              <template v-if="currentScript">
                <n-descriptions bordered :column="2" label-placement="left" size="small">
                  <n-descriptions-item label="当前剧本">{{ currentScript.project_name }}</n-descriptions-item>
                  <n-descriptions-item label="创建时间">{{ formatDate(currentScript.created_at) }}</n-descriptions-item>
                </n-descriptions>
                <n-text depth="3" style="margin-top: 8px; display: block; font-size: 13px;">
                  剧本主题: {{ currentScript.theme }}
                </n-text>
              </template>
              <n-empty v-else description="暂未关联剧本，请先生成剧本并关联" />
            </n-card>
          </n-tab-pane>

          <n-tab-pane name="snapshots" tab="版本快照">
            <n-spin :show="loadingSnapshots">
              <n-empty v-if="snapshots.length === 0" description="暂无快照" size="small" />
              <n-list v-else bordered>
                <n-list-item v-for="snap in snapshots" :key="snap.id">
                  <n-thing>
                    <template #header>{{ snap.snapshot_name }}</template>
                    <template #description>
                      <n-text depth="3" style="font-size: 12px;">{{ formatDate(snap.created_at) }}</n-text>
                      <n-text v-if="snap.snapshot_meta?.remark" depth="3" style="font-size: 12px; margin-left: 12px;">
                        备注: {{ snap.snapshot_meta.remark as string }}
                      </n-text>
                    </template>
                    <template #header-extra>
                      <n-space size="small">
                        <n-button size="tiny" @click="handleViewSnapshot(snap)">查看</n-button>
                        <n-button size="tiny" type="primary" @click="handleRestore(snap)">恢复</n-button>
                        <n-checkbox
                          :checked="compareIds.includes(snap.id)"
                          @update:checked="(v: boolean) => toggleCompare(snap.id, v)"
                        >
                          对比
                        </n-checkbox>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </n-spin>

            <!-- 对比按钮 -->
            <n-button
              v-if="compareIds.length === 2"
              type="info"
              style="margin-top: 12px;"
              @click="handleCompare"
              :loading="comparing"
            >
              对比选中的 2 个快照
            </n-button>
            <n-text v-else-if="compareIds.length === 1" depth="3" style="margin-top: 12px; display: block; font-size: 12px;">
              已选 1 个，再选 1 个即可对比
            </n-text>
          </n-tab-pane>

          <n-tab-pane name="compare" tab="对比结果" :disabled="!compareResult">
            <template v-if="compareResult">
              <n-card title="剧本差异" size="small" style="margin-bottom: 16px;">
                <n-descriptions bordered :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="快照 A">{{ compareResult.snapshot_1_name }}</n-descriptions-item>
                  <n-descriptions-item label="快照 B">{{ compareResult.snapshot_2_name }}</n-descriptions-item>
                  <n-descriptions-item label="标题变化">
                    <n-text v-if="!compareResult.script_diff.title_changed" type="success">无变化</n-text>
                    <n-text v-else type="warning">
                      {{ compareResult.script_diff.title_1 }} → {{ compareResult.script_diff.title_2 }}
                    </n-text>
                  </n-descriptions-item>
                  <n-descriptions-item label="集数变化">
                    {{ compareResult.script_diff.episodes_count_1 }} 集 → {{ compareResult.script_diff.episodes_count_2 }} 集
                  </n-descriptions-item>
                </n-descriptions>

                <template v-if="((compareResult.script_diff as any).episodes_detail as any[]).length > 0">
                  <n-h5 style="margin: 12px 0 8px;">集数详情变化</n-h5>
                  <n-list size="small" bordered>
                    <n-list-item v-for="(ep, idx) in (compareResult.script_diff as any).episodes_detail" :key="idx">
                      <n-text :type="(ep as any).change === 'added' ? 'success' : (ep as any).change === 'removed' ? 'error' : 'warning'">
                        第{{ (ep as any).episode }}集 {{ (ep as any).change === 'added' ? '(新增)' : (ep as any).change === 'removed' ? '(删除)' : '(已修改)' }}
                      </n-text>
                    </n-list-item>
                  </n-list>
                </template>
              </n-card>

              <n-card title="分镜差异" size="small">
                <n-descriptions bordered :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="分镜数">
                    {{ compareResult.storyboards_diff.count_1 }} → {{ compareResult.storyboards_diff.count_2 }}
                  </n-descriptions-item>
                </n-descriptions>

                <template v-if="(compareResult.storyboards_diff.added as string[]).length > 0">
                  <n-text type="success" style="margin-top: 8px; display: block;">
                    新增镜头: {{ (compareResult.storyboards_diff.added as string[]).join(', ') }}
                  </n-text>
                </template>
                <template v-if="(compareResult.storyboards_diff.removed as string[]).length > 0">
                  <n-text type="error" style="margin-top: 4px; display: block;">
                    删除镜头: {{ (compareResult.storyboards_diff.removed as string[]).join(', ') }}
                  </n-text>
                </template>
                <template v-if="(compareResult.storyboards_diff.modified as Array<Record<string, unknown>>).length > 0">
                  <n-text type="warning" style="margin-top: 4px; display: block;">
                    修改镜头: {{ (compareResult.storyboards_diff.modified as Array<Record<string, unknown>>).map(m => m.key).join(', ') }}
                  </n-text>
                </template>
                <template v-if="!(compareResult.storyboards_diff.added as string[]).length && !(compareResult.storyboards_diff.removed as string[]).length && !(compareResult.storyboards_diff.modified as Array<Record<string, unknown>>).length">
                  <n-text type="success" style="margin-top: 8px; display: block;">分镜无变化</n-text>
                </template>
              </n-card>
            </template>
          </n-tab-pane>
        </n-tabs>
      </template>
    </n-spin>

    <!-- 编辑项目弹窗 -->
    <n-modal
      v-model:show="showEditModal"
      preset="dialog"
      title="编辑项目"
      positive-text="保存"
      negative-text="取消"
      @positive-click="handleUpdate"
    >
      <n-form label-placement="top">
        <n-form-item label="项目名称">
          <n-input v-model:value="editForm.name" />
        </n-form-item>
        <n-form-item label="项目描述">
          <n-input v-model:value="editForm.description" type="textarea" :rows="3" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 快照详情弹窗 -->
    <n-modal
      v-model:show="showSnapshotModal"
      preset="dialog"
      :title="viewingSnapshot?.snapshot_name || '快照详情'"
      style="width: 600px;"
    >
      <template v-if="viewingSnapshotDetail">
        <n-descriptions bordered :column="1" label-placement="left" size="small">
          <n-descriptions-item label="快照名称">{{ viewingSnapshotDetail.snapshot_name }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">{{ formatDate(viewingSnapshotDetail.created_at) }}</n-descriptions-item>
          <n-descriptions-item label="分镜数量">
            {{ viewingSnapshotDetail.storyboards_snapshot?.length || 0 }}
          </n-descriptions-item>
          <n-descriptions-item label="剧本标题">
            {{ (viewingSnapshotDetail.script_snapshot as Record<string, unknown>)?.title || '-' }}
          </n-descriptions-item>
        </n-descriptions>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NButton, NCard, NCheckbox, NDescriptions, NDescriptionsItem, NEmpty,
  NForm, NFormItem, NH5, NInput, NList, NListItem, NModal,
  NPageHeader, NSpace, NSpin, NTabs, NTabPane, NText, NThing, useMessage,
} from 'naive-ui'
import {
  projectsApi,
  type ProjectResponse,
  type SnapshotBriefResponse,
  type SnapshotDetailResponse,
  type CompareResponse,
} from '../api/projects'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const projectId = route.params.id as string
const loading = ref(false)
const loadingSnapshots = ref(false)
const comparing = ref(false)
const project = ref<ProjectResponse | null>(null)
const currentScript = ref<{project_name: string; theme: string; created_at: string} | null>(null)
const snapshots = ref<SnapshotBriefResponse[]>([])
const compareIds = ref<string[]>([])
const compareResult = ref<CompareResponse | null>(null)
const activeTab = ref('overview')

const showEditModal = ref(false)
const showSnapshotModal = ref(false)
const viewingSnapshot = ref<SnapshotBriefResponse | null>(null)
const viewingSnapshotDetail = ref<SnapshotDetailResponse | null>(null)

const editForm = reactive({ name: '', description: '' })

async function fetchProject() {
  loading.value = true
  try {
    const resp = await projectsApi.getById(projectId)
    project.value = resp.data
    editForm.name = resp.data.name
    editForm.description = resp.data.description || ''
    if (resp.data.current_script_id) {
      await fetchCurrentScript(resp.data.current_script_id)
    }
  } catch {
    message.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

async function fetchCurrentScript(_scriptId: string) {
  // 简化：只显示有剧本关联的信息，不获取完整详情
  currentScript.value = { project_name: project.value?.name || '', theme: '已关联', created_at: project.value?.created_at || '' }
}

async function fetchSnapshots() {
  loadingSnapshots.value = true
  try {
    const resp = await projectsApi.listSnapshots(projectId)
    snapshots.value = resp.data
  } catch {
    // ignore
  } finally {
    loadingSnapshots.value = false
  }
}

async function handleUpdate(): Promise<boolean> {
  try {
    const resp = await projectsApi.update(projectId, {
      name: editForm.name || undefined,
      description: editForm.description || undefined,
    })
    project.value = resp.data
    message.success('项目信息已更新')
    return true
  } catch {
    message.error('更新失败')
    return false
  }
}

async function handleCreateSnapshot() {
  try {
    await projectsApi.createSnapshot(projectId)
    message.success('快照已创建')
    await fetchSnapshots()
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '创建快照失败'
    message.error(detail)
  }
}

async function handleViewSnapshot(snap: SnapshotBriefResponse) {
  viewingSnapshot.value = snap
  showSnapshotModal.value = true
  try {
    const resp = await projectsApi.getSnapshot(projectId, snap.id)
    viewingSnapshotDetail.value = resp.data
  } catch {
    message.error('加载快照详情失败')
  }
}

async function handleRestore(snap: SnapshotBriefResponse) {
  try {
    const resp = await projectsApi.restoreSnapshot(projectId, snap.id)
    project.value = resp.data
    message.success('快照已恢复')
    await fetchProject()
  } catch {
    message.error('恢复快照失败')
  }
}

function toggleCompare(id: string, checked: boolean) {
  if (checked) {
    if (compareIds.value.length < 2) {
      compareIds.value.push(id)
    }
  } else {
    compareIds.value = compareIds.value.filter(i => i !== id)
  }
}

async function handleCompare() {
  if (compareIds.value.length !== 2) return
  comparing.value = true
  try {
    const resp = await projectsApi.compareSnapshots(projectId, compareIds.value[0], compareIds.value[1])
    compareResult.value = resp.data
    activeTab.value = 'compare'
  } catch {
    message.error('对比失败')
  } finally {
    comparing.value = false
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(async () => {
  await Promise.all([fetchProject(), fetchSnapshots()])
})
</script>

<style scoped>
.project-detail {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
