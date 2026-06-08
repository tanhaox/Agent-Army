<template>
  <div class="project-workspace">
    <n-spin :show="loading">
      <template v-if="project">
        <!-- 顶部信息栏 -->
        <n-page-header @back="router.push('/projects')">
          <template #title>
            {{ project.name }}
            <n-tag :type="statusTagType" size="small" style="margin-left: 8px;">{{ statusText }}</n-tag>
          </template>
          <template #extra>
            <n-space>
              <n-button size="small" @click="showEditModal = true">编辑信息</n-button>
              <n-button type="primary" size="small" @click="handleCreateSnapshot">创建快照</n-button>
            </n-space>
          </template>
        </n-page-header>
        <n-text depth="3" style="margin-top: 4px; display: block;">{{ project.description || '暂无描述' }}</n-text>

        <!-- 统计卡片 -->
        <n-grid :cols="4" :x-gap="12" style="margin-top: 16px;">
          <n-gi>
            <n-card size="small"><n-statistic label="剧本" :value="dashboard.script_count" /></n-card>
          </n-gi>
          <n-gi>
            <n-card size="small"><n-statistic label="分镜" :value="dashboard.storyboard_count" /></n-card>
          </n-gi>
          <n-gi>
            <n-card size="small"><n-statistic label="角色" :value="dashboard.character_count" /></n-card>
          </n-gi>
          <n-gi>
            <n-card size="small"><n-statistic label="视频任务" :value="dashboard.video_task_count" /></n-card>
          </n-gi>
        </n-grid>

        <!-- 工作区标签页 -->
        <n-tabs type="line" style="margin-top: 20px;" v-model:value="activeTab">
          <!-- Tab 1: 剧本 -->
          <n-tab-pane name="script" tab="剧本">
            <n-tabs type="segment" v-model:value="scriptSubTab">
              <!-- 子 Tab: 创作 -->
              <n-tab-pane name="create" tab="创作">
            <n-spin :show="loadingScript">
              <template v-if="currentScript">
                <n-card size="small" style="margin-bottom: 12px;">
                  <n-space align="center" justify="space-between">
                    <n-space align="center">
                      <n-h3 style="margin: 0;">{{ currentScript.content?.title || currentScript.project_name }}</n-h3>
                      <n-tag type="info" size="small">{{ currentScript.content?.total_episodes || 0 }} 集</n-tag>
                    </n-space>
                    <n-space>
                      <n-text depth="3" style="font-size: 13px;">{{ formatDate(currentScript.created_at) }}</n-text>
                      <n-button v-if="!editingScript" size="small" @click="enterScriptEditMode">编辑剧本</n-button>
                      <template v-else>
                        <n-button size="small" type="primary" :loading="savingScript" @click="handleSaveScript">保存</n-button>
                        <n-button size="small" @click="cancelScriptEdit">取消</n-button>
                      </template>
                    </n-space>
                  </n-space>
                </n-card>

                <!-- 只读模式 -->
                <n-collapse v-if="!editingScript && currentScript.content?.episodes">
                  <n-collapse-item
                    v-for="ep in currentScript.content.episodes"
                    :key="ep.episode"
                    :title="`第 ${ep.episode} 集 - ${ep.hook}`"
                    :name="ep.episode"
                  >
                    <n-grid :cols="1" :y-gap="8">
                      <n-gi v-for="(scene, idx) in ep.scenes" :key="idx">
                        <n-card size="small" embedded>
                          <n-space align="center" :size="8">
                            <n-tag size="small" :bordered="false">{{ scene.shot_type }}</n-tag>
                            <n-tag size="small" :bordered="false" type="info">{{ scene.emotion }}</n-tag>
                          </n-space>
                          <n-text style="margin-top: 8px; display: block;">{{ scene.action }}</n-text>
                          <n-text v-if="scene.dialogue" type="primary" style="margin-top: 4px; display: block; font-style: italic;">
                            "{{ scene.dialogue }}"
                          </n-text>
                        </n-card>
                      </n-gi>
                    </n-grid>
                    <n-divider style="margin: 4px 0;" />
                    <n-text depth="3" style="font-size: 13px;">结尾悬念:</n-text>
                    <n-tag type="warning" size="small" style="margin-left: 4px;">{{ ep.cliffhanger }}</n-tag>
                  </n-collapse-item>
                </n-collapse>

                <!-- 编辑模式 -->
                <template v-if="editingScript && editScriptContent?.episodes">
                  <n-card v-for="(ep, _epIdx) in editScriptContent.episodes" :key="ep.episode" size="small" style="margin-bottom: 12px;">
                    <template #header>第 {{ ep.episode }} 集</template>
                    <n-space vertical>
                      <n-form-item label="开篇钩子" label-placement="left">
                        <n-input v-model:value="ep.hook" />
                      </n-form-item>
                      <n-card v-for="(scene, scIdx) in ep.scenes" :key="scIdx" size="small" embedded style="margin-bottom: 8px;">
                        <n-grid :cols="2" :x-gap="12">
                          <n-gi>
                            <n-form-item label="景别">
                              <n-select v-model:value="scene.shot_type" :options="shotTypeOptions" />
                            </n-form-item>
                          </n-gi>
                          <n-gi>
                            <n-form-item label="情绪">
                              <n-select v-model:value="scene.emotion" :options="emotionOptions" />
                            </n-form-item>
                          </n-gi>
                        </n-grid>
                        <n-form-item label="动作描述">
                          <n-input v-model:value="scene.action" type="textarea" :rows="2" />
                        </n-form-item>
                        <n-form-item label="对话">
                          <n-input v-model:value="scene.dialogue" />
                        </n-form-item>
                      </n-card>
                      <n-form-item label="结尾悬念">
                        <n-input v-model:value="ep.cliffhanger" />
                      </n-form-item>
                    </n-space>
                  </n-card>
                </template>
              </template>
              <template v-else>
                <!-- 叙事树剧本创作流程 -->
                <n-space vertical size="large">
                  <!-- 步骤1: 生成叙事树 -->
                    <n-card title="步骤一：构建叙事树" size="small">
                      <n-space vertical>
                        <n-text depth="3">输入创意主题，AI 将生成分支叙事树，你可以选择感兴趣的方向。</n-text>
                        <n-input
                          v-model:value="treeTheme"
                          type="textarea"
                          :rows="2"
                          placeholder="描述你想要的短剧故事核心冲突..."
                          :disabled="generatingTree"
                        />
                        <n-button
                          type="primary"
                          :loading="generatingTree"
                          @click="handleGenerateTree"
                        >{{ generatingTree ? 'AI 正在发散创意...' : '生成叙事树' }}</n-button>
                      </n-space>
                    </n-card>

                    <!-- 步骤2: 展示叙事树并选择分支 -->
                    <n-card v-if="narrativeTree?.tree_data?.root" title="步骤二：选择故事主线" size="small">
                      <n-text depth="3" style="margin-bottom: 12px; display: block;">
                        勾选节点选择路径，评分越高爆款潜力越大。选好后确认主线。
                      </n-text>
                      <n-divider style="margin: 8px 0;" />
                      <!-- 递归渲染树节点 -->
                      <div class="narrative-tree">
                        <template v-for="item in flattenNodes(narrativeTree.tree_data.root)" :key="item.node.id">
                          <div :style="{ paddingLeft: (item.depth * 28) + 'px', marginBottom: '8px' }">
                            <n-space align="center" :size="6" :wrap="false">
                              <n-checkbox
                                :checked="isBranchSelected(item.node.id)"
                                @update:checked="() => toggleBranch(item.node.id)"
                              />
                              <n-tag
                                v-if="item.node.type === 'root'"
                                type="info" size="small" :bordered="false"
                              >核心冲突</n-tag>
                              <!-- 评分徽章 -->
                              <n-tag
                                v-if="item.node.score != null"
                                :type="item.node.score >= 8 ? 'success' : item.node.score >= 5 ? 'warning' : 'error'"
                                size="small"
                                round
                              >{{ item.node.score }}分</n-tag>
                              <n-text
                                :type="isBranchSelected(item.node.id) ? 'primary' : 'default'"
                                :strong="isBranchSelected(item.node.id)"
                              >{{ item.node.text }}</n-text>
                            </n-space>
                            <!-- 标签行 -->
                            <n-space
                              v-if="(item.node.tags || []).length > 0"
                              :size="4"
                              :style="{ paddingLeft: '32px', marginTop: '2px' }"
                              :wrap="true"
                            >
                              <n-tag
                                v-for="tag in (item.node.tags || [])"
                                :key="tag"
                                :type="(tagColor(tag) as any)"
                                size="tiny"
                                :bordered="false"
                                round
                              >{{ tag }}</n-tag>
                            </n-space>
                            <!-- 优缺点 -->
                            <div
                              v-if="item.node.pros || item.node.cons"
                              style="padding-left: 32px; margin-top: 2px;"
                            >
                              <n-text v-if="item.node.pros" type="success" style="font-size: 12px;">+ {{ item.node.pros }}</n-text>
                              <n-text v-if="item.node.cons" type="error" style="font-size: 12px; margin-left: 8px;">- {{ item.node.cons }}</n-text>
                            </div>
                            <!-- 扩展按钮 -->
                            <div style="padding-left: 32px; margin-top: 4px;">
                              <n-button
                                size="tiny"
                                quaternary
                                type="info"
                                :loading="expandingNodeId === item.node.id"
                                @click="handleExpandNode(item.node.id)"
                              >
                                + 更多分支
                              </n-button>
                            </div>
                          </div>
                        </template>
                      </div>
                      <n-divider style="margin: 12px 0;" />
                      <n-space>
                        <n-text depth="3">已选择 {{ selectedBranchIds.length }} 个节点</n-text>
                        <n-button
                          type="warning"
                          :loading="generatingOutlines"
                          :disabled="selectedBranchIds.length < 2"
                          @click="handleGenerateOutlines"
                        >{{ generatingOutlines ? 'AI 正在创作概要（约 1-3 分钟）...' : '生成剧情概要' }}</n-button>
                      </n-space>
                    </n-card>

                    <!-- 步骤3: 多版本概要选择 -->
                    <n-spin :show="generatingOutlines">
                      <template v-if="outlines.length > 0">
                        <n-card title="步骤三：选择剧情版本" size="small">
                          <n-text depth="3" style="margin-bottom: 12px; display: block;">
                            AI 根据你选的主线生成了 {{ outlines.length }} 个版本的剧情概要，选择一个最喜欢的。
                          </n-text>
                          <n-grid :cols="1" :y-gap="12">
                            <n-gi v-for="o in outlines" :key="o.version">
                              <n-card
                                size="small"
                                :style="{
                                  border: selectedOutline?.version === o.version ? '2px solid #2080f0' : '1px solid #e0e0e6',
                                  cursor: 'pointer',
                                }"
                                @click="handleSelectOutline(o)"
                              >
                                <template #header>
                                  <n-space align="center" :size="8">
                                    <n-tag
                                      :type="(OUTLINE_VERSION_COLORS[o.version] || 'default') as any"
                                      size="small"
                                      round
                                    >{{ o.version }}</n-tag>
                                    <n-text strong>{{ o.style }}</n-text>
                                  </n-space>
                                </template>
                                <n-text style="white-space: pre-wrap; line-height: 1.7;">{{ o.text }}</n-text>
                                <template #action>
                                  <n-button
                                    size="small"
                                    :type="selectedOutline?.version === o.version ? 'primary' : 'default'"
                                    @click.stop="handleSelectOutline(o)"
                                  >{{ selectedOutline?.version === o.version ? '已选择' : '选择此版本' }}</n-button>
                                </template>
                              </n-card>
                            </n-gi>
                          </n-grid>
                          <n-divider style="margin: 12px 0;" />
                          <n-space vertical align="center" style="width: 100%;">
                            <n-button
                              type="primary"
                              :disabled="!selectedOutline"
                              :loading="generatingScriptFromTree"
                              @click="handleGenerateScriptFromTree"
                            >{{ selectedOutline ? `用「${selectedOutline.style}」版本生成剧本` : '请先选择一个版本' }}</n-button>
                            <n-text v-if="generatingScriptFromTree" depth="3" style="font-size: 12px;">
                              AI 正在创作完整剧本，预计需要 2-5 分钟，请耐心等待...
                            </n-text>
                          </n-space>
                        </n-card>
                      </template>
                    </n-spin>
                </n-space>
              </template>
            </n-spin>
              </n-tab-pane>

              <!-- 子 Tab: 历史 -->
              <n-tab-pane name="history" tab="历史">
                <n-spin :show="loadingCreativeHistory">
                  <n-empty v-if="creativeHistory.length === 0" description="暂无创作历史" size="small" />
                  <n-list v-else bordered>
                    <n-list-item v-for="item in creativeHistory" :key="item.tree.id">
                      <n-thing>
                        <template #header>
                          <n-space align="center" :size="8">
                            <n-tag size="small" :bordered="false">{{ item.tree.status === 'converted' ? '已转剧本' : item.tree.status }}</n-tag>
                            <n-text>{{ item.tree.user_theme }}</n-text>
                          </n-space>
                        </template>
                        <template #description>
                          <n-text depth="3" style="font-size: 12px;">{{ formatDate(item.tree.created_at) }}</n-text>
                        </template>
                        <!-- 概要卡片 -->
                        <n-grid v-if="item.outlines.length > 0" :cols="1" :y-gap="8" style="margin-top: 8px;">
                          <n-gi v-for="o in item.outlines" :key="o.id">
                            <n-card size="small" embedded>
                              <template #header>
                                <n-space align="center" :size="6">
                                  <n-tag size="small" round :type="(OUTLINE_VERSION_COLORS[o.version_label] || 'default') as any">{{ o.version_label }}</n-tag>
                                  <n-text strong>{{ o.style }}</n-text>
                                </n-space>
                              </template>
                              <n-text style="white-space: pre-wrap; line-height: 1.6; font-size: 13px;">{{ o.outline_text }}</n-text>
                              <template #action>
                                <n-button size="tiny" type="primary" @click="handleReuseOutline(o)">复用此概要</n-button>
                              </template>
                            </n-card>
                          </n-gi>
                        </n-grid>
                        <n-text v-else depth="3" style="font-size: 13px;">未生成概要</n-text>
                      </n-thing>
                    </n-list-item>
                  </n-list>
                </n-spin>
              </n-tab-pane>
            </n-tabs>
          </n-tab-pane>

          <!-- Tab 2: 角色 -->
          <n-tab-pane name="characters" tab="角色">
            <n-spin :show="loadingChars">
              <n-space justify="space-between" style="margin-bottom: 12px;">
                <n-text depth="3">项目角色 ({{ projectCharacters.length }})</n-text>
                <n-space>
                  <n-button
                    size="small"
                    type="warning"
                    :loading="generatingCharacters"
                    :disabled="!currentScript"
                    @click="showVisualSettingsModal = true"
                  >{{ generatingCharacters ? 'AI 正在生成角色...' : 'AI 生成角色' }}</n-button>
                  <n-button size="small" type="primary" @click="openAddCharModal">从角色库添加</n-button>
                </n-space>
              </n-space>
              <n-empty v-if="projectCharacters.length === 0" :description="currentScript ? '暂无角色，点击「AI 生成角色」自动创建' : '暂无角色，请先生成剧本'" />
              <n-grid :cols="3" :x-gap="12" :y-gap="12" v-else>
                <n-gi v-for="pc in projectCharacters" :key="pc.character_id">
                  <n-card size="small" hoverable>
                    <template #header>
                      <n-space align="center" :size="6">
                        <n-tag v-if="pc.traits?.role_type" size="tiny" :bordered="false" :type="(roleTypeColor(pc.traits?.role_type as string) as any)">
                          {{ roleTypeLabel(pc.traits?.role_type as string) }}
                        </n-tag>
                        <span style="font-weight: 600;">{{ pc.character_name }}</span>
                      </n-space>
                    </template>
                    <template #header-extra>
                      <n-button size="tiny" quaternary type="error" @click="handleRemoveChar(pc.character_id)">移除</n-button>
                    </template>
                    <n-space vertical :size="4">
                      <n-text v-if="pc.traits?.personality" depth="2" style="font-size: 13px;">性格: {{ pc.traits.personality as string }}</n-text>
                      <n-text v-if="pc.traits?.special_features" depth="3" style="font-size: 12px; color: #e8803a;">特殊: {{ pc.traits.special_features as string }}</n-text>
                      <n-text v-if="pc.traits?.appearance" depth="3" style="font-size: 12px;">外貌: {{ pc.traits.appearance as string }}</n-text>
                      <n-text v-if="pc.traits?.clothing" depth="3" style="font-size: 12px;">服饰: {{ pc.traits.clothing as string }}</n-text>
                    </n-space>
                    <template v-if="pc.traits?.image_prompt" #action>
                      <n-space :size="4">
                        <n-button size="tiny" quaternary type="info" @click="copyPrompt(pc.traits.image_prompt as string)">复制正向提示词</n-button>
                        <n-button v-if="pc.traits?.negative_prompt" size="tiny" quaternary type="warning" @click="copyPrompt(pc.traits.negative_prompt as string)">复制负面提示词</n-button>
                        <n-button size="tiny" quaternary @click="openRefImageDrawer(pc)">参考图 ({{ getRefImageCount(pc) }})</n-button>
                      </n-space>
                    </template>
                  </n-card>
                </n-gi>
              </n-grid>
            </n-spin>
          </n-tab-pane>

          <!-- Tab 3: 分镜 -->
          <n-tab-pane name="storyboards" tab="分镜">
            <n-spin :show="loadingStoryboards">
              <n-space justify="space-between" style="margin-bottom: 12px;">
                <n-text depth="3">共 {{ projectStoryboards.length }} 个分镜 · 总时长 {{ totalDurationText }}</n-text>
                <n-space>
                  <n-button
                    size="small"
                    :loading="autoAssigningDuration"
                    :disabled="projectStoryboards.length === 0"
                    @click="handleAutoAssignDurations"
                  >自动分配时长</n-button>
                  <n-button
                    size="small"
                    type="info"
                    :loading="loadingRhythm"
                    :disabled="projectStoryboards.length === 0"
                    @click="handleRhythmAnalysis"
                  >节奏分析</n-button>
                  <n-button
                    size="small"
                    type="success"
                    :loading="loadingReview"
                    :disabled="projectStoryboards.length === 0"
                    @click="handleReviewStoryboards"
                  >爆款审核</n-button>
                  <n-button
                    size="small"
                    color="#9333ea"
                    text-color="white"
                    :loading="reconstructing"
                    :disabled="!currentScript"
                    @click="handleReconstructStoryboards"
                  >爆款重构</n-button>
                  <n-button
                    size="small"
                    type="warning"
                    :loading="generatingStoryboards"
                    :disabled="!currentScript"
                    @click="handleGenerateStoryboards"
                  >AI 生成分镜</n-button>
                  <n-button size="small" type="primary" @click="openCreateStoryboard">新增分镜</n-button>
                </n-space>
              </n-space>
              <n-empty v-if="projectStoryboards.length === 0" :description="currentScript ? '暂无分镜，点击「AI 生成分镜」自动创建' : '暂无分镜，请先生成剧本'" />
              <n-data-table
                v-else
                :columns="storyboardColumns"
                :data="projectStoryboards"
                :bordered="false"
                size="small"
                :row-key="(row: any) => row.id"
              />
              <n-space v-if="projectStoryboards.length > 0 && episodeDurationSummary.length > 0" style="margin-top: 8px;" :size="8">
                <n-tag v-for="ep in episodeDurationSummary" :key="ep.episode"
                  size="small"
                  :type="ep.inRange ? 'success' : 'warning'"
                  :bordered="false"
                >第{{ ep.episode }}集: {{ ep.count }}镜 / {{ ep.duration }}s</n-tag>
              </n-space>
            </n-spin>
          </n-tab-pane>

          <!-- Tab 4: 镜头制作 -->
          <n-tab-pane name="lens-production" tab="镜头制作">
            <LensProduction :projectId="projectId" @update="fetchStoryboards" />
          </n-tab-pane>

          <!-- Tab 5: 视觉风格 -->
          <n-tab-pane name="visual-style" tab="视觉风格">
            <n-spin :show="loadingVisualStyle">
              <n-space vertical :size="16">
                <n-card title="风格参考图" size="small">
                  <template v-if="visualStyle.style_reference_image">
                    <n-space vertical align="center" :size="8">
                      <n-image :src="visualStyle.style_reference_image" width="200" height="200" object-fit="cover" />
                      <n-button size="tiny" type="error" @click="handleRemoveStyleRef">移除参考图</n-button>
                    </n-space>
                  </template>
                  <template v-else>
                    <n-upload :max="1" accept=".jpg,.jpeg,.png,.webp" :custom-request="handleUploadStyleRef" :show-file-list="false">
                      <n-button size="small">上传风格参考图</n-button>
                    </n-upload>
                    <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                      上传一张代表目标视觉风格的参考图片
                    </n-text>
                  </template>
                </n-card>

                <n-card title="风格参数" size="small">
                  <n-form label-placement="left" label-width="80" size="small">
                    <n-form-item label="艺术风格">
                      <n-select
                        v-model:value="visualStyle.art_style"
                        :options="artStyleOptions"
                        filterable
                        clearable
                        placeholder="选择艺术风格"
                      />
                    </n-form-item>
                    <n-form-item label="色调">
                      <n-select
                        v-model:value="visualStyle.color_palette"
                        :options="colorPaletteOptions"
                        filterable
                        clearable
                        multiple
                        tag
                        placeholder="选择主色调"
                      />
                    </n-form-item>
                    <n-form-item label="光照规则">
                      <n-select
                        v-model:value="visualStyle.lighting_rule"
                        :options="lightingRuleOptions"
                        clearable
                        placeholder="选择光照规则"
                      />
                    </n-form-item>
                    <n-form-item label="运镜风格">
                      <n-select
                        v-model:value="visualStyle.camera_style"
                        :options="cameraStyleOptions"
                        clearable
                        placeholder="选择运镜风格"
                      />
                    </n-form-item>
                  </n-form>
                </n-card>

                <n-space>
                  <n-button type="primary" size="small" :loading="savingVisualStyle" @click="handleSaveVisualStyle">
                    保存风格设置
                  </n-button>
                  <n-button size="small" @click="handleApplyCurrentVisualSettings">
                    从当前视觉设定应用
                  </n-button>
                </n-space>
              </n-space>
            </n-spin>
          </n-tab-pane>

          <!-- Tab 6: 版本 -->
          <n-tab-pane name="versions" tab="版本">
            <n-spin :show="loadingSnapshots">
              <n-empty v-if="snapshots.length === 0" description="暂无快照" size="small" />
              <n-list v-else bordered>
                <n-list-item v-for="snap in snapshots" :key="snap.id">
                  <n-thing>
                    <template #header>{{ snap.snapshot_name }}</template>
                    <template #description>
                      <n-text depth="3" style="font-size: 12px;">{{ formatDate(snap.created_at) }}</n-text>
                    </template>
                    <template #header-extra>
                      <n-space size="small">
                        <n-button size="tiny" @click="handleViewSnapshot(snap)">查看</n-button>
                        <n-button size="tiny" type="primary" @click="handleRestore(snap)">恢复</n-button>
                        <n-checkbox
                          :checked="compareIds.includes(snap.id)"
                          @update:checked="(v: boolean) => toggleCompare(snap.id, v)"
                        >对比</n-checkbox>
                      </n-space>
                    </template>
                  </n-thing>
                </n-list-item>
              </n-list>
            </n-spin>
            <n-button
              v-if="compareIds.length === 2"
              type="info"
              style="margin-top: 12px;"
              @click="handleCompare"
              :loading="comparing"
            >对比选中的 2 个快照</n-button>
          </n-tab-pane>

          <!-- Tab 6: 对比结果 -->
          <n-tab-pane name="compare" tab="对比结果" :disabled="!compareResult">
            <template v-if="compareResult">
              <n-card title="剧本差异" size="small" style="margin-bottom: 16px;">
                <n-descriptions bordered :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="快照 A">{{ compareResult.snapshot_1_name }}</n-descriptions-item>
                  <n-descriptions-item label="快照 B">{{ compareResult.snapshot_2_name }}</n-descriptions-item>
                  <n-descriptions-item label="标题变化">
                    <n-text v-if="!(compareResult.script_diff as any).title_changed" type="success">无变化</n-text>
                    <n-text v-else type="warning">{{ (compareResult.script_diff as any).title_1 }} → {{ (compareResult.script_diff as any).title_2 }}</n-text>
                  </n-descriptions-item>
                </n-descriptions>
              </n-card>
              <n-card title="分镜差异" size="small">
                <n-descriptions bordered :column="1" label-placement="left" size="small">
                  <n-descriptions-item label="分镜数">{{ (compareResult.storyboards_diff as any).count_1 }} → {{ (compareResult.storyboards_diff as any).count_2 }}</n-descriptions-item>
                </n-descriptions>
              </n-card>
            </template>
          </n-tab-pane>
        </n-tabs>
      </template>
    </n-spin>

    <!-- 编辑项目弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="编辑项目" positive-text="保存" negative-text="取消" @positive-click="handleUpdate">
      <n-form label-placement="top">
        <n-form-item label="项目名称"><n-input v-model:value="editForm.name" /></n-form-item>
        <n-form-item label="项目描述"><n-input v-model:value="editForm.description" type="textarea" :rows="3" /></n-form-item>
      </n-form>
    </n-modal>

    <!-- 节奏分析弹窗 -->
    <n-modal v-model:show="showRhythmModal" preset="card" title="节奏分析报告" style="max-width: 600px;">
      <n-input
        type="textarea"
        :value="rhythmReport"
        :rows="16"
        readonly
        style="font-family: monospace; font-size: 13px;"
      />
      <template #action>
        <n-space justify="space-between">
          <n-button
            type="warning"
            :loading="optimizingByRhythm"
            @click="handleAutoOptimize"
          >自动优化</n-button>
          <n-space>
            <n-button @click="showRhythmModal = false">关闭</n-button>
            <n-button type="primary" @click="handleCopyRhythmReport">复制报告</n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- 审核报告弹窗 -->
    <n-modal v-model:show="showReviewModal" preset="card" title="分镜审核报告（爆款标准）" style="max-width: 700px;">
      <template v-if="reviewReport">
        <n-space vertical size="large">
          <n-card size="small">
            <n-statistic label="综合评分" :value="reviewReport.overall_score">
              <template #suffix>/ 100</template>
            </n-statistic>
          </n-card>
          <n-card v-for="ep in reviewReport.episodes" :key="ep.episode" size="small">
            <template #header>第{{ ep.episode }}集 · {{ ep.score }}分 · {{ ep.shot_count }}镜 / {{ ep.total_duration }}s</template>
            <n-grid :cols="4" :x-gap="8">
              <n-gi v-for="(val, dim) in ep.dimensions" :key="dim">
                <n-text :type="val >= 80 ? 'success' : val >= 60 ? 'warning' : 'error'" style="font-size: 12px;">{{ dimLabel(String(dim)) }}: {{ val }}</n-text>
              </n-gi>
            </n-grid>
            <n-divider style="margin: 8px 0;" />
            <n-text v-if="ep.issues.length" type="error" style="font-size: 12px;">
              <div v-for="(issue, i) in ep.issues" :key="i">⚠ {{ issue }}</div>
            </n-text>
            <n-text v-if="ep.suggestions.length" type="info" style="font-size: 12px;">
              <div v-for="(sug, i) in ep.suggestions" :key="i">💡 {{ sug }}</div>
            </n-text>
          </n-card>
          <n-card v-if="reviewReport.global_suggestions.length" size="small" title="全局建议">
            <div v-for="(s, i) in reviewReport.global_suggestions" :key="i" style="font-size: 12px;">· {{ s }}</div>
          </n-card>
        </n-space>
      </template>
      <template #action>
        <n-space justify="space-between">
          <n-space>
            <n-button type="error" :loading="addingClimax" @click="handleAddClimaxShots">添加高潮镜头</n-button>
            <n-button type="warning" :loading="optimizingByReview" @click="handleOptimizeByReview">全面优化</n-button>
          </n-space>
          <n-space>
            <n-button @click="showReviewModal = false">关闭</n-button>
            <n-button type="primary" @click="handleCopyReview">复制报告</n-button>
          </n-space>
        </n-space>
      </template>
    </n-modal>

    <!-- 快照详情弹窗 -->

    <!-- 爆款重构预览弹窗 -->
    <n-modal v-model:show="showReconstructResult" preset="card" title="爆款重构预览" style="max-width: 750px;">
      <template v-if="reconstructResult">
        <n-alert v-if="reconstructResult.preview" type="info" style="margin-bottom: 12px;">
          以下为LLM基于爆款心理机制生成的新分镜，当前仅预览。点击"应用此重构"将替换现有分镜（自动备份快照）。
        </n-alert>
        <n-alert v-else type="success" style="margin-bottom: 12px;">
          重构已应用！旧分镜已自动备份为快照（ID: {{ reconstructResult.snapshot_id?.slice(0,8) }}...），可通过快照管理回滚。
        </n-alert>
        <n-space vertical size="large">
          <n-card size="small">
            <n-space justify="space-around">
              <n-statistic label="重构集数" :value="reconstructResult.total_episodes" />
              <n-statistic label="新镜头数" :value="reconstructResult.total_shots" />
              <n-statistic v-if="reconstructResult.old_shot_count != null" label="原镜头数" :value="reconstructResult.old_shot_count" />
            </n-space>
          </n-card>
          <n-card size="small" title="爆款原则">
            <n-space size="small">
              <n-tag v-for="p in reconstructResult.principles_applied" :key="p.id" size="small" type="info">
                {{ p.name }} ({{ Math.round(p.weight * 100) }}%)
              </n-tag>
            </n-space>
          </n-card>
          <n-card size="small" title="重构镜头预览">
            <n-collapse>
              <n-collapse-item
                v-for="ep in reconstructEpisodes"
                :key="ep.episode"
              >
                <template #header>
                  <span>第{{ ep.episode }}集（{{ ep.shots.length }}镜）</span>
                </template>
                <n-table size="small" :bordered="false" :single-line="false" striped>
                  <thead>
                    <tr>
                      <th style="width:40px;">#</th>
                      <th style="width:50px;">景别</th>
                      <th style="width:50px;">运镜</th>
                      <th>动作</th>
                      <th style="width:50px;">情绪</th>
                      <th>对话</th>
                      <th>设计意图</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in ep.shots" :key="s.shot_no">
                      <td>{{ s.shot_no }}</td>
                      <td><n-tag size="tiny" :bordered="false">{{ s.shot_type }}</n-tag></td>
                      <td>{{ s.camera_move }}</td>
                      <td style="font-size:12px;">{{ s.action }}</td>
                      <td><n-tag size="tiny" :type="s.emotion === '紧张' || s.emotion === '恐惧' || s.emotion === '愤怒' ? 'error' : s.emotion === '惊喜' || s.emotion === '期待' ? 'success' : 'default'" :bordered="false">{{ s.emotion }}</n-tag></td>
                      <td style="font-size:12px; color: #666;">{{ s.dialogue || '-' }}</td>
                      <td style="font-size:11px; color: #9333ea;">{{ s.note || '-' }}</td>
                    </tr>
                  </tbody>
                </n-table>
              </n-collapse-item>
            </n-collapse>
          </n-card>
        </n-space>
      </template>
      <template #action>
        <n-space justify="space-between" style="width:100%;">
          <n-button @click="showReconstructResult = false">关闭</n-button>
          <n-button
            v-if="reconstructResult?.preview"
            type="error"
            :loading="applyingReconstruct"
            @click="handleApplyReconstruct"
          >应用此重构（替换现有分镜）</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 快照详情弹窗 -->
    <n-modal v-model:show="showSnapshotModal" preset="dialog" :title="viewingSnapshot?.snapshot_name || '快照详情'" style="width: 600px;">
      <template v-if="viewingSnapshotDetail">
        <n-descriptions bordered :column="1" label-placement="left" size="small">
          <n-descriptions-item label="快照名称">{{ viewingSnapshotDetail.snapshot_name }}</n-descriptions-item>
          <n-descriptions-item label="创建时间">{{ formatDate(viewingSnapshotDetail.created_at) }}</n-descriptions-item>
          <n-descriptions-item label="分镜数量">{{ viewingSnapshotDetail.storyboards_snapshot?.length || 0 }}</n-descriptions-item>
        </n-descriptions>
      </template>
    </n-modal>

    <!-- 添加角色弹窗 -->
    <n-modal v-model:show="showAddCharModal" preset="dialog" title="从角色库添加角色" :show-icon="false" style="width: 500px;">
      <n-spin :show="loadingAllChars">
        <n-empty v-if="allCharacters.length === 0" description="角色库为空，请先到角色库页面创建" />
        <n-list v-else bordered>
          <n-list-item v-for="char in allCharacters" :key="char.id">
            <n-thing>
              <template #header>{{ char.name }}</template>
              <template #header-extra>
                <n-space>
                  <n-input v-model:value="charRoleNames[char.id]" placeholder="剧中角色名" size="small" style="width: 120px;" />
                  <n-button size="small" type="primary" @click="handleAddSingleChar(char.id)">添加</n-button>
                </n-space>
              </template>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-spin>
      <template #action>
        <n-button @click="showAddCharModal = false">关闭</n-button>
      </template>
    </n-modal>

    <!-- 分镜创建/编辑弹窗 -->
    <n-modal
      v-model:show="showStoryboardModal"
      preset="dialog"
      :title="editingStoryboardId ? '编辑分镜' : '新增分镜'"
      positive-text="保存"
      negative-text="取消"
      :loading="savingStoryboard"
      @positive-click="handleSaveStoryboard"
    >
      <n-form :model="storyboardForm" label-placement="top">
        <n-grid :cols="2" :x-gap="12">
          <n-gi><n-form-item label="集数"><n-input-number v-model:value="storyboardForm.episode_no" :min="1" style="width: 100%;" /></n-form-item></n-gi>
          <n-gi><n-form-item label="镜头序号"><n-input-number v-model:value="storyboardForm.shot_no" :min="1" style="width: 100%;" /></n-form-item></n-gi>
          <n-gi><n-form-item label="景别"><n-select v-model:value="storyboardForm.shot_type" :options="shotTypeOptions" /></n-form-item></n-gi>
          <n-gi><n-form-item label="运镜"><n-select v-model:value="storyboardForm.camera_move" :options="cameraMoveOptions" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item label="动作描述"><n-input v-model:value="storyboardForm.action" type="textarea" :rows="2" /></n-form-item>
        <n-form-item label="对话内容"><n-input v-model:value="storyboardForm.dialogue" type="textarea" :rows="2" /></n-form-item>
        <n-grid :cols="3" :x-gap="12">
          <n-gi><n-form-item label="情绪"><n-select v-model:value="storyboardForm.emotion" :options="emotionOptions" /></n-form-item></n-gi>
          <n-gi><n-form-item label="特效"><n-select v-model:value="storyboardForm.vfx" :options="vfxOptions" /></n-form-item></n-gi>
          <n-gi><n-form-item label="光线"><n-input v-model:value="storyboardForm.lighting" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item label="环境/背景"><n-input v-model:value="storyboardForm.environment" type="textarea" :rows="2" /></n-form-item>
      </n-form>
    </n-modal>

    <!-- 视觉设定弹窗 -->
    <n-modal v-model:show="showVisualSettingsModal" preset="dialog" title="视觉基调设定" positive-text="开始生成" negative-text="取消" style="width: 600px;" :loading="generatingCharacters" @positive-click="handleGenerateCharacters">
      <n-space vertical :size="12">
        <!-- 预设选择器 -->
        <n-form-item label="加载预设风格">
          <n-select v-model:value="selectedPresetId" :options="presetOptions" placeholder="选择预设风格快速填充" clearable @update:value="handlePresetChange" />
        </n-form-item>

        <n-divider style="margin: 0;" />

        <!-- 简易/高级模式切换 -->
        <n-space justify="space-between" align="center">
          <n-text strong>详细设定</n-text>
          <n-switch v-model:value="advancedMode">
            <template #checked>高级</template>
            <template #unchecked>简易</template>
          </n-switch>
        </n-space>

        <n-form label-placement="left" label-width="80">
          <n-form-item label="画风">
            <n-select v-model:value="visualSettings.art_style" :options="artStyleOptions" filterable clearable multiple tag placeholder="可选择多个画风" />
          </n-form-item>
          <n-form-item label="时代">
            <n-select v-model:value="visualSettings.era" :options="eraOptions" filterable clearable />
          </n-form-item>
          <n-form-item label="环境">
            <n-select v-model:value="visualSettings.environment" :options="environmentOptions" filterable clearable multiple tag placeholder="可选择多个环境" />
          </n-form-item>
          <n-form-item label="色调">
            <n-select v-model:value="visualSettings.color_palette" :options="colorPaletteOptions" filterable clearable multiple tag placeholder="可选择多种色调" />
          </n-form-item>

          <!-- 高级选项 -->
          <template v-if="advancedMode">
            <n-form-item label="文化风格">
              <n-select v-model:value="visualSettings.cultural_style" :options="culturalStyleOptions" />
            </n-form-item>
            <n-form-item label="光照风格">
              <n-select v-model:value="visualSettings.lighting" :options="lightingOptions" filterable clearable multiple tag placeholder="可选择多种光照" />
            </n-form-item>
            <n-form-item label="相机角度">
              <n-select v-model:value="visualSettings.camera_angle" :options="cameraAngleOptions" />
            </n-form-item>
            <n-form-item label="渲染质量">
              <n-select v-model:value="visualSettings.render_quality" :options="renderQualityOptions" />
            </n-form-item>
            <n-form-item label="全局备注">
              <n-input v-model:value="visualSettings.global_note" type="textarea" :rows="2" placeholder="一致性约束，追加到每个角色 prompt 末尾" />
            </n-form-item>
          </template>
        </n-form>

        <n-space justify="space-between" align="center">
          <n-text depth="3" style="font-size: 12px;">
            不确定设定？留空即可，AI 会根据剧本内容自动推断。
          </n-text>
          <n-button size="small" :loading="savingTemplate" @click="handleSaveAsTemplate">保存为模板</n-button>
        </n-space>
      </n-space>
    </n-modal>

    <!-- 角色参考图抽屉 -->
    <n-drawer v-model:show="showRefImageDrawer" :width="640" placement="right">
      <n-drawer-content :title="refImageCharName + ' - 参考图'">
        <n-space vertical :size="12">
          <n-space>
            <n-button size="small" type="primary" @click="handleUploadRefImage">上传参考图</n-button>
            <n-button size="small" type="info" :loading="generatingPortrait" @click="handleGeneratePortrait">AI 生成角色</n-button>
            <n-button size="small" :loading="generatingAnglePrompts" @click="handleGenerateAnglePrompts">生成多角度提示词</n-button>
          </n-space>
          <input ref="fileInputRef" type="file" accept="image/jpeg,image/png,image/webp" style="display:none" @change="onRefImageFileSelected" />

          <!-- 上传时选角度 -->
          <n-modal v-model:show="showRefUploadModal" preset="dialog" title="上传参考图" positive-text="确认上传" negative-text="取消" @positive-click="handleConfirmUpload">
            <n-form label-placement="left" label-width="80">
              <n-form-item label="角度">
                <n-select v-model:value="refUploadAngle" :options="angleOptions" />
              </n-form-item>
              <n-form-item label="姿态">
                <n-select v-model:value="refUploadPose" :options="poseOptions" />
              </n-form-item>
              <n-form-item label="设为主视觉">
                <n-switch v-model:value="refUploadPrimary" />
              </n-form-item>
            </n-form>
          </n-modal>

          <!-- 多角度提示词弹窗 -->
          <n-modal v-model:show="showAnglePromptsModal" preset="dialog" title="多角度提示词" positive-text="关闭" :show-icon="false" style="width: 600px;">
            <n-space vertical :size="8">
              <n-card v-for="(prompt, angle) in anglePrompts" :key="angle" size="small">
                <template #header>
                  <n-space align="center" :size="8">
                    <n-tag size="small">{{ angle }}</n-tag>
                    <n-button size="tiny" quaternary type="info" @click="copyPrompt(prompt)">复制</n-button>
                  </n-space>
                </template>
                <n-text style="font-size: 12px; word-break: break-all;">{{ prompt }}</n-text>
              </n-card>
              <n-text v-if="Object.keys(anglePrompts).length === 0" depth="3">暂无提示词</n-text>
            </n-space>
          </n-modal>

          <!-- 参考图网格 -->
          <n-grid :cols="2" :x-gap="12" :y-gap="12" v-if="refImageList.length > 0">
            <n-gi v-for="img in refImageList" :key="img.id">
              <n-card size="small" style="cursor: pointer;" @click="previewImageUrl = getFullUrl(img.url)">
                <img :src="getFullUrl(img.url)" style="width: 100%; border-radius: 4px; display: block;" @error="($event.target as HTMLImageElement).style.display='none'" />
                <n-space justify="space-between" align="center" style="margin-top: 6px;">
                  <n-space :size="4">
                    <n-tag size="tiny">{{ img.angle }}</n-tag>
                    <n-tag v-if="img.is_primary" size="tiny" type="success">主视觉</n-tag>
                  </n-space>
                  <n-space :size="4" @click.stop>
                    <n-button v-if="!img.is_primary" size="tiny" quaternary @click="handleSetPrimary(img.id)">设为主视觉</n-button>
                    <n-button size="tiny" quaternary type="error" @click="handleDeleteRefImage(img.id)">删除</n-button>
                  </n-space>
                </n-space>
              </n-card>
            </n-gi>
          </n-grid>
          <n-empty v-else description="暂无参考图，点击上传或生成多角度提示词" />
        </n-space>
      </n-drawer-content>
    </n-drawer>

    <!-- 图片预览 Modal -->
    <n-modal v-model:show="previewImageVisible" preset="card" style="max-width: 90vw; max-height: 90vh;" :bordered="false">
      <img :src="previewImageUrl" style="width: 100%; display: block; border-radius: 8px;" />
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import {
  NButton, NCard, NCheckbox, NCollapse, NCollapseItem, NDataTable,
  NDescriptions, NDescriptionsItem, NDivider, NDrawer, NDrawerContent,
  NEmpty, NForm, NFormItem, NGi, NGrid, NH3, NInput, NInputNumber,
  NList, NListItem, NModal, NPageHeader, NSelect, NSpace, NSpin,
  NStatistic, NSwitch, NTabPane, NTabs, NTable, NTag, NText, NThing,
  NAlert, NUpload, useMessage, type DataTableColumns, type SelectOption,
} from 'naive-ui'
import {
  projectsApi,
  type SnapshotBriefResponse,
  type SnapshotDetailResponse,
  type CompareResponse,
  type ProjectCharacterResponse,
} from '../api/projects'
import {
  scriptsApi,
  type ScriptContent,
} from '../api/scripts'
import {
  storyboardsApi,
  type StoryboardResponse,
  type StoryboardCreate,
} from '../api/storyboards'
import {
  charactersApi,
  type ReferenceImageItem,
} from '../api/characters'
import LensProduction from '../components/LensProduction.vue'
import { useProjectStore } from '../stores/projectStore'
import { useNarrativeTree } from '../composables/useNarrativeTree'
import { useVisualSettings } from '../composables/useVisualSettings'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const projectId = route.params.id as string

// ── Store & Composables ──
const store = useProjectStore()
const nt = useNarrativeTree(projectId, {
  currentScript: store.currentScript as any,
  onScriptGenerated: async () => {
    await store.fetchDashboard(projectId)
    await store.fetchProject(projectId)
    await nt.fetchCreativeHistory()
    await nextTick()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  },
})
const vs = useVisualSettings(projectId)

// ── 从 store 解构（storeToRefs 保持响应性） ──
const {
  project, loading, dashboard,
  currentScript, loadingScript,
  projectCharacters, allCharacters, charRoleNames, loadingChars, loadingAllChars,
  projectStoryboards, loadingStoryboards, generatingStoryboards,
  loadingSnapshots, snapshots,
} = storeToRefs(store)

// ── 叙事树（composable） ──
const {
  narrativeTree, generatingTree, generatingScriptFromTree,
  treeTheme, selectedBranchIds, outlines, selectedOutline,
  generatingOutlines, expandingNodeId,
  scriptSubTab, loadingCreativeHistory, creativeHistory,
  tagColor, isBranchSelected, toggleBranch, flattenNodes,
  handleExpandNode, handleGenerateTree, handleGenerateScriptFromTree,
  handleGenerateOutlines, handleSelectOutline,
  fetchNarrativeTree, fetchCreativeHistory, handleReuseOutline,
} = nt

// ── 视觉设置（composable） ──
const {
  generatingCharacters, showVisualSettingsModal, selectedPresetId,
  advancedMode, templateList, savingTemplate, visualSettings,
  loadingVisualStyle, savingVisualStyle, visualStyle,
  artStyleOptions, eraOptions, environmentOptions,
  colorPaletteOptions, lightingOptions, cameraAngleOptions,
  renderQualityOptions, culturalStyleOptions,
  lightingRuleOptions, cameraStyleOptions,
  fetchVisualStyle, handleSaveVisualStyle,
  handleUploadStyleRef, handleRemoveStyleRef,
  handleApplyCurrentVisualSettings, handlePresetChange,
  fetchPresets, handleSaveAsTemplate, getVisualSettingsPayload,
} = vs

// --- 状态 ---
// project, loading, dashboard, currentScript, etc. — 来自 storeToRefs(store)
const activeTab = ref('script')

// Script
const editingScript = ref(false)
const savingScript = ref(false)
const editScriptContent = ref<ScriptContent | null>(null)

// Characters
const showAddCharModal = ref(false)

// Storyboards (store-managed: loadingStoryboards, generatingStoryboards, projectStoryboards)

// Narrative Tree (composable-managed)

// Creative History sub-tab (composable-managed)

const showStoryboardModal = ref(false)
const savingStoryboard = ref(false)
const editingStoryboardId = ref<string | null>(null)
const regeneratingPromptId = ref<string | null>(null)
const enhancingPromptId = ref<string | null>(null)
const autoAssigningDuration = ref(false)
const loadingRhythm = ref(false)
const loadingReview = ref(false)
const showReviewModal = ref(false)
const reviewReport = ref<any>(null)
const optimizingByReview = ref(false)
const addingClimax = ref(false)
const reconstructing = ref(false)
const applyingReconstruct = ref(false)
const showReconstructResult = ref(false)
const reconstructResult = ref<any>(null)
const reconstructEpisodes = computed(() => {
  if (!reconstructResult.value?.changes) return []
  const map = new Map<number, any[]>()
  for (const c of reconstructResult.value.changes) {
    const ep = c.episode_no
    if (!map.has(ep)) map.set(ep, [])
    map.get(ep)!.push(c)
  }
  return Array.from(map.entries()).map(([episode, shots]) => ({
    episode,
    shots: shots.sort((a: any, b: any) => a.shot_no - b.shot_no),
  }))
})
const showRhythmModal = ref(false)
const rhythmReport = ref('')
const optimizingByRhythm = ref(false)
const expandedPromptId = ref<string | null>(null)
const editingDurationId = ref<string | null>(null)
const storyboardForm = reactive({
  episode_no: 1, shot_no: 1, shot_type: '中景', camera_move: '固定',
  action: '', dialogue: '', emotion: '', vfx: '无', environment: '', lighting: '',
})

const vfxOptions: SelectOption[] = [
  { label: '无', value: '无' },
  { label: '光效', value: '光效' },
  { label: '粒子特效', value: '粒子特效' },
  { label: '镜头特效', value: '镜头特效' },
  { label: '色彩滤镜', value: '色彩滤镜' },
  { label: '动态模糊', value: '动态模糊' },
  { label: '转场特效', value: '转场特效' },
]

// AI 角色生成（composable-managed: generatingCharacters, showVisualSettingsModal）
const presetOptions = computed<SelectOption[]>(() =>
  templateList.value.map(t => ({
    label: t.is_system ? `⭐ ${t.name}` : t.name,
    value: t.id,
  })),
)

// 视觉设置（composable-managed: visualSettings, artStyleOptions, etc.）
// 视觉风格锁定（composable-managed: visualStyle, loadingVisualStyle, etc.）
// 视觉风格方法（composable-managed: fetchVisualStyle, handleSaveVisualStyle, etc.）

// Reference Images
const showRefImageDrawer = ref(false)
const refImageCharName = ref('')
const refImageCharId = ref('')
const refImageList = ref<ReferenceImageItem[]>([])
const showRefUploadModal = ref(false)
const refUploadAngle = ref('front')
const refUploadPose = ref('standing')
const refUploadPrimary = ref(false)
const pendingRefFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const generatingAnglePrompts = ref(false)
const generatingPortrait = ref(false)
const previewImageUrl = ref('')
const previewImageVisible = computed({
  get: () => !!previewImageUrl.value,
  set: (v: boolean) => { if (!v) previewImageUrl.value = '' },
})

function getFullUrl(path: string): string {
  if (!path || path.startsWith('http')) return path
  return `${window.location.origin}${path}`
}
const showAnglePromptsModal = ref(false)
const anglePrompts = ref<Record<string, string>>({})
const angleOptions: SelectOption[] = [
  { label: '正面', value: 'front' },
  { label: '左侧', value: 'left_side' },
  { label: '右侧', value: 'right_side' },
  { label: '背面', value: 'back' },
  { label: '全身', value: 'full_body' },
  { label: '半身', value: 'half_body' },
]
const poseOptions: SelectOption[] = [
  { label: '站立', value: 'standing' },
  { label: '坐着', value: 'sitting' },
  { label: '动作', value: 'action' },
  { label: '行走', value: 'walking' },
  { label: '动态', value: 'dynamic_pose' },
]


// Versions
// Versions (store-managed: loadingSnapshots, snapshots)
const compareIds = ref<string[]>([])
const compareResult = ref<CompareResponse | null>(null)
const comparing = ref(false)

// Modals
const showEditModal = ref(false)
const showSnapshotModal = ref(false)
const viewingSnapshot = ref<SnapshotBriefResponse | null>(null)
const viewingSnapshotDetail = ref<SnapshotDetailResponse | null>(null)
const editForm = reactive({ name: '', description: '' })

// --- Options ---
const shotTypeOptions: SelectOption[] = [
  { label: '远景', value: '远景' }, { label: '全景', value: '全景' },
  { label: '中景', value: '中景' }, { label: '近景', value: '近景' },
  { label: '特写', value: '特写' },
]
const cameraMoveOptions: SelectOption[] = [
  { label: '固定', value: '固定' }, { label: '推', value: '推' },
  { label: '拉', value: '拉' }, { label: '摇', value: '摇' },
  { label: '移', value: '移' }, { label: '跟', value: '跟' },
]
const emotionOptions: SelectOption[] = [
  { label: '愤怒', value: '愤怒' }, { label: '悲伤', value: '悲伤' },
  { label: '喜悦', value: '喜悦' }, { label: '紧张', value: '紧张' },
  { label: '恐惧', value: '恐惧' }, { label: '甜蜜', value: '甜蜜' },
  { label: '惊讶', value: '惊讶' }, { label: '平静', value: '平静' },
]

// --- Computed ---
const statusText = computed(() => {
  const map: Record<string, string> = { active: '进行中', archived: '已归档', completed: '已完成' }
  return map[project.value?.status || 'active'] || '进行中'
})
const statusTagType = computed(() => {
  const map: Record<string, 'success' | 'default' | 'info'> = { active: 'success', archived: 'default', completed: 'info' }
  return map[project.value?.status || 'active'] || 'success'
})

const storyboardColumns: DataTableColumns<StoryboardResponse> = [
  { title: '集', key: 'episode_no', width: 35, align: 'center' },
  { title: '镜', key: 'shot_no', width: 35, align: 'center' },
  { title: '景别', key: 'shot_type', width: 45 },
  { title: '运镜', key: 'camera_move', width: 45 },
  {
    title: '时长(s)', key: 'duration_seconds', width: 60, align: 'center',
    render: (row) => h(NSpace, { size: 2, align: 'center', justify: 'center' }, () => [
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
    ]),
  },
  { title: '动作', key: 'action', ellipsis: { tooltip: true }, render: (row) => truncate(row.action, 20) },
  {
    title: '情绪', key: 'emotion', width: 55,
    render: (row) => h(NTag, {
      size: 'tiny', bordered: false,
      type: row.is_key_moment ? 'error' : 'default',
    }, () => row.emotion),
  },
  {
    title: '特效', key: 'vfx', width: 50,
    render: (row) => row.vfx && row.vfx !== '无'
      ? h(NTag, { size: 'tiny', type: 'warning', bordered: false }, () => row.vfx)
      : h(NText, { depth: 3 }, () => '-'),
  },
  {
    title: '提示词', key: 'prompt_text', width: 220,
    render: (row) => {
      if (!row.prompt_text) return h(NText, { depth: 3 }, () => '未生成')
      const expanded = expandedPromptId.value === row.id
      const displayText = expanded ? row.prompt_text : (row.prompt_text.length > 50 ? row.prompt_text.slice(0, 50) + '...' : row.prompt_text)
      return h(NSpace, { size: 4, align: 'start', vertical: true }, () => [
        h(NSpace, { size: 4, align: 'center' }, () => [
          h('span', {
            style: 'font-size: 12px; cursor: pointer; color: #4098fc;',
            onClick: () => { expandedPromptId.value = expanded ? null : row.id },
          }, expanded ? '收起' : '展开'),
          h(NButton, {
            size: 'tiny', quaternary: true,
            onClick: () => { navigator.clipboard.writeText(row.prompt_text || ''); message.success('已复制') },
          }, () => '📋'),
          row.negative_prompt ? h('span', {
            style: 'font-size: 11px; color: #d03050; cursor: help;',
            title: row.negative_prompt,
          }, '⛔负面') : null,
        ]),
        h('div', { style: 'font-size: 12px; line-height: 1.5; word-break: break-all; white-space: pre-wrap;' }, displayText),
      ])
    },
  },
  {
    title: '关键', key: 'is_key_moment', width: 35, align: 'center',
    render: (row) => h(NText, { type: row.is_key_moment ? 'error' : 'default' }, () => row.is_key_moment ? '★' : ''),
  },
  { title: '定稿', key: 'approved', width: 35, align: 'center', render: (row) => h(NText, { type: row.approved ? 'success' : 'default' }, () => row.approved ? '✓' : '') },
  {
    title: '操作', key: 'actions', width: 140,
    render: (row) => h(NSpace, { size: 4 }, () => [
      h(NButton, { size: 'tiny', quaternary: true, onClick: () => openEditStoryboard(row) }, () => '编辑'),
      h(NButton, { size: 'tiny', quaternary: true, type: 'info', loading: regeneratingPromptId.value === row.id, onClick: () => handleRegeneratePrompt(row) }, () => '提示词'),
      h(NButton, {
        size: 'tiny', quaternary: true, type: 'warning',
        loading: enhancingPromptId.value === row.id,
        onClick: () => handleEnhancePrompt(row),
      }, () => '增强'),
      h(NButton, { size: 'tiny', quaternary: true, type: 'error', onClick: () => handleDeleteStoryboard(row) }, () => '删除'),
    ]),
  },
]

// --- 数据加载（store-managed: fetchProject, fetchDashboard, fetchScript, etc.） ---
async function fetchProject() {
  await store.fetchProject(projectId)
  editForm.name = store.project?.name || ''
  editForm.description = store.project?.description || ''
}
async function fetchDashboard() { await store.fetchDashboard(projectId) }
async function fetchScript() { await store.fetchScript(projectId) }
async function fetchProjectCharacters() { await store.fetchProjectCharacters(projectId) }
async function fetchAllCharacters() { await store.fetchAllCharacters() }
async function fetchStoryboards() { await store.fetchStoryboards(projectId) }
async function fetchSnapshots() { await store.fetchSnapshots(projectId) }

// --- 叙事树（composable-managed: tagColor, toggleBranch, flattenNodes, etc.） ---

// --- 剧本编辑 ---
function enterScriptEditMode() {
  editingScript.value = true
  editScriptContent.value = JSON.parse(JSON.stringify(currentScript.value?.content))
}

function cancelScriptEdit() {
  editingScript.value = false
  editScriptContent.value = null
}

async function handleSaveScript() {
  if (!editScriptContent.value || !currentScript.value) return
  savingScript.value = true
  try {
    await scriptsApi.update(currentScript.value.id, editScriptContent.value)
    await fetchScript()
    editingScript.value = false
    message.success('剧本已保存')
  } catch {
    message.error('保存失败')
  } finally {
    savingScript.value = false
  }
}

const OUTLINE_VERSION_COLORS: Record<string, string> = {
  'A': 'error', 'B': 'success', 'C': 'warning',
}

// --- 交互处理 ---
// handleAddChar removed - use handleAddSingleChar instead

async function openAddCharModal() {
  showAddCharModal.value = true
  await fetchAllCharacters()
}

async function handleAddSingleChar(characterId: string) {
  try {
    await projectsApi.addProjectCharacter(projectId, {
      character_id: characterId,
      role_name: charRoleNames.value[characterId] || undefined,
    })
    message.success('角色已添加')
    await fetchProjectCharacters()
    await fetchDashboard()
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '添加失败'
    message.error(detail)
  }
}

async function handleRemoveChar(characterId: string) {
  try {
    await projectsApi.removeProjectCharacter(projectId, characterId)
    message.success('角色已移除')
    await fetchProjectCharacters()
    await fetchDashboard()
  } catch { message.error('移除失败') }
}

async function handleGenerateCharacters(): Promise<boolean> {
  generatingCharacters.value = true
  try {
    await projectsApi.generateCharacters(projectId, getVisualSettingsPayload())
    await fetchProjectCharacters()
    await fetchDashboard()
    message.success('角色生成完成！')
    return true
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    message.error(detail || '角色生成失败，请查看后端日志')
    return false
  } finally {
    generatingCharacters.value = false
  }
}

// handlePresetChange, fetchPresets, handleSaveAsTemplate — provided by useVisualSettings composable

function roleTypeLabel(type: string): string {
  const map: Record<string, string> = { protagonist: '主角', antagonist: '反派', supporting: '配角', minor: '龙套' }
  return map[type] || '角色'
}

function roleTypeColor(type: string): string {
  const map: Record<string, string> = { protagonist: 'success', antagonist: 'error', supporting: 'info', minor: 'default' }
  return map[type] || 'default'
}

function copyPrompt(prompt: string) {
  navigator.clipboard.writeText(prompt).then(() => message.success('提示词已复制')).catch(() => message.error('复制失败'))
}

async function handleGenerateStoryboards() {
  const hasExisting = projectStoryboards.value.length > 0
  const regenerate = hasExisting
  generatingStoryboards.value = true
  try {
    const resp = await projectsApi.generateStoryboards(projectId, regenerate)
    message.success(`已生成 ${resp.data.generated_count} 个分镜`)
    await fetchStoryboards()
    await fetchDashboard()
  } catch (err: any) {
    const detail = err?.response?.data?.detail || '生成分镜失败'
    message.error(detail)
  } finally {
    generatingStoryboards.value = false
  }
}

function openCreateStoryboard() {
  editingStoryboardId.value = null
  storyboardForm.episode_no = 1
  storyboardForm.shot_no = projectStoryboards.value.length + 1
  storyboardForm.shot_type = '中景'
  storyboardForm.camera_move = '固定'
  storyboardForm.action = ''
  storyboardForm.dialogue = ''
  storyboardForm.emotion = ''
  storyboardForm.vfx = '无'
  storyboardForm.environment = ''
  storyboardForm.lighting = ''
  showStoryboardModal.value = true
}

function openEditStoryboard(row: StoryboardResponse) {
  editingStoryboardId.value = row.id
  storyboardForm.episode_no = row.episode_no
  storyboardForm.shot_no = row.shot_no
  storyboardForm.shot_type = row.shot_type
  storyboardForm.camera_move = row.camera_move
  storyboardForm.action = row.action
  storyboardForm.dialogue = row.dialogue || ''
  storyboardForm.emotion = row.emotion
  storyboardForm.vfx = row.vfx || '无'
  storyboardForm.environment = row.environment
  storyboardForm.lighting = row.lighting
  showStoryboardModal.value = true
}

async function handleSaveStoryboard(): Promise<boolean> {
  if (!storyboardForm.action || !storyboardForm.emotion || !storyboardForm.environment || !storyboardForm.lighting) {
    message.warning('请填写必填字段')
    return false
  }
  savingStoryboard.value = true
  try {
    const payload: StoryboardCreate = {
      ...storyboardForm,
      project_id: projectId,
      dialogue: storyboardForm.dialogue || null,
    }
    if (editingStoryboardId.value) {
      await storyboardsApi.update(editingStoryboardId.value, payload)
      message.success('分镜已更新')
    } else {
      await storyboardsApi.create(payload)
      message.success('分镜已创建')
    }
    await fetchStoryboards()
    await fetchDashboard()
    return true
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '保存失败'
    message.error(detail)
    return false
  } finally {
    savingStoryboard.value = false
  }
}

async function handleDeleteStoryboard(row: StoryboardResponse) {
  try {
    await storyboardsApi.delete(row.id)
    message.success('分镜已删除')
    await fetchStoryboards()
    await fetchDashboard()
  } catch { message.error('删除失败') }
}

async function handleRegeneratePrompt(row: StoryboardResponse) {
  regeneratingPromptId.value = row.id
  try {
    const resp = await storyboardsApi.regeneratePrompt(row.id)
    // 直接用响应更新表格行，避免全量刷新
    const idx = projectStoryboards.value.findIndex(s => s.id === row.id)
    if (idx >= 0) projectStoryboards.value[idx] = resp.data
    message.success('提示词已重新生成')
  } catch {
    message.error('生成提示词失败')
  } finally {
    regeneratingPromptId.value = null
  }
}

async function handleEnhancePrompt(row: StoryboardResponse) {
  enhancingPromptId.value = row.id
  try {
    const resp = await storyboardsApi.enhancePrompt(row.id)
    // 后端 enhance-prompt 返回的是 { standard, enhanced, negative_prompt }，不是完整的 StoryboardResponse
    // 需要通过 regeneratePrompt 获取完整数据，或者直接更新行
    const fullResp = await storyboardsApi.getById(row.id)
    const idx = projectStoryboards.value.findIndex(s => s.id === row.id)
    if (idx >= 0) projectStoryboards.value[idx] = fullResp.data
    message.success(`提示词增强成功（增强${resp.data.enhanced.length}字）`)
  } catch {
    message.error('增强失败，请检查 DeepSeek 配置')
  } finally {
    enhancingPromptId.value = null
  }
}

async function handleUpdateDuration(row: StoryboardResponse, val: number) {
  try {
    await storyboardsApi.update(row.id, { duration_seconds: val })
    row.duration_seconds = val
  } catch {
    message.error('更新时长失败')
  }
}

async function handleAutoAssignDurations() {
  autoAssigningDuration.value = true
  try {
    const resp = await storyboardsApi.autoAssignDurations(projectId)
    message.success(resp.data.detail)
    await fetchStoryboards()
  } catch {
    message.error('自动分配时长失败')
  } finally {
    autoAssigningDuration.value = false
  }
}

async function handleRhythmAnalysis() {
  loadingRhythm.value = true
  try {
    const resp = await storyboardsApi.rhythmAnalysis(projectId)
    const data = resp.data
    const lines = [`综合评分: ${data.overall_score}/100`]
    for (const s of data.global_suggestions) {
      lines.push(`· ${s}`)
    }
    for (const [ep, info] of Object.entries(data.per_episode)) {
      lines.push(`\n第${ep}集: ${info.score}/100, ${info.shot_count}镜, ${info.total_duration}s`)
      for (const issue of info.issues) lines.push(`  ⚠ ${issue}`)
      for (const sug of info.suggestions) lines.push(`  💡 ${sug}`)
    }
    rhythmReport.value = lines.join('\n')
    showRhythmModal.value = true
  } catch {
    message.error('节奏分析失败')
  } finally {
    loadingRhythm.value = false
  }
}

function handleCopyRhythmReport() {
  navigator.clipboard.writeText(rhythmReport.value)
  message.success('已复制到剪贴板')
}

async function handleAutoOptimize() {
  optimizingByRhythm.value = true
  try {
    const resp = await projectsApi.optimizeByRhythm(projectId)
    const { total_added, total_modified, changes } = resp.data
    const summary = changes.map(c => `第${c.episode_no}集 镜头${c.shot_no}: ${c.detail}`).join('\n')
    message.success(`优化完成：新增${total_added}个镜头，修改${total_modified}个镜头`)
    if (summary) {
      rhythmReport.value = `=== 优化结果 ===\n新增 ${total_added} 个镜头，修改 ${total_modified} 个镜头\n\n${summary}\n\n=== 原始分析 ===\n${rhythmReport.value}`
    }
    await fetchStoryboards()
  } catch {
    message.error('自动优化失败')
  } finally {
    optimizingByRhythm.value = false
  }
}

async function handleReviewStoryboards() {
  loadingReview.value = true
  try {
    const resp = await projectsApi.reviewStoryboards(projectId)
    reviewReport.value = resp.data
    showReviewModal.value = true
  } catch {
    message.error('审核失败')
  } finally {
    loadingReview.value = false
  }
}

async function handleOptimizeByReview() {
  optimizingByReview.value = true
  try {
    const resp = await projectsApi.optimizeByReview(projectId)
    const { total_added, total_modified } = resp.data
    message.success(`优化完成：新增${total_added}个，修改${total_modified}个镜头`)
    await fetchStoryboards()
    const resp2 = await projectsApi.reviewStoryboards(projectId)
    reviewReport.value = resp2.data
  } catch {
    message.error('优化失败')
  } finally {
    optimizingByReview.value = false
  }
}

async function handleAddClimaxShots() {
  addingClimax.value = true
  try {
    const resp = await projectsApi.addClimaxShots(projectId)
    const { total_added, changes } = resp.data
    if (total_added === 0) {
      message.info('所有集情绪曲线已达标，无需添加')
    } else {
      const detail = changes.map(c => `第${c.episode_no}集 镜头${c.shot_no}: ${c.detail}`).join('\n')
      message.success(`已添加${total_added}个高潮镜头`)
      // 追加到报告
      if (reviewReport.value) {
        reviewReport.value = {
          ...reviewReport.value,
          _climaxResult: `新增 ${total_added} 个高潮镜头：\n${detail}`,
        }
      }
    }
    await fetchStoryboards()
    // 重新审核
    const resp2 = await projectsApi.reviewStoryboards(projectId)
    reviewReport.value = { ...resp2.data, _climaxResult: reviewReport.value?._climaxResult }
  } catch {
    message.error('添加高潮镜头失败')
  } finally {
    addingClimax.value = false
  }
}

async function handleReconstructStoryboards() {
  reconstructing.value = true
  try {
    const resp = await projectsApi.reconstructStoryboardsPreview(projectId)
    reconstructResult.value = resp.data
    showReconstructResult.value = true
    message.info(`预览已生成：${resp.data.total_episodes}集${resp.data.total_shots}镜（原${resp.data.old_shot_count}镜）`)
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '爆款重构预览失败'
    message.error(msg)
  } finally {
    reconstructing.value = false
  }
}

async function handleApplyReconstruct() {
  if (!window.confirm('将覆盖现有分镜（会自动创建备份快照），是否继续？')) return
  applyingReconstruct.value = true
  try {
    const resp = await projectsApi.reconstructStoryboardsApply(projectId)
    reconstructResult.value = resp.data
    message.success(`重构已应用：${resp.data.total_episodes}集${resp.data.total_shots}镜，快照已备份`)
    await fetchStoryboards()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '应用重构失败'
    message.error(msg)
  } finally {
    applyingReconstruct.value = false
  }
}

function handleCopyReview() {
  if (!reviewReport.value) return
  const lines = [`综合评分: ${reviewReport.value.overall_score}/100`]
  for (const s of reviewReport.value.global_suggestions || []) lines.push(`· ${s}`)
  for (const ep of reviewReport.value.episodes || []) {
    lines.push(`\n第${ep.episode}集: ${ep.score}/100, ${ep.shot_count}镜, ${ep.total_duration}s`)
    for (const [dk, dv] of Object.entries(ep.dimensions)) lines.push(`  ${dimLabel(dk)}: ${dv}`)
    for (const i of ep.issues) lines.push(`  ⚠ ${i}`)
    for (const s of ep.suggestions) lines.push(`  💡 ${s}`)
  }
  navigator.clipboard.writeText(lines.join('\n'))
  message.success('已复制到剪贴板')
}

function dimLabel(key: string): string {
  const map: Record<string, string> = {
    emotion_curve: '情绪曲线', hook_density: '钩子密度', ending_suspense: '结尾悬念',
    shot_diversity: '镜头多样性', key_moment_placement: '关键镜头', duration_and_count: '时长数量',
    visual_rhythm: '视觉节奏',
  }
  return map[key] || key
}

const totalDurationText = computed(() => {
  const total = projectStoryboards.value.reduce((sum, s) => sum + (s.duration_seconds || 5), 0)
  return `${total}秒`
})

const episodeDurationSummary = computed(() => {
  const map = new Map<number, { count: number; duration: number }>()
  for (const s of projectStoryboards.value) {
    const ep = s.episode_no
    const cur = map.get(ep) || { count: 0, duration: 0 }
    cur.count++
    cur.duration += s.duration_seconds || 5
    map.set(ep, cur)
  }
  return Array.from(map.entries()).map(([ep, info]) => ({
    episode: ep,
    count: info.count,
    duration: info.duration,
    inRange: info.duration >= 60 && info.duration <= 90,
  }))
})

async function handleUpdate(): Promise<boolean> {
  try {
    const resp = await projectsApi.update(projectId, {
      name: editForm.name || undefined,
      description: editForm.description || undefined,
    })
    project.value = resp.data
    message.success('项目信息已更新')
    return true
  } catch { message.error('更新失败'); return false }
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
  } catch { message.error('加载快照详情失败') }
}

async function handleRestore(snap: SnapshotBriefResponse) {
  try {
    const resp = await projectsApi.restoreSnapshot(projectId, snap.id)
    project.value = resp.data
    message.success('快照已恢复')
    await fetchProject()
    await fetchScript()
    await fetchStoryboards()
  } catch { message.error('恢复快照失败') }
}

function toggleCompare(id: string, checked: boolean) {
  if (checked && compareIds.value.length < 2) compareIds.value.push(id)
  else compareIds.value = compareIds.value.filter(i => i !== id)
}

async function handleCompare() {
  if (compareIds.value.length !== 2) return
  comparing.value = true
  try {
    const resp = await projectsApi.compareSnapshots(projectId, compareIds.value[0], compareIds.value[1])
    compareResult.value = resp.data
    activeTab.value = 'compare'
  } catch { message.error('对比失败') } finally {
    comparing.value = false
  }
}

// --- 参考图管理 ---
function getRefImageCount(pc: ProjectCharacterResponse): number {
  const images = pc.reference_images
  if (!images) return 0
  if (Array.isArray(images)) return images.length
  return 0
}

function parseRefImages(raw: unknown): ReferenceImageItem[] {
  if (!raw || !Array.isArray(raw)) return []
  return raw.map((item: unknown, idx: number) => {
    if (typeof item === 'string') {
      return { id: String(idx), url: item, angle: 'front', pose: 'standing', is_primary: idx === 0, created_at: '' }
    }
    return item as ReferenceImageItem
  })
}

async function openRefImageDrawer(pc: ProjectCharacterResponse) {
  refImageCharId.value = pc.character_id
  refImageCharName.value = pc.character_name
  try {
    const resp = await charactersApi.getById(pc.character_id)
    refImageList.value = parseRefImages(resp.data.reference_images)
  } catch {
    refImageList.value = []
  }
  showRefImageDrawer.value = true
}

function handleUploadRefImage() {
  fileInputRef.value?.click()
}

function onRefImageFileSelected(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  pendingRefFile.value = file
  target.value = ''
  showRefUploadModal.value = true
}

function handleConfirmUpload(): boolean {
  doUploadRefImage()
  return false
}

async function doUploadRefImage() {
  if (!pendingRefFile.value) {
    message.error('请先选择文件')
    showRefUploadModal.value = false
    return
  }
  if (!refImageCharId.value) {
    message.error('角色 ID 缺失')
    showRefUploadModal.value = false
    return
  }
  console.log('[RefImage] Uploading:', pendingRefFile.value.name, pendingRefFile.value.size, 'bytes, charId:', refImageCharId.value)
  try {
    const resp = await charactersApi.uploadReferenceImage(
      refImageCharId.value,
      pendingRefFile.value,
      refUploadAngle.value,
      refUploadPose.value,
      refUploadPrimary.value,
    )
    refImageList.value.push(resp.data)
    message.success('参考图上传成功')
    pendingRefFile.value = null
    showRefUploadModal.value = false
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      || (err as Error)?.message || String(err)
    console.error('[RefImage Upload Error]', err)
    message.error('上传失败: ' + detail)
  }
}

async function handleGeneratePortrait() {
  if (!refImageCharId.value) return
  generatingPortrait.value = true
  try {
    await charactersApi.generatePortrait(refImageCharId.value)
    const charResp = await charactersApi.getById(refImageCharId.value)
    refImageList.value = parseRefImages(charResp.data.reference_images)
    message.success('角色肖像已生成')
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    message.error(detail || '生成失败，请查看后端日志')
  } finally {
    generatingPortrait.value = false
  }
}

async function handleGenerateAnglePrompts() {
  if (!refImageCharId.value) return
  generatingAnglePrompts.value = true
  try {
    const resp = await charactersApi.generateAnglePrompts(refImageCharId.value)
    anglePrompts.value = resp.data
    showAnglePromptsModal.value = true
  } catch {
    message.error('生成提示词失败')
  } finally {
    generatingAnglePrompts.value = false
  }
}

async function handleSetPrimary(imageId: string) {
  if (!refImageCharId.value) return
  try {
    await charactersApi.updateReferenceImage(refImageCharId.value, imageId, { is_primary: true })
    refImageList.value.forEach(img => { img.is_primary = img.id === imageId })
    message.success('已设为主视觉')
  } catch {
    message.error('设置失败')
  }
}

async function handleDeleteRefImage(imageId: string) {
  if (!refImageCharId.value) return
  try {
    const resp = await charactersApi.deleteReferenceImage(refImageCharId.value, imageId)
    refImageList.value = parseRefImages(resp.data.reference_images)
    message.success('参考图已删除')
  } catch {
    message.error('删除失败')
  }
}

function formatDate(dateStr: string) { return new Date(dateStr).toLocaleString('zh-CN') }
function truncate(text: string, max: number) { return text.length > max ? text.slice(0, max) + '...' : text }

// --- 生命周期 ---
onMounted(async () => {
  await fetchProject()
  fetchPresets()
  await Promise.all([
    fetchDashboard(),
    fetchScript(),
    fetchProjectCharacters(),
    fetchStoryboards(),
    fetchSnapshots(),
    fetchNarrativeTree(),
    fetchCreativeHistory(),
    fetchVisualStyle(),
  ])
})
</script>

<style scoped>
.project-workspace {
  max-width: 1200px;
  margin: 0 auto;
}
.narrative-tree {
  padding: 8px 0;
}
</style>
