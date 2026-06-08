<template>
  <div class="character-manager">
    <!-- 顶部操作栏 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 16px;">
      <n-h2 style="margin: 0;">角色库</n-h2>
      <n-button type="primary" @click="showCreateModal = true">新建角色</n-button>
    </n-space>

    <!-- 角色卡片网格 -->
    <n-spin :show="loading">
      <n-empty v-if="!loading && characters.length === 0" description="暂无角色，点击右上角创建" />
      <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
        <n-gi v-for="char in characters" :key="char.id">
          <n-card hoverable class="character-card" @click="openDetail(char)">
            <template #header>
              <n-text strong>{{ char.name }}</n-text>
            </template>
            <template #header-extra>
              <n-dropdown :options="cardActions" @select="(key: string) => handleAction(key, char)">
                <n-button quaternary size="small">
                  <template #icon>
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                      <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                    </svg>
                  </template>
                </n-button>
              </n-dropdown>
            </template>
            <!-- 参考图缩略图 -->
            <div v-if="char.reference_images.length > 0" class="thumb-grid">
              <img
                v-for="(img, idx) in char.reference_images.slice(0, 3)"
                :key="idx"
                :src="getImageUrl(img)"
                class="thumb"
                @error="($event.target as HTMLImageElement).style.display='none'"
              />
            </div>
            <n-text v-else depth="3" style="font-size: 13px;">暂无参考图</n-text>
            <!-- 特征摘要 -->
            <n-space style="margin-top: 8px;" :size="4">
              <n-tag v-if="char.traits.age" size="tiny">{{ char.traits.age }}岁</n-tag>
              <n-tag v-if="char.traits.personality" size="tiny" type="info">
                {{ truncate(char.traits.personality, 8) }}
              </n-tag>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>

    <!-- 创建角色对话框 -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="新建角色" positive-text="创建" negative-text="取消"
      @positive-click="handleCreate"
    >
      <n-form ref="createFormRef" :model="createForm" label-placement="top">
        <n-form-item label="角色名称" required>
          <n-input v-model:value="createForm.name" placeholder="例如：林小夏" :maxlength="200" />
        </n-form-item>
        <n-form-item label="年龄">
          <n-input-number v-model:value="createForm.age" placeholder="25" :min="1" :max="200" style="width: 100%;" />
        </n-form-item>
        <n-form-item label="性格">
          <n-input v-model:value="createForm.personality" placeholder="例如：外冷内热" />
        </n-form-item>
        <n-form-item label="外貌">
          <n-input v-model:value="createForm.appearance" placeholder="例如：短发、黑眸、身材高挑" type="textarea" :rows="2" />
        </n-form-item>
      </n-form>
    </n-modal>

    <!-- 角色详情抽屉 -->
    <n-drawer v-model:show="showDetail" :width="520">
      <n-drawer-content :title="selectedChar?.name || '角色详情'">
        <template v-if="selectedChar">
          <n-tabs type="line" animated>
            <!-- Tab: 基本信息 -->
            <n-tab-pane name="basic" tab="基本信息">
              <n-space justify="end" style="margin-bottom: 12px;">
                <n-button v-if="!editing" size="small" @click="startEdit">编辑</n-button>
                <template v-else>
                  <n-button size="small" @click="cancelEdit">取消</n-button>
                  <n-button size="small" type="primary" :loading="saving" @click="handleSaveEdit">保存</n-button>
                </template>
              </n-space>

              <!-- 只读模式 -->
              <n-descriptions v-if="!editing" bordered :column="1" label-style="width: 100px;">
                <n-descriptions-item label="年龄">{{ selectedChar.traits.age || '-' }}</n-descriptions-item>
                <n-descriptions-item label="性格">{{ selectedChar.traits.personality || '-' }}</n-descriptions-item>
                <n-descriptions-item label="外貌">{{ selectedChar.traits.appearance || '-' }}</n-descriptions-item>
                <n-descriptions-item label="服饰">{{ selectedChar.traits.clothing || '-' }}</n-descriptions-item>
                <n-descriptions-item label="特殊特征">{{ selectedChar.traits.special_features || '-' }}</n-descriptions-item>
              </n-descriptions>

              <!-- 基准图 -->
              <template v-if="!editing && selectedChar.base_image_url">
                <n-divider>基准图</n-divider>
                <div style="text-align: center;">
                  <img :src="getImageUrl(selectedChar.base_image_url)" style="max-width: 200px; max-height: 200px; border-radius: 8px; border: 2px solid #e0e0e0;" />
                </div>
              </template>

              <!-- 编辑模式 -->
              <n-form v-else :model="editForm" label-placement="top">
                <n-form-item label="年龄">
                  <n-input-number v-model:value="editForm.age" placeholder="25" :min="1" :max="200" style="width: 100%;" />
                </n-form-item>
                <n-form-item label="性格">
                  <n-input v-model:value="editForm.personality" type="textarea" :rows="2" />
                </n-form-item>
                <n-form-item label="外貌">
                  <n-input v-model:value="editForm.appearance" type="textarea" :rows="3" />
                </n-form-item>
                <n-form-item label="服饰">
                  <n-input v-model:value="editForm.clothing" type="textarea" :rows="2" />
                </n-form-item>
                <n-form-item label="特殊特征">
                  <n-input v-model:value="editForm.special_features" type="textarea" :rows="1" />
                </n-form-item>
              </n-form>

              <n-divider>参考图</n-divider>
              <n-grid :cols="3" :x-gap="8" :y-gap="8">
                <n-gi v-for="(img, idx) in selectedChar.reference_images" :key="idx">
                  <img :src="getImageUrl(img)" style="width: 100%; border-radius: 6px; display: block;"
                       @error="($event.target as HTMLImageElement).parentElement!.style.display='none'" />
                </n-gi>
              </n-grid>
              <n-text v-if="selectedChar.reference_images.length === 0" depth="3">暂无参考图</n-text>
              <n-upload style="margin-top: 12px;" :max="1" accept=".jpg,.jpeg,.png,.webp" :custom-request="handleUpload" :show-file-list="false">
                <n-button size="small">上传参考图</n-button>
              </n-upload>
            </n-tab-pane>

            <!-- Tab: Seedream 多角度生成 -->
            <n-tab-pane name="seedream" tab="多角度生成">
              <n-space vertical :size="16">
                <n-alert type="info" :closable="false" style="font-size: 13px;">
                  使用 Seedream 5.0 图生图保持角色一致性。先生成候选正面照，选择基准图后生成其他角度。
                </n-alert>
                <CharacterCandidateSelector
                  :character-id="selectedChar.id"
                  @base-image-set="handleBaseImageSet"
                />
                <n-divider style="margin: 4px 0;" />
                <CharacterAngleGenerator
                  :character-id="selectedChar.id"
                  :base-image-url="selectedChar.base_image_url"
                  @angles-generated="handleBaseImageSet"
                />
              </n-space>
            </n-tab-pane>
          </n-tabs>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import {
  NAlert, NButton, NCard, NDescriptions, NDescriptionsItem, NDivider, NDrawer, NDrawerContent,
  NEmpty, NForm, NFormItem, NGi, NGrid, NH2, NInput, NInputNumber,
  NModal, NSpace, NSpin, NTabPane, NTabs, NTag, NText, NUpload, NDropdown, useMessage,
} from 'naive-ui'
import type { UploadSettledFileInfo, DropdownOption } from 'naive-ui'
import { charactersApi, type CharacterResponse, type ReferenceImageItem } from '../api/characters'
import CharacterCandidateSelector from '../components/CharacterCandidateSelector.vue'
import CharacterAngleGenerator from '../components/CharacterAngleGenerator.vue'

const message = useMessage()
const loading = ref(false)
const characters = ref<CharacterResponse[]>([])
const showCreateModal = ref(false)
const showDetail = ref(false)
const selectedChar = ref<CharacterResponse | null>(null)
const editing = ref(false)
const saving = ref(false)
const editForm = reactive({
  age: undefined as number | undefined,
  personality: '',
  appearance: '',
  clothing: '',
  special_features: '',
})

const createForm = reactive({
  name: '',
  age: undefined as number | undefined,
  personality: '',
  appearance: '',
})

/** 下拉菜单选项。 */
const cardActions: DropdownOption[] = [
  { label: '删除', key: 'delete' },
]

/** 加载角色列表。 */
async function fetchCharacters(): Promise<void> {
  loading.value = true
  try {
    const resp = await charactersApi.list()
    characters.value = resp.data
  } catch {
    message.error('加载角色列表失败')
  } finally {
    loading.value = false
  }
}

/** 创建角色。 */
async function handleCreate(): Promise<void> {
  if (!createForm.name.trim()) {
    message.warning('请输入角色名称')
    return
  }
  try {
    await charactersApi.create({
      name: createForm.name,
      traits: {
        age: createForm.age,
        personality: createForm.personality || undefined,
        appearance: createForm.appearance || undefined,
      },
    })
    message.success(`角色「${createForm.name}」创建成功`)
    createForm.name = ''
    createForm.age = undefined
    createForm.personality = ''
    createForm.appearance = ''
    await fetchCharacters()
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '创建失败'
    message.error(detail)
  }
}

/** 打开角色详情。 */
function openDetail(char: CharacterResponse): void {
  selectedChar.value = char
  editing.value = false
  showDetail.value = true
}

/** 进入编辑模式。 */
function startEdit(): void {
  if (!selectedChar.value) return
  const t = selectedChar.value.traits
  editForm.age = t.age as number | undefined
  editForm.personality = (t.personality as string) || ''
  editForm.appearance = (t.appearance as string) || ''
  editForm.clothing = (t.clothing as string) || ''
  editForm.special_features = (t.special_features as string) || ''
  editing.value = true
}

/** 取消编辑。 */
function cancelEdit(): void {
  editing.value = false
}

/** 保存编辑。 */
async function handleSaveEdit(): Promise<void> {
  if (!selectedChar.value) return
  saving.value = true
  try {
    const resp = await charactersApi.update(selectedChar.value.id, {
      traits: {
        ...selectedChar.value.traits,
        age: editForm.age,
        personality: editForm.personality || undefined,
        appearance: editForm.appearance || undefined,
        clothing: editForm.clothing || undefined,
        special_features: editForm.special_features || undefined,
      },
    })
    selectedChar.value = resp.data
    editing.value = false
    message.success('角色信息已更新')
    await fetchCharacters()
  } catch {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

/** 上传参考图。 */
async function handleUpload({ file }: { file: UploadSettledFileInfo }): Promise<void> {
  if (!selectedChar.value) return
  try {
    const resp = await charactersApi.uploadImage(selectedChar.value.id, file.file as File)
    selectedChar.value = resp.data
    message.success('参考图上传成功')
    await fetchCharacters()
  } catch {
    message.error('上传失败')
  }
}

/** 操作菜单处理。 */
async function handleAction(key: string, char: CharacterResponse): Promise<void> {
  if (key === 'delete') {
    try {
      await charactersApi.delete(char.id)
      message.success(`角色「${char.name}」已删除`)
      await fetchCharacters()
    } catch {
      message.error('删除失败')
    }
  }
}

/** 基准图设置后刷新角色信息。 */
async function handleBaseImageSet(): Promise<void> {
  if (!selectedChar.value) return
  try {
    const resp = await charactersApi.getById(selectedChar.value.id)
    selectedChar.value = resp.data
    await fetchCharacters()
  } catch {
    message.error('刷新角色信息失败')
  }
}

/** 拼接图片完整 URL，兼容字符串和对象格式。 */
function getImageUrl(img: string | ReferenceImageItem): string {
  const path = typeof img === 'string' ? img : img.url
  if (path.startsWith('http')) return path
  return `http://localhost:8000${path}`
}

/** 截断文本。 */
function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max) + '...' : text
}

onMounted(() => {
  fetchCharacters()
})
</script>

<style scoped>
.character-manager {
  max-width: 960px;
  margin: 0 auto;
}

.character-card {
  cursor: pointer;
}

.thumb-grid {
  display: flex;
  gap: 4px;
}

.thumb {
  width: 64px;
  height: 64px;
  object-fit: cover;
  border-radius: 6px;
}
</style>
