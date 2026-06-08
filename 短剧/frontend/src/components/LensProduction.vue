<template>
  <div class="lens-production">
    <n-spin :show="loading">
      <n-empty v-if="!loading && episodes.length === 0" description="暂无分镜数据，请先生成分镜" />

      <n-space v-else vertical :size="16">
        <!-- 顶部：集数选择 -->
        <n-space align="center" justify="space-between">
          <n-space align="center">
            <n-text strong>选择集数</n-text>
            <n-button-group>
              <n-button
                v-for="ep in episodes"
                :key="ep.episode_no"
                :type="currentEpisode === ep.episode_no ? 'primary' : 'default'"
                size="small"
                @click="switchEpisode(ep.episode_no)"
              >
                第{{ ep.episode_no }}集 ({{ ep.shots.length }}镜)
              </n-button>
            </n-button-group>
          </n-space>
          <n-button type="warning" size="small" @click="openBatchDialog" :disabled="batchSubmitting || currentShots.length === 0">
            批量生成 ({{ currentShots.length }}镜)
          </n-button>
        </n-space>

        <!-- 镜头卡片列表 -->
        <n-collapse v-if="currentShots.length > 0" :default-expanded-names="[currentShots[0]?.id]">
          <n-collapse-item
            v-for="shot in currentShots"
            :key="shot.id"
            :name="shot.id"
          >
            <template #header>
              <n-space align="center" :size="8">
                <n-tag size="small" :bordered="false">镜{{ shot.shot_no }}</n-tag>
                <n-tag size="tiny">{{ shot.shot_type }}</n-tag>
                <n-tag size="tiny" type="info">{{ shot.camera_move }}</n-tag>
                <n-tag size="tiny">{{ shot.duration_seconds }}s</n-tag>
                <n-tag v-if="shot.video_status === 'success'" size="tiny" type="success">视频已生成</n-tag>
                <n-tag v-else-if="shot.video_status === 'generating' || shot.video_status === 'pending' || shot.video_status === 'processing'" size="tiny" type="warning">生成中</n-tag>
                <n-tag v-else-if="shot.video_status === 'failed'" size="tiny" type="error">生成失败</n-tag>
              </n-space>
            </template>

            <n-grid :cols="24" :x-gap="16">
              <!-- 左列：基本信息 + 素材 -->
              <n-gi :span="14">
                <!-- 基本信息（只读） -->
                <n-descriptions bordered :column="2" size="small" label-style="width: 60px;">
                  <n-descriptions-item label="动作">{{ shot.action }}</n-descriptions-item>
                  <n-descriptions-item label="情绪">{{ shot.emotion }}</n-descriptions-item>
                  <n-descriptions-item label="环境">{{ shot.environment }}</n-descriptions-item>
                  <n-descriptions-item label="光线">{{ shot.lighting }}</n-descriptions-item>
                  <n-descriptions-item label="特效">{{ shot.vfx || '无' }}</n-descriptions-item>
                  <n-descriptions-item label="对话">{{ shot.dialogue || '—' }}</n-descriptions-item>
                </n-descriptions>

                <!-- 素材制作区域 -->
                <n-divider style="margin: 12px 0;">素材制作</n-divider>
                <n-space align="center" style="margin-bottom: 8px;">
                  <n-text strong style="font-size: 13px;">素材需求</n-text>
                  <n-button size="tiny" type="primary" :loading="directoring === shot.id" @click="handleDirector(shot)">
                    {{ directorAnalysis(shot) ? '重新导演' : '智能导演' }}
                  </n-button>
                </n-space>

                <!-- 无分析结果 -->
                <n-text v-if="!directorAnalysis(shot)" depth="3" style="font-size: 12px;">
                  点击"智能导演"分析素材需求
                </n-text>

                <!-- 素材卡片列表 -->
                <n-space v-else vertical :size="8">
                  <template v-for="req in getMaterialRequirements(shot)" :key="req.id">
                    <n-descriptions bordered :column="2" size="small" label-style="width: 70px;">
                      <n-descriptions-item label="素材">
                        <n-space align="center" :size="6">
                          <n-tag :type="getTypeColor(req.type)" size="tiny">{{ getTypeLabel(req.type) }}</n-tag>
                          <n-tag v-if="req.necessity === 'required'" size="tiny" type="warning" :bordered="false">必需</n-tag>
                          <n-text strong>{{ req.name }}</n-text>
                          <n-tag v-if="req.status === 'success'" size="tiny" type="success" :bordered="false">已生成</n-tag>
                          <n-tag v-else-if="req.status === 'uploaded'" size="tiny" type="info" :bordered="false">已上传</n-tag>
                          <n-tag v-else-if="req.status === 'failed'" size="tiny" type="error" :bordered="false">失败</n-tag>
                        </n-space>
                      </n-descriptions-item>
                      <n-descriptions-item label="说明">{{ req.reason || '—' }}</n-descriptions-item>
                    </n-descriptions>
                    <n-input
                      :ref="(el: any) => setPromptInputRef(shot.id, req.id, el)"
                      :value="getMaterialPrompt(shot.id, req.id)"
                      type="textarea"
                      :rows="2"
                      size="small"
                      placeholder="中文生图提示词，可用 @角色名 引用角色图"
                      @update:value="(v: string) => setMaterialPrompt(shot.id, req.id, v)"
                      @focus="() => {}"
                      @blur="saveCursorPos(shot.id, req.id)"
                    />
                    <n-space :size="6" align="center">
                      <n-popover trigger="click" placement="bottom-start" :width="680" style="max-height:420px;overflow-y:auto;">
                        <template #trigger>
                          <n-button size="tiny" @click="loadRefOptions">插入引用</n-button>
                        </template>
                        <div class="ref-panel">
                          <template v-for="grp in refGroups" :key="grp.key">
                            <div class="ref-group-header">{{ grp.label }}（{{ grp.items.length }}）</div>
                            <div class="ref-grid" :style="{ gridTemplateColumns: `repeat(${Math.min(Math.ceil(grp.items.length / 20), 4)}, 1fr)` }">
                              <div
                                v-for="item in grp.items"
                                :key="item.reference_mark"
                                class="ref-item"
                                @click="insertRef(shot.id, req.id, item.reference_mark)"
                              >
                                <img :src="getFullUrl(item.thumbnail_url)" class="ref-thumb" @error="($event.target as HTMLImageElement).style.display='none'" />
                                <span>{{ item.name }}</span>
                              </div>
                            </div>
                          </template>
                          <n-empty v-if="!refGroups.length" description="暂无可引用素材" size="small" />
                        </div>
                      </n-popover>
                      <div v-if="req.generated_url" class="material-preview">
                        <img :src="getFullUrl(req.generated_url)" @click="previewImage = getFullUrl(req.generated_url)" @error="($event.target as HTMLImageElement).style.display='none'" />
                      </div>
                      <n-button
                        size="tiny"
                        type="primary"
                        :loading="isGenerating(shot.id, req.id)"
                        :disabled="isGenerating(shot.id, req.id)"
                        @click="handleGenerateMaterial(shot, req)"
                      >
                        {{ req.status === 'success' ? '重新生成' : '生成图片' }}
                      </n-button>
                      <n-upload
                        :max="1"
                        accept=".jpg,.jpeg,.png,.webp"
                        :custom-request="(opts: any) => handleUploadMaterialForReq(shot.id, req, opts)"
                        :show-file-list="false"
                      >
                        <n-button size="tiny">上传图片</n-button>
                      </n-upload>
                    </n-space>
                  </template>
                </n-space>
              </n-gi>

              <!-- 右列：提示词 + 音频 + 视频 -->
              <n-gi :span="10">
                <!-- 提示词编辑 -->
                <n-text strong style="font-size: 13px;">视频提示词</n-text>
                <n-input
                  v-model:value="editPrompts[shot.id]!.prompt_text"
                  type="textarea"
                  :rows="3"
                  size="small"
                  placeholder="英文视频提示词"
                  style="margin-top: 4px;"
                />
                <n-text strong style="font-size: 13px; margin-top: 8px; display: block;">负面提示词</n-text>
                <n-input
                  v-model:value="editPrompts[shot.id]!.negative_prompt"
                  type="textarea"
                  :rows="2"
                  size="small"
                  placeholder="负面提示词"
                  style="margin-top: 4px;"
                />
                <n-button size="tiny" style="margin-top: 4px;" @click="handleSavePrompt(shot)">保存提示词</n-button>

                <!-- 导演视频指令 -->
                <template v-if="directorAnalysis(shot)">
                  <n-divider style="margin: 12px 0;" />
                  <n-space align="center" justify="space-between">
                    <n-text strong style="font-size: 13px;">导演视频指令</n-text>
                    <n-button size="tiny" quaternary @click="toggleParamPanel(shot.id)">
                      {{ showParamPanel[shot.id] ? '收起参数' : '编辑镜头参数' }}
                    </n-button>
                  </n-space>

                  <!-- 引用素材标签 -->
                  <n-space v-if="getReferencedMaterials(shot).length" :size="4" style="margin-top: 4px; flex-wrap: wrap;">
                    <n-tag v-for="(ref, idx) in getReferencedMaterials(shot)" :key="ref.material_id"
                      size="tiny"
                      :type="ref.generated_url ? 'success' : 'warning'"
                      :bordered="false"
                      closable
                      @close="removeReferencedMaterial(shot, idx)"
                    >
                      图片{{ ref.material_index }}: {{ ref.description }}
                    </n-tag>
                  </n-space>

                  <!-- 镜头参数面板（可折叠） -->
                  <div v-if="showParamPanel[shot.id] && creativeEdits[shot.id]" style="margin-top: 8px; padding: 8px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 6px;">
                    <n-space vertical :size="6">
                      <n-input v-model:value="creativeEdits[shot.id]!.subject" size="small" placeholder="主体描述（可含 图片n）" />
                      <n-input v-model:value="creativeEdits[shot.id]!.action" size="small" placeholder="动作描述" />
                      <n-input v-model:value="creativeEdits[shot.id]!.environment" size="small" placeholder="环境描述" />
                      <n-grid :cols="3" :x-gap="6">
                        <n-gi><n-select v-model:value="creativeEdits[shot.id]!.camera!.shot" :options="shotOptions" size="small" placeholder="景别" /></n-gi>
                        <n-gi><n-select v-model:value="creativeEdits[shot.id]!.camera!.movement" :options="movementOptions" size="small" placeholder="运镜" /></n-gi>
                        <n-gi><n-select v-model:value="creativeEdits[shot.id]!.camera!.stability" :options="stabilityOptions" size="small" placeholder="稳定" /></n-gi>
                      </n-grid>
                      <n-grid :cols="3" :x-gap="6">
                        <n-gi><n-select v-model:value="creativeEdits[shot.id]!.style" :options="styleOptions" size="small" placeholder="风格" clearable /></n-gi>
                        <n-gi><n-select v-model:value="creativeEdits[shot.id]!.lighting" :options="lightingOptions" size="small" placeholder="光照" clearable /></n-gi>
                        <n-gi>
                          <n-input-number
                            v-model:value="creativeEdits[shot.id]!.duration_suggestion"
                            :min="3" :max="15" size="small"
                            placeholder="时长(s)"
                            style="width: 100%;"
                          />
                        </n-gi>
                      </n-grid>
                      <n-select v-model:value="creativeEdits[shot.id]!.aspect_ratio" :options="ratioOptions" size="small" placeholder="画面比例" style="width: 120px;" />

                      <!-- 实时预览 -->
                      <div style="margin-top: 4px;">
                        <n-text depth="3" style="font-size: 11px;">预览 prompt：</n-text>
                        <div style="font-size: 12px; padding: 4px 6px; background: rgba(99,226,183,0.06); border-radius: 4px; margin-top: 2px; line-height: 1.5;">
                          {{ getPreviewPrompt(shot.id) }}
                        </div>
                      </div>
                      <div>
                        <n-text depth="3" style="font-size: 11px;">预览负面提示：</n-text>
                        <div style="font-size: 12px; padding: 4px 6px; background: rgba(255,255,255,0.03); border-radius: 4px; margin-top: 2px;">
                          {{ getPreviewNegative(shot.id) }}
                        </div>
                      </div>

                      <n-button size="tiny" type="primary" @click="saveCreativeData(shot)">保存镜头参数</n-button>
                    </n-space>
                  </div>

                  <!-- 提示词（高亮占位符） -->
                  <div style="margin-top: 6px; font-size: 12px; white-space: pre-wrap; line-height: 1.6; padding: 6px; background: rgba(255,255,255,0.04); border-radius: 4px;">
                    <template v-for="(seg, i) in splitPromptByPlaceholders(getVideoInstruction(shot))" :key="i">
                      <span v-if="seg.highlight" style="color: #63e2b7; font-weight: 600;">{{ seg.text }}</span>
                      <span v-else>{{ seg.text }}</span>
                    </template>
                  </div>
                  <n-button size="tiny" style="margin-top: 4px;" @click="applyDirectorPrompt(shot)">应用到提示词</n-button>
                </template>

                <!-- 音频配置 -->
                <n-divider style="margin: 12px 0;" />
                <n-text strong style="font-size: 13px;">音频配置</n-text>
                <n-space vertical :size="4" style="margin-top: 4px;">
                  <n-input
                    v-model:value="editAudios[shot.id]!.voiceover"
                    size="small"
                    placeholder="画外音文本"
                  />
                  <n-input
                    v-model:value="editAudios[shot.id]!.soundEffects"
                    size="small"
                    placeholder="音效描述（逗号分隔）"
                  />
                  <n-input
                    v-model:value="editAudios[shot.id]!.bgm"
                    size="small"
                    placeholder="背景音乐描述"
                  />
                  <n-button size="tiny" @click="handleSaveAudio(shot)">保存音频</n-button>
                </n-space>

                <!-- 视频生成 -->
                <n-divider style="margin: 12px 0;" />
                <n-text strong style="font-size: 13px;">视频生成</n-text>
                <n-space vertical :size="8" style="margin-top: 4px;">
                  <n-button
                    type="primary"
                    size="small"
                    block
                    :loading="generatingVideos.has(shot.id)"
                    :disabled="generatingVideos.has(shot.id) || shot.video_status === 'generating' || shot.video_status === 'pending' || shot.video_status === 'processing' || !shot.prompt_text"
                    @click="handleGenerateVideo(shot)"
                  >
                    {{ generatingVideos.has(shot.id) || shot.video_status === 'generating' || shot.video_status === 'pending' || shot.video_status === 'processing' ? '生成中...' : '生成视频' }}
                  </n-button>

                  <!-- 多版本视频选择器 -->
                  <template v-if="videoCandidates[shot.id] && videoCandidates[shot.id].length > 0">
                    <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                      <n-tag
                        v-for="(c, idx) in videoCandidates[shot.id]"
                        :key="c.task_id"
                        size="small"
                        :type="(selectedCandidate[shot.id] || videoCandidates[shot.id][0]?.task_id) === c.task_id ? 'primary' : 'default'"
                        :bordered="true"
                        style="cursor: pointer;"
                        @click="selectVideoCandidate(shot.id, c.task_id)"
                      >
                        v{{ idx + 1 }}
                      </n-tag>
                      <n-tag v-if="isGeneratingStatus(shot.video_status) && generatingVideos.has(shot.id)" size="tiny" type="warning" :bordered="false">
                        新版本生成中...
                      </n-tag>
                    </div>
                    <!-- 视频播放或过期提示 -->
                    <template v-if="videoExpired[shot.id]">
                      <n-alert type="warning" style="margin-top: 4px;" :show-icon="false">
                        该版本视频已过期（视频源链接失效），请点击下方按钮重新生成。
                        <n-button size="tiny" type="primary" style="margin-left: 8px;"
                          :loading="generatingVideos.has(shot.id)"
                          @click="handleGenerateVideo(shot)"
                        >重新生成视频</n-button>
                      </n-alert>
                    </template>
                    <video
                      v-else
                      :src="`/api/storyboards/${shot.id}/video-candidates/${selectedCandidate[shot.id] || videoCandidates[shot.id][0]?.task_id}/stream`"
                      controls
                      style="width: 100%; border-radius: 6px;"
                      @error="handleVideoError(shot.id)"
                    />
                    <!-- 下载按钮 -->
                    <n-space v-if="!videoExpired[shot.id]" justify="end">
                      <n-button
                        size="tiny"
                        @click="storyboardsApi.downloadVideo(
                          shot.id,
                          selectedCandidate[shot.id] || videoCandidates[shot.id][0]?.task_id
                        )"
                      >
                        下载 v{{ videoCandidates[shot.id].findIndex(c => c.task_id === (selectedCandidate[shot.id] || videoCandidates[shot.id][0]?.task_id)) + 1 }}
                      </n-button>
                    </n-space>
                  </template>

                  <!-- 旧版兼容：有 video_task_id 但无 candidates 数据 -->
                  <template v-else-if="shot.video_status === 'success' && shot.video_task_id && (!videoCandidates[shot.id] || videoCandidates[shot.id].length === 0)">
                    <template v-if="videoExpired[shot.id]">
                      <n-alert type="warning" :show-icon="false">
                        视频已过期（视频源链接失效），请重新生成。
                        <n-button size="tiny" type="primary" style="margin-left: 8px;"
                          :loading="generatingVideos.has(shot.id)"
                          @click="handleGenerateVideo(shot)"
                        >重新生成视频</n-button>
                      </n-alert>
                    </template>
                    <video v-else :src="`/api/storyboards/${shot.id}/video-candidates/${shot.video_task_id}/stream`" controls style="width: 100%; border-radius: 6px;" @error="handleVideoError(shot.id)" />
                    <n-space v-if="!videoExpired[shot.id]" justify="end">
                      <n-button size="tiny" @click="storyboardsApi.downloadVideo(shot.id, shot.video_task_id || '')">下载</n-button>
                    </n-space>
                  </template>
                  <n-text v-else-if="shot.video_status === 'failed'" type="error" style="font-size: 12px;">
                    生成失败
                    <n-button size="tiny" @click="handleGenerateVideo(shot)">重试</n-button>
                  </n-text>
                  <n-text v-else-if="isGeneratingStatus(shot.video_status)" type="warning" style="font-size: 12px;">
                    正在生成，请稍候...
                  </n-text>
                </n-space>
              </n-gi>
            </n-grid>
          </n-collapse-item>
        </n-collapse>
      </n-space>
    </n-spin>

    <!-- 图片预览 -->
    <n-modal v-model:show="showPreview" preset="card" style="max-width: 90vw; max-height: 90vh;" :bordered="true">
      <img v-if="previewImage" :src="previewImage" style="width: 100%; display: block;" />
    </n-modal>

    <!-- 批量生成弹窗 -->
    <n-modal v-model:show="showBatchDialog" preset="card" title="批量生成视频" style="max-width: 560px;" :bordered="true" :mask-closable="!batchSubmitting">
      <n-space vertical :size="12">
        <n-text>选择要生成视频的镜头（共 {{ currentShots.length }} 镜）</n-text>
        <n-space>
          <n-button size="tiny" @click="batchSelectedIds = new Set(currentShots.map(s => s.id))">全选</n-button>
          <n-button size="tiny" @click="batchSelectedIds = new Set()">取消全选</n-button>
          <n-text depth="3" style="font-size: 12px;">已选 {{ batchSelectedIds.size }} 镜</n-text>
        </n-space>
        <div style="max-height: 280px; overflow-y: auto;">
          <n-checkbox
            v-for="shot in currentShots"
            :key="shot.id"
            :checked="batchSelectedIds.has(shot.id)"
            @update:checked="(v: boolean) => { v ? batchSelectedIds.add(shot.id) : batchSelectedIds.delete(shot.id) }"
            style="display: block; margin-bottom: 6px;"
          >
            <n-space align="center" :size="4">
              <n-tag size="tiny" :bordered="false">镜{{ shot.shot_no }}</n-tag>
              <n-text style="font-size: 13px;">{{ shot.shot_type }} · {{ shot.camera_move }} · {{ shot.duration_seconds }}s</n-text>
              <n-tag v-if="shot.video_status === 'success'" size="tiny" type="success">已有视频</n-tag>
              <n-tag v-else-if="shot.video_status === 'generating' || shot.video_status === 'pending' || shot.video_status === 'processing'" size="tiny" type="warning">生成中</n-tag>
              <n-tag v-else-if="!shot.prompt_text" size="tiny" type="default">无提示词</n-tag>
            </n-space>
          </n-checkbox>
        </div>
        <n-divider style="margin: 4px 0;" />
        <n-text strong style="font-size: 13px;">并发数: {{ batchConcurrency }}</n-text>
        <n-slider v-model:value="batchConcurrency" :min="1" :max="5" :step="1" :marks="{ 1: '1', 2: '2', 3: '3', 4: '4', 5: '5' }" />
        <n-text depth="3" style="font-size: 11px;">建议设置 2-3，过高可能触发 API 限流</n-text>

        <!-- 进度面板 -->
        <template v-if="batchProgress.size > 0">
          <n-divider style="margin: 4px 0;" />
          <n-text strong style="font-size: 13px;">生成进度</n-text>
          <div style="max-height: 200px; overflow-y: auto;">
            <div v-for="[sid, prog] in batchProgress" :key="sid" style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 12px;">
              <n-tag size="tiny" :bordered="false">{{ shotLabel(sid) }}</n-tag>
              <n-tag v-if="prog === 'generating'" size="tiny" type="warning">生成中</n-tag>
              <n-tag v-else-if="prog === 'success'" size="tiny" type="success">完成</n-tag>
              <n-tag v-else-if="prog === 'failed'" size="tiny" type="error">失败</n-tag>
              <n-tag v-else size="tiny" type="default">{{ prog }}</n-tag>
            </div>
          </div>
        </template>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showBatchDialog = false" :disabled="batchSubmitting">取消</n-button>
          <n-button type="primary" @click="submitBatch" :loading="batchSubmitting" :disabled="batchSelectedIds.size === 0">
            开始生成 ({{ batchSelectedIds.size }})
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  NButton, NButtonGroup, NCheckbox, NCollapse, NCollapseItem, NDescriptions, NDescriptionsItem,
  NDivider, NEmpty, NGi, NGrid, NInput, NInputNumber, NModal, NPopover, NSelect, NSlider, NSpace, NSpin, NTag, NText, NUpload, useMessage,
} from 'naive-ui'
import type { UploadSettledFileInfo } from 'naive-ui'
import { storyboardsApi, type StoryboardResponse, type AudioConfig, type VideoCandidate, referenceApi, type ReferenceableItem } from '../api/storyboards'
import {
  assemblePrompt, type CreativeData,
  SHOT_TYPES, CAMERA_MOVEMENTS, STABILITY, STYLES, LIGHTING, ASPECT_RATIOS,
} from '../utils/promptAssembler'

interface MaterialRequirement {
  id: string
  type: string
  name: string
  description: string
  reason: string
  prompt: string
  status: string
  generated_url: string | null
  necessity?: string
  material_index?: number | null
}

const props = defineProps<{ projectId: string }>()
const emit = defineEmits<{ (e: 'update'): void }>()
const message = useMessage()

const loading = ref(false)
const storyboards = ref<StoryboardResponse[]>([])
const currentEpisode = ref(1)
const directoring = ref<string | null>(null)
const generatingVideos = ref(new Set<string>())
const videoCandidates = ref<Record<string, VideoCandidate[]>>({})
const selectedCandidate = ref<Record<string, string>>({})
const videoExpired = reactive<Record<string, boolean>>({})
const generatingMaterials = ref(new Set<string>())
const previewImage = ref<string | null>(null)
const showPreview = computed({
  get: () => !!previewImage.value,
  set: (v: boolean) => { if (!v) previewImage.value = null },
})

// 编辑态
const editPrompts = reactive<Record<string, { prompt_text: string; negative_prompt: string }>>({})
const editAudios = reactive<Record<string, { voiceover: string; soundEffects: string; bgm: string }>>({})
const materialPrompts = reactive<Record<string, Record<string, string>>>({})

// creative_data 编辑态
const creativeEdits = reactive<Record<string, CreativeData>>({})
const showParamPanel = reactive<Record<string, boolean>>({})

// 选择器选项（从词汇表生成）
const shotOptions = Object.keys(SHOT_TYPES).map(k => ({ label: k, value: k }))
const movementOptions = Object.keys(CAMERA_MOVEMENTS).map(k => ({ label: k, value: k }))
const stabilityOptions = Object.keys(STABILITY).map(k => ({ label: k, value: k }))
const styleOptions = Object.keys(STYLES).map(k => ({ label: k, value: k }))
const lightingOptions = Object.keys(LIGHTING).map(k => ({ label: k, value: k }))
const ratioOptions = ASPECT_RATIOS.map(r => ({ label: r, value: r }))

// 轮询定时器
const pollTimers = new Map<string, ReturnType<typeof setInterval>>()

// 批量生成状态
const showBatchDialog = ref(false)
const batchSelectedIds = ref(new Set<string>())
const batchConcurrency = ref(3)
const batchSubmitting = ref(false)
const batchProgress = ref(new Map<string, string>())
let batchPollTimer: ReturnType<typeof setInterval> | null = null

// 按集分组
const episodes = computed(() => {
  const map = new Map<number, StoryboardResponse[]>()
  for (const sb of storyboards.value) {
    const list = map.get(sb.episode_no) || []
    list.push(sb)
    map.set(sb.episode_no, list)
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => a - b)
    .map(([episode_no, shots]) => ({ episode_no, shots }))
})

const currentShots = computed(() => {
  const ep = episodes.value.find(e => e.episode_no === currentEpisode.value)
  return ep?.shots || []
})

// 初始化编辑态 — 始终从服务器数据刷新
function initEditState(shots: StoryboardResponse[]) {
  for (const shot of shots) {
    // prompt 编辑态始终从服务器数据同步（覆盖本地缓存）
    editPrompts[shot.id] = {
      prompt_text: shot.prompt_text || '',
      negative_prompt: shot.negative_prompt || '',
    }
    // 音频编辑态 — 始终从服务器数据同步
    const ac = shot.audio_config as AudioConfig | null
    editAudios[shot.id] = {
      voiceover: ac?.voiceover || '',
      soundEffects: ac?.sound_effects?.join(', ') || '',
      bgm: ac?.bgm || '',
    }
    // 初始化素材提示词编辑态
    const analysis = (shot.director_analysis as Record<string, unknown>) || null
    if (analysis) {
      const reqs = (analysis.material_requirements || []) as MaterialRequirement[]
      if (!materialPrompts[shot.id]) materialPrompts[shot.id] = {}
      for (const req of reqs) {
        // 素材提示词始终从服务器数据同步
        materialPrompts[shot.id][req.id] = req.prompt || ''
      }
      // 初始化 creative_data 编辑态
      if (!creativeEdits[shot.id]) {
        const cd = analysis.creative_data as CreativeData | undefined
        creativeEdits[shot.id] = cd ? { ...cd, camera: { ...cd.camera } } : {
          subject: '', action: '', environment: '',
          camera: { shot: '中景', movement: '固定', stability: '三脚架' },
          style: '电影感', lighting: '', dialogue: '', duration_suggestion: 5,
          aspect_ratio: '9:16',
        }
        showParamPanel[shot.id] = false
      }
    }
  }
}

async function fetchStoryboards() {
  if (!props.projectId) return
  loading.value = true
  try {
    const resp = await storyboardsApi.list(undefined, props.projectId)
    storyboards.value = resp.data
    initEditState(resp.data)
    for (const sb of resp.data) {
      // 只对有 video_task_id 且状态为 generating 的进行轮询
      if (sb.video_task_id && isGeneratingStatus(sb.video_status)) startPolling(sb.id, true)
      // 只要有过视频生成记录就加载候选列表
      if (sb.video_task_id || sb.video_status === 'success') fetchVideoCandidates(sb.id)
    }
  } catch {
    message.error('加载分镜数据失败')
  } finally {
    loading.value = false
  }
}

function switchEpisode(ep: number) {
  currentEpisode.value = ep
}

// 智能导演
function directorAnalysis(shot: StoryboardResponse): Record<string, unknown> | null {
  return (shot.director_analysis as Record<string, unknown>) || null
}

async function handleDirector(shot: StoryboardResponse) {
  directoring.value = shot.id
  try {
    await storyboardsApi.directorPlan(shot.id, !!directorAnalysis(shot))
    const freshResp = await storyboardsApi.getById(shot.id)
    updateShotInList(freshResp.data)
    initEditState([freshResp.data])
    message.success('智能导演分析完成')
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '导演分析失败'
    message.error(detail)
  } finally {
    directoring.value = null
  }
}

function applyDirectorPrompt(shot: StoryboardResponse) {
  const analysis = directorAnalysis(shot)
  if (!analysis) return
  const vi = analysis.video_instruction as Record<string, string> | undefined
  if (editPrompts[shot.id] && vi) {
    editPrompts[shot.id].prompt_text = vi.prompt || ''
    editPrompts[shot.id].negative_prompt = vi.negative_prompt || ''
  }
  message.success('视频指令已应用到提示词')
}

function getVideoInstruction(shot: StoryboardResponse): string {
  const analysis = directorAnalysis(shot)
  if (!analysis) return ''
  const vi = analysis.video_instruction as Record<string, unknown> | undefined
  return (vi?.prompt as string) || ''
}

interface ImageRef {
  material_id: string
  material_index: number
  description: string
  generated_url: string | null
  status: string
}

function getReferencedMaterials(shot: StoryboardResponse): ImageRef[] {
  const analysis = directorAnalysis(shot)
  if (!analysis) return []
  const vi = analysis.video_instruction as Record<string, unknown> | undefined
  const images = (vi?.images || []) as Array<{ material_id: string; material_index: number; description: string }>
  if (!images.length) return []
  const reqs = getMaterialRequirements(shot)
  const reqMap = new Map(reqs.map(r => [r.id, r]))
  return images.map(img => ({
    ...img,
    generated_url: reqMap.get(img.material_id)?.generated_url || null,
    status: reqMap.get(img.material_id)?.status || 'pending',
  }))
}

function splitPromptByPlaceholders(prompt: string): Array<{ text: string; highlight: boolean }> {
  if (!prompt) return []
  const parts: Array<{ text: string; highlight: boolean }> = []
  const regex = /图片\d+/g
  let last = 0
  let m: RegExpExecArray | null
  while ((m = regex.exec(prompt)) !== null) {
    if (m.index > last) parts.push({ text: prompt.slice(last, m.index), highlight: false })
    parts.push({ text: m[0], highlight: true })
    last = regex.lastIndex
  }
  if (last < prompt.length) parts.push({ text: prompt.slice(last), highlight: false })
  return parts
}

async function removeReferencedMaterial(shot: StoryboardResponse, removeIdx: number) {
  const analysis = directorAnalysis(shot)
  if (!analysis) return
  const vi = analysis.video_instruction as Record<string, unknown>
  const images = [...((vi?.images || []) as Array<{ material_id: string; material_index: number; description: string }>)]
  if (removeIdx < 0 || removeIdx >= images.length) return

  const removed = images.splice(removeIdx, 1)[0]
  const removedIndex = removed.material_index

  // 重新分配 material_index
  images.forEach((img, i) => { img.material_index = i + 1 })

  // 更新 prompt 中的占位符：从大序号往小序号替换，避免冲突
  let prompt = (vi.prompt as string) || ''
  const reindexMap = new Map<number, number>()
  for (const img of (vi.images as Array<{ material_index: number }>)) {
    if (img.material_index > removedIndex) {
      reindexMap.set(img.material_index, img.material_index - 1)
    }
  }
  const sortedOld = [...reindexMap.keys()].sort((a, b) => b - a)
  for (const oldIdx of sortedOld) {
    prompt = prompt.replace(new RegExp(`图片${oldIdx}(?![0-9])`, 'g'), `图片${oldIdx - 1}`)
  }
  // 移除被删除素材的引用（图片N）
  prompt = prompt.replace(new RegExp(`图片${removedIndex}(?![0-9])`, 'g'), '')

  // 构建新 analysis
  const newAnalysis = { ...analysis, video_instruction: { ...vi, images, prompt } }

  try {
    const resp = await storyboardsApi.updateDirectorAnalysis(shot.id, newAnalysis)
    updateShotInList(resp.data)
    initEditState([resp.data])
    message.success(`已移除引用: ${removed.description}`)
  } catch {
    message.error('移除引用失败')
  }
}

// ── 镜头参数面板：实时预览 + 保存 ──
function getPreviewPrompt(shotId: string): string {
  const cd = creativeEdits[shotId]
  if (!cd) return ''
  return assemblePrompt(cd).prompt
}

function getPreviewNegative(shotId: string): string {
  const cd = creativeEdits[shotId]
  if (!cd) return ''
  return assemblePrompt(cd).negativePrompt
}

function toggleParamPanel(shotId: string) {
  showParamPanel[shotId] = !showParamPanel[shotId]
}

async function saveCreativeData(shot: StoryboardResponse) {
  const cd = creativeEdits[shot.id]
  if (!cd) return
  const analysis = directorAnalysis(shot)
  if (!analysis) return

  const assembled = assemblePrompt(cd)
  const vi = { ...(analysis.video_instruction as Record<string, unknown>) }
  vi.prompt = assembled.prompt
  vi.negative_prompt = assembled.negativePrompt
  vi.duration = cd.duration_suggestion || 5
  vi.aspect_ratio = cd.aspect_ratio || '9:16'

  const newAnalysis = { ...analysis, creative_data: cd, video_instruction: vi }

  try {
    const resp = await storyboardsApi.updateDirectorAnalysis(shot.id, newAnalysis)
    updateShotInList(resp.data)
    initEditState([resp.data])
    message.success('镜头参数已保存')
  } catch {
    message.error('保存镜头参数失败')
  }
}

function getMaterialRequirements(shot: StoryboardResponse): MaterialRequirement[] {
  const analysis = directorAnalysis(shot)
  if (!analysis) return []
  const reqs = analysis.material_requirements
  if (!Array.isArray(reqs)) return []
  return reqs as MaterialRequirement[]
}

// 素材提示词编辑
function getMaterialPrompt(shotId: string, reqId: string): string {
  return materialPrompts[shotId]?.[reqId] || ''
}

function setMaterialPrompt(shotId: string, reqId: string, value: string) {
  if (!materialPrompts[shotId]) materialPrompts[shotId] = {}
  materialPrompts[shotId][reqId] = value
}

function isGenerating(shotId: string, reqId: string): boolean {
  return generatingMaterials.value.has(`${shotId}:${reqId}`)
}

// 类型标签
function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    background: '背景', prop: '道具', vfx: '特效',
    character_expression: '角色',
  }
  return labels[type] || type
}

function getTypeColor(type: string): 'success' | 'warning' | 'info' | 'error' | 'default' {
  const colors: Record<string, 'success' | 'warning' | 'info' | 'error' | 'default'> = {
    background: 'success', prop: 'warning', vfx: 'error', character_expression: 'info',
  }
  return colors[type] || 'default'
}

// 生成单个素材图片
async function handleGenerateMaterial(shot: StoryboardResponse, req: MaterialRequirement) {
  const key = `${shot.id}:${req.id}`
  generatingMaterials.value.add(key)
  try {
    const prompt = getMaterialPrompt(shot.id, req.id)
    const resp = await storyboardsApi.generateMaterial(shot.id, req.id, prompt)
    updateShotInList(resp.data)
    initEditState([resp.data])
    message.success(`素材"${req.name}"生成完成`)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败'
    message.error(detail)
  } finally {
    generatingMaterials.value.delete(key)
  }
}

// 上传素材（关联到指定素材需求）
async function handleUploadMaterialForReq(
  shotId: string,
  req: MaterialRequirement,
  { file }: { file: UploadSettledFileInfo },
) {
  try {
    const resp = await storyboardsApi.uploadMaterial(shotId, file.file as File, req.type, req.id)
    updateShotInList(resp.data)
    initEditState([resp.data])
    message.success(`素材"${req.name}"上传成功`)
  } catch {
    message.error('素材上传失败')
  }
}

// 保存提示词
async function handleSavePrompt(shot: StoryboardResponse) {
  const ep = editPrompts[shot.id]
  if (!ep) return
  try {
    const resp = await storyboardsApi.update(shot.id, {
      prompt_text: ep.prompt_text || null,
      negative_prompt: ep.negative_prompt || null,
    })
    updateShotInList(resp.data)
    message.success('提示词已保存')
    emit('update')
  } catch {
    message.error('保存失败')
  }
}

// 保存音频配置
async function handleSaveAudio(shot: StoryboardResponse) {
  const ea = editAudios[shot.id]
  if (!ea) return
  const audioConfig: AudioConfig = {
    voiceover: ea.voiceover || undefined,
    sound_effects: ea.soundEffects ? ea.soundEffects.split(/[,，]/).map(s => s.trim()).filter(Boolean) : undefined,
    bgm: ea.bgm || undefined,
  }
  try {
    const resp = await storyboardsApi.updateAudioConfig(shot.id, audioConfig)
    updateShotInList(resp.data)
    message.success('音频配置已保存')
  } catch {
    message.error('保存失败')
  }
}

// 生成视频
async function handleGenerateVideo(shot: StoryboardResponse) {
  generatingVideos.value.add(shot.id)
  try {
    const resp = await storyboardsApi.generateVideo(shot.id)
    updateShotField(shot.id, 'video_status', 'generating')
    updateShotField(shot.id, 'video_task_id', resp.data.task_id)
    message.info('视频生成任务已提交')
    startPolling(shot.id)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '视频生成失败'
    message.error(detail)
    updateShotField(shot.id, 'video_status', 'failed')
  } finally {
    generatingVideos.value.delete(shot.id)
  }
}

async function fetchVideoCandidates(shotId: string) {
  try {
    const resp = await storyboardsApi.getVideoCandidates(shotId)
    videoCandidates.value[shotId] = resp.data
    // 默认选中最新版本（第一个）
    if (resp.data.length > 0 && !selectedCandidate.value[shotId]) {
      selectedCandidate.value[shotId] = resp.data[0].task_id
    }
  } catch (err: unknown) {
    console.error(`[VideoCandidates] 获取候选视频失败 shot=${shotId}:`, err)
  }
}

// 停止单个镜头轮询
function stopPolling(shotId: string) {
  const existing = pollTimers.get(shotId)
  if (existing != null) {
    clearInterval(existing)
    pollTimers.delete(shotId)
  }
}

// 轮询视频状态
function startPolling(shotId: string, silent = false) {
  stopPolling(shotId)  // 先清除旧轮询，防止重复注册
  const timer = setInterval(async () => {
    try {
      const resp = await storyboardsApi.getVideoStatus(shotId)
      const { status, video_url } = resp.data
      updateShotField(shotId, 'video_status', status)
      if (video_url) updateShotField(shotId, 'video_url', video_url)
      if (status === 'success' || status === 'failed') {
        stopPolling(shotId)
        if (status === 'success') {
          if (!silent) message.success(`镜头视频生成成功`)
          fetchVideoCandidates(shotId)
        }
        else if (!silent) message.error('镜头视频生成失败')
      }
    } catch {
      stopPolling(shotId)
    }
  }, 3000)
  pollTimers.set(shotId, timer)
}

// 工具函数
function updateShotInList(updated: StoryboardResponse) {
  const idx = storyboards.value.findIndex(s => s.id === updated.id)
  if (idx >= 0) storyboards.value[idx] = updated
}

function updateShotField(shotId: string, field: string, value: unknown) {
  const shot = storyboards.value.find(s => s.id === shotId)
  if (shot) (shot as Record<string, unknown>)[field] = value
}

function getFullUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `http://localhost:8000${path}`
}

function isGeneratingStatus(status: string | undefined): boolean {
  return status === 'generating' || status === 'pending' || status === 'processing'
}

function handleVideoError(shotId: string): void {
  videoExpired[shotId] = true
}

function selectVideoCandidate(shotId: string, taskId: string): void {
  selectedCandidate.value[shotId] = taskId
  videoExpired[shotId] = false
}

// 引用下拉
const activeRefDrop = ref('')
const _savedCursor: Record<string, { start: number; end: number }> = {}
const refData = ref<{
  characters: ReferenceableItem[]
  scenes: ReferenceableItem[]
  props: ReferenceableItem[]
  generated_materials: ReferenceableItem[]
}>({ characters: [], scenes: [], props: [], generated_materials: [] })
const promptInputRefs = reactive<Record<string, Record<string, any>>>({})

const refGroups = computed(() => {
  const groups: Array<{ key: string; label: string; items: ReferenceableItem[] }> = []
  const d = refData.value
  if (d.characters.length) {
    groups.push({ key: 'char', label: '角色', items: d.characters })
  }
  if (d.scenes.length) {
    groups.push({ key: 'scene', label: '场景', items: d.scenes })
  }
  if (d.props.length) {
    groups.push({ key: 'prop', label: '道具', items: d.props })
  }
  if (d.generated_materials.length) {
    groups.push({ key: 'mat', label: '已生成素材', items: d.generated_materials })
  }
  return groups
})

async function loadRefOptions() {
  if (refData.value.characters.length || refData.value.scenes.length) return
  try {
    const resp = await referenceApi.list(props.projectId)
    refData.value = resp.data
  } catch { /* 静默 */ }
}

function setPromptInputRef(shotId: string, reqId: string, el: any) {
  if (!el) return
  if (!promptInputRefs[shotId]) promptInputRefs[shotId] = {}
  promptInputRefs[shotId][reqId] = el
}

function saveCursorPos(shotId: string, reqId: string) {
  const inputComp = promptInputRefs[shotId]?.[reqId]
  const textarea: HTMLTextAreaElement | null = inputComp?.$el?.querySelector('textarea') ?? inputComp?.$el
  if (textarea) {
    _savedCursor[`${shotId}:${reqId}`] = { start: textarea.selectionStart, end: textarea.selectionEnd }
  }
}

function insertRef(shotId: string, reqId: string, mark: string) {
  const insert = `${mark} `
  const current = getMaterialPrompt(shotId, reqId) || ''
  const saved = _savedCursor[`${shotId}:${reqId}`]
  const start = saved?.start ?? current.length
  const end = saved?.end ?? current.length
  const before = current.substring(0, start)
  const after = current.substring(end)
  const needSpace = before.length > 0 && !before.endsWith(' ')
  const newText = before + (needSpace ? ' ' : '') + insert + after
  setMaterialPrompt(shotId, reqId, newText)
  const cursorPos = start + (needSpace ? 1 : 0) + insert.length
  const inputComp = promptInputRefs[shotId]?.[reqId]
  const textarea: HTMLTextAreaElement | null = inputComp?.$el?.querySelector('textarea') ?? inputComp?.$el
  nextTick(() => {
    if (textarea) {
      textarea.focus()
      textarea.setSelectionRange(cursorPos, cursorPos)
    }
    delete _savedCursor[`${shotId}:${reqId}`]
  })
  activeRefDrop.value = ''
}

// 批量生成 —— 弹窗控制
function openBatchDialog() {
  batchSelectedIds.value = new Set(currentShots.value.map(s => s.id))
  batchProgress.value = new Map()
  showBatchDialog.value = true
}

function shotLabel(sid: string): string {
  const s = storyboards.value.find(x => x.id === sid)
  return s ? `第${s.episode_no}集第${s.shot_no}镜` : sid.slice(0, 8)
}

// 批量生成 —— 提交 + 轮询
async function submitBatch() {
  if (batchSelectedIds.value.size === 0) return
  batchSubmitting.value = true
  const ids = Array.from(batchSelectedIds.value)
  // 初始化进度
  const progress = new Map<string, string>()
  for (const id of ids) progress.set(id, '等待中')
  batchProgress.value = progress

  try {
    const resp = await storyboardsApi.batchGenerate(ids, batchConcurrency.value)
    for (const r of resp.data) {
      progress.set(r.storyboard_id, r.status === 'generating' || r.status === 'success' ? 'generating' : 'failed')
      if (r.task_id) {
        updateShotField(r.storyboard_id, 'video_status', 'generating')
        updateShotField(r.storyboard_id, 'video_task_id', r.task_id)
      }
    }
    batchProgress.value = new Map(progress)
    // 启动批量轮询
    startBatchPolling(ids)
    message.success(`已提交 ${resp.data.filter(r => r.status === 'generating').length} 个视频任务`)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '批量提交失败'
    message.error(detail)
  } finally {
    batchSubmitting.value = false
  }
}

function startBatchPolling(ids: string[]) {
  stopBatchPolling()
  batchPollTimer = setInterval(async () => {
    try {
      const resp = await storyboardsApi.batchStatus(ids)
      let doneCount = 0
      const progress = new Map(batchProgress.value)
      for (const item of resp.data) {
        const sid = item.storyboard_id
        if (item.video_status === 'success' || item.task_status === 'success') {
          progress.set(sid, 'success')
          updateShotField(sid, 'video_status', 'success')
          if (item.video_url) updateShotField(sid, 'video_url', item.video_url)
          fetchVideoCandidates(sid)
          doneCount++
        } else if (item.video_status === 'failed' || item.task_status === 'failed') {
          progress.set(sid, 'failed')
          updateShotField(sid, 'video_status', 'failed')
          doneCount++
        } else if (item.video_status === 'generating' || item.task_status === 'processing' || item.task_status === 'pending') {
          progress.set(sid, 'generating')
          updateShotField(sid, 'video_status', 'generating')
        }
      }
      batchProgress.value = new Map(progress)
      if (doneCount >= ids.length) stopBatchPolling()
    } catch {
      // 轮询失败不中断
    }
  }, 3000)
}

function stopBatchPolling() {
  if (batchPollTimer) {
    clearInterval(batchPollTimer)
    batchPollTimer = null
  }
}

onMounted(fetchStoryboards)

onUnmounted(() => {
  for (const timer of pollTimers.values()) {
    clearInterval(timer)
  }
  pollTimers.clear()
  stopBatchPolling()
})
</script>

<style scoped>
.lens-production { padding: 0 4px; }

.material-preview {
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #3a3a4a;
  max-width: 160px;
  cursor: pointer;
}

.material-preview img {
  width: 100%;
  max-height: 80px;
  object-fit: cover;
  display: block;
  transition: opacity 0.2s;
}

.material-preview img:hover {
  opacity: 0.85;
}

/* 引用面板 */
.ref-panel { padding: 4px 0; }
.ref-group-header {
  font-weight: 600;
  font-size: 13px;
  color: #e0e0e0;
  padding: 6px 8px 4px;
  border-bottom: 1px solid #3a3a4a;
  margin-bottom: 4px;
}
.ref-grid {
  display: grid;
  gap: 2px 8px;
  padding: 0 4px 8px;
}
.ref-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 13px;
  transition: background 0.15s;
}
.ref-item:hover { background: rgba(255,255,255,0.08); }
.ref-thumb {
  width: 24px;
  height: 24px;
  object-fit: cover;
  border-radius: 3px;
  flex-shrink: 0;
}
</style>
