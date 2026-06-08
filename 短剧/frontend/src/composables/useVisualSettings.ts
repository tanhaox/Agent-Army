/**
 * 视觉设置 composable — 从 ProjectWorkspace 中提取的视觉风格逻辑。
 *
 * 管理视觉风格参数、模板预设、风格参考图等。
 */

import { ref, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import type { SelectOption } from 'naive-ui'
import {
  ART_STYLE_OPTIONS, ERA_OPTIONS, ENVIRONMENT_OPTIONS, COLOR_PALETTE_OPTIONS,
  LIGHTING_OPTIONS, toGroupedOptions,
} from '../constants/visualOptions'
import { visualTemplatesApi, type VisualTemplate } from '../api/projects'
import { getVisualStyle, updateVisualStyle, uploadStyleReference } from '../api/visualStyles'

export function useVisualSettings(projectId: string) {
  const message = useMessage()

  // ── 视觉设定 ──
  const generatingCharacters = ref(false)
  const showVisualSettingsModal = ref(false)
  const selectedPresetId = ref<string | null>(null)
  const advancedMode = ref(false)
  const templateList = ref<VisualTemplate[]>([])
  const savingTemplate = ref(false)

  const visualSettings = reactive({
    art_style: [] as string[],
    era: '',
    environment: [] as string[],
    color_palette: [] as string[],
    lighting: [] as string[],
    camera_angle: '中景平视',
    render_quality: '精细4K电影级',
    global_note: '',
    cultural_style: 'east_asian',
  })

  const artStyleOptions = toGroupedOptions(ART_STYLE_OPTIONS)
  const eraOptions = toGroupedOptions(ERA_OPTIONS)
  const environmentOptions = toGroupedOptions(ENVIRONMENT_OPTIONS)
  const colorPaletteOptions = toGroupedOptions(COLOR_PALETTE_OPTIONS)
  const lightingOptions = toGroupedOptions(LIGHTING_OPTIONS)
  const cameraAngleOptions: SelectOption[] = [
    { label: '中景平视', value: '中景，平视' },
    { label: '中景俯拍', value: '中景，微俯拍' },
    { label: '仰拍', value: '戏剧性低角度仰拍' },
    { label: '特写', value: '特写，浅景深' },
    { label: '全景', value: '全景建立镜头' },
  ]
  const renderQualityOptions: SelectOption[] = [
    { label: '4K电影', value: '精细4K电影级' },
    { label: 'UE5 8K', value: '虚幻引擎5，8K，光线追踪' },
    { label: '高清插画', value: '高质量数字插画' },
    { label: '胶片质感', value: '胶片颗粒感，模拟摄影美学' },
  ]
  const culturalStyleOptions: SelectOption[] = [
    { label: '东亚（默认）', value: 'east_asian' },
    { label: '西方', value: 'western' },
    { label: '日本', value: 'japanese' },
    { label: '韩国', value: 'korean' },
  ]

  // ── 视觉风格锁定 ──
  const loadingVisualStyle = ref(false)
  const savingVisualStyle = ref(false)
  const visualStyle = reactive({
    style_reference_image: null as string | null,
    color_palette: null as string[] | null,
    lighting_rule: null as string | null,
    camera_style: null as string | null,
    art_style: null as string | null,
  })
  const lightingRuleOptions: SelectOption[] = [
    { label: '自然光', value: '自然光' },
    { label: '黄金时刻', value: '黄金时刻' },
    { label: '蓝调时刻', value: '蓝调时刻' },
    { label: '霓虹', value: '霓虹' },
    { label: '电影布光', value: '电影布光' },
    { label: '暗调', value: '暗调' },
    { label: '高调', value: '高调' },
    { label: '逆光', value: '逆光' },
  ]
  const cameraStyleOptions: SelectOption[] = [
    { label: '稳定', value: '稳定' },
    { label: '手持', value: '手持' },
    { label: '运动', value: '运动' },
    { label: '环绕', value: '环绕' },
  ]

  // ── 方法 ──

  async function fetchVisualStyle() {
    loadingVisualStyle.value = true
    try {
      const data = await getVisualStyle(projectId)
      Object.assign(visualStyle, data)
    } catch (e: any) {
      message.warning('获取视觉风格失败: ' + (e.message || '未知错误'))
    } finally {
      loadingVisualStyle.value = false
    }
  }

  async function handleSaveVisualStyle() {
    savingVisualStyle.value = true
    try {
      const data = await updateVisualStyle(projectId, {
        art_style: visualStyle.art_style,
        color_palette: visualStyle.color_palette,
        lighting_rule: visualStyle.lighting_rule,
        camera_style: visualStyle.camera_style,
      })
      Object.assign(visualStyle, data)
      message.success('视觉风格已保存')
    } catch (e: any) {
      message.error('保存失败: ' + (e.message || '未知错误'))
    } finally {
      savingVisualStyle.value = false
    }
  }

  async function handleUploadStyleRef({ file }: any) {
    try {
      const data = await uploadStyleReference(projectId, file.file)
      visualStyle.style_reference_image = data.style_reference_image
      message.success('风格参考图已上传')
    } catch (e: any) {
      message.error('上传失败: ' + (e.message || '未知错误'))
    }
  }

  async function handleRemoveStyleRef() {
    try {
      const data = await updateVisualStyle(projectId, { style_reference_image: null })
      visualStyle.style_reference_image = data.style_reference_image
      message.success('参考图已移除')
    } catch (e: any) {
      message.error('移除失败: ' + (e.message || '未知错误'))
    }
  }

  function handleApplyCurrentVisualSettings() {
    if (visualSettings.art_style?.length) {
      visualStyle.art_style = visualSettings.art_style.join('，')
    }
    if (visualSettings.color_palette?.length) {
      visualStyle.color_palette = [...visualSettings.color_palette]
    }
    if (visualSettings.lighting?.length) {
      visualStyle.lighting_rule = visualSettings.lighting.join('，')
    }
    message.info('已从当前视觉设定填入')
  }

  const MULTI_FIELDS = new Set(['art_style', 'environment', 'color_palette', 'lighting'])

  function splitToArr(val: unknown): string[] {
    if (Array.isArray(val)) return val
    if (typeof val === 'string' && val.trim()) return val.split(/[，,]/).map(s => s.trim()).filter(Boolean)
    return []
  }

  function handlePresetChange(templateId: string | null) {
    if (!templateId) return
    const tpl = templateList.value.find(t => t.id === templateId)
    if (!tpl) return
    const s = tpl.settings
    for (const key of Object.keys(s)) {
      if (MULTI_FIELDS.has(key)) {
        (visualSettings as any)[key] = splitToArr(s[key])
      } else {
        (visualSettings as any)[key] = s[key]
      }
    }
  }

  async function fetchPresets() {
    try {
      const resp = await visualTemplatesApi.list()
      templateList.value = resp.data
    } catch { /* ignore */ }
  }

  async function handleSaveAsTemplate() {
    savingTemplate.value = true
    try {
      const name = prompt('请输入模板名称：')
      if (!name) return
      const tplSettings: Record<string, string> = {}
      for (const [k, v] of Object.entries(visualSettings)) {
        tplSettings[k] = Array.isArray(v) ? v.join('，') : (v as string)
      }
      await visualTemplatesApi.create({ name, settings: tplSettings })
      await fetchPresets()
      message.success('模板已保存')
    } catch {
      message.error('保存模板失败')
    } finally {
      savingTemplate.value = false
    }
  }

  function getVisualSettingsPayload(): Record<string, string> {
    const payload: Record<string, string> = {}
    for (const [k, v] of Object.entries(visualSettings)) {
      payload[k] = Array.isArray(v) ? v.join('，') : (v as string)
    }
    return payload
  }

  return {
    // State
    generatingCharacters, showVisualSettingsModal, selectedPresetId,
    advancedMode, templateList, savingTemplate, visualSettings,
    loadingVisualStyle, savingVisualStyle, visualStyle,
    // Options
    artStyleOptions, eraOptions, environmentOptions,
    colorPaletteOptions, lightingOptions, cameraAngleOptions,
    renderQualityOptions, culturalStyleOptions,
    lightingRuleOptions, cameraStyleOptions,
    // Actions
    fetchVisualStyle, handleSaveVisualStyle,
    handleUploadStyleRef, handleRemoveStyleRef,
    handleApplyCurrentVisualSettings, handlePresetChange,
    fetchPresets, handleSaveAsTemplate, getVisualSettingsPayload,
  }
}
