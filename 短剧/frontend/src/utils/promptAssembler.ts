/**
 * 前端提示词组装器 — 与后端 prompt_engineering_service.py 保持同步的简化版本。
 *
 * 六步公式：[主体], [动作], in [环境], camera [镜头指令], style [风格], [时长]s, [比例]
 * 用于实时预览，无需请求后端。
 */

// ── 词汇映射（与后端 prompt_vocab.py 同步）────────────────────────

export const SHOT_TYPES: Record<string, string> = {
  极特写: "extreme close-up",
  特写: "close-up",
  近景: "medium close-up",
  中景: "medium shot",
  中远景: "medium long shot",
  全景: "full shot",
  远景: "wide shot",
  大远景: "extreme wide shot",
}

export const CAMERA_MOVEMENTS: Record<string, string> = {
  固定: "static tripod",
  推: "slow push-in",
  拉: "pull back",
  左摇: "pan left",
  右摇: "pan right",
  上摇: "tilt up",
  下摇: "tilt down",
  环绕: "orbit",
  跟拍: "tracking shot",
  手持: "handheld",
  升降: "crane shot",
  甩镜: "whip pan",
}

export const STABILITY: Record<string, string> = {
  三脚架: "tripod",
  手持: "handheld",
  稳定器: "gimbal",
  滑轨: "slider",
}

export const STYLES: Record<string, string> = {
  电影感: "cinematic",
  纪录片: "documentary",
  动漫: "anime",
  写实: "photorealistic",
  胶片: "35mm film grain",
  赛博朋克: "cyberpunk",
  复古: "vintage retro",
  梦幻: "dreamy soft focus",
  暗黑: "dark moody",
  清新: "bright and airy",
}

export const LIGHTING: Record<string, string> = {
  自然光: "soft natural light",
  黄金时刻: "golden hour",
  蓝调时刻: "blue hour",
  霓虹: "neon lighting",
  高调: "high-key lighting",
  低调: "low-key dramatic lighting",
  逆光: "backlit silhouette",
  侧光: "side lighting with shadows",
  顶光: "overhead lighting",
  烛光: "warm candlelight",
}

export const ASPECT_RATIOS = ["16:9", "9:16", "4:3", "1:1", "21:9"]

const NEGATIVE_PROMPTS: Record<string, string> = {
  通用:
    "no text overlays, no watermarks, no extra characters, no bent limbs, no distorted hands, no melting edges, no logos, no jump cuts, no blurry frames",
  动作:
    "no slow motion unless specified, no shaky camera, no blur, no distorted limbs, no extra characters",
  对话:
    "no lip sync errors, no unnatural expressions, no frozen face, no extra characters in frame",
  特写:
    "no distorted facial features, no extra fingers, no blurry details, no text overlays",
  远景:
    "no empty sky, no flat horizon, no overexposure, no floating objects",
}

// ── 类型定义 ──────────────────────────────────────────────────

export interface CameraData {
  shot?: string
  movement?: string
  stability?: string
}

export interface CreativeData {
  subject?: string
  action?: string
  environment?: string
  camera?: CameraData
  style?: string
  lighting?: string
  dialogue?: string
  duration_suggestion?: number
  aspect_ratio?: string
  /** 自定义负面提示 */
  negative_prompt?: string
  /** 参考音频 URL */
  audio_url?: string
}

export interface AssembledResult {
  prompt: string
  negativePrompt: string
}

// ── 组装函数 ──────────────────────────────────────────────────

function resolveShot(shot: string): string {
  return SHOT_TYPES[shot] || shot
}

function resolveMovement(movement: string): string {
  return CAMERA_MOVEMENTS[movement] || movement
}

function resolveStability(stability: string): string {
  return STABILITY[stability] || stability
}

function resolveStyle(style: string): string {
  return STYLES[style] || style
}

function resolveLighting(lighting: string): string {
  return LIGHTING[lighting] || lighting
}

function clampDuration(d: number): number {
  return Math.max(3, Math.min(15, d))
}

function inferSceneType(data: CreativeData): string {
  const shot = data.camera?.shot || ""
  const action = data.action || ""
  const dialogue = data.dialogue || ""

  if (shot === "极特写" || shot === "特写") return "特写"
  if (shot === "远景" || shot === "大远景") return "远景"
  if (dialogue) return "对话"
  if (/跑|打|追|跳|摔|飞/.test(action)) return "动作"
  return "通用"
}

function buildCameraBlock(camera?: CameraData): string {
  const parts: string[] = []
  if (camera?.stability) parts.push(resolveStability(camera.stability))
  if (camera?.movement) parts.push(resolveMovement(camera.movement))
  if (camera?.shot) parts.push(resolveShot(camera.shot))
  return parts.join(", ")
}

function buildStyleBlock(data: CreativeData): string {
  const parts: string[] = []
  if (data.style) parts.push(`style ${resolveStyle(data.style)}`)
  if (data.lighting) parts.push(resolveLighting(data.lighting))
  return parts.join(", ")
}

function clean(text: string): string {
  return text.replace(/,\s*,/g, ",").replace(/\s+/g, " ").replace(/^[,\s]+|[,\s]+$/g, "")
}

/**
 * 六步公式组装 prompt。
 *
 * 输出格式：主体, 动作, in 环境, camera [镜头指令], style [风格], [时长]s, [比例]
 */
export function assembleSixStep(data: CreativeData): string {
  const segments: string[] = []

  if (data.subject) segments.push(data.subject.trim().replace(/[,.\s]+$/, ""))
  if (data.action) segments.push(data.action.trim().replace(/[,.\s]+$/, ""))
  if (data.environment) segments.push(`in ${data.environment.trim().replace(/[,.\s]+$/, "")}`)

  const cameraBlock = buildCameraBlock(data.camera)
  if (cameraBlock) segments.push(`camera ${cameraBlock}`)

  const styleBlock = buildStyleBlock(data)
  if (styleBlock) segments.push(styleBlock)

  const duration = clampDuration(data.duration_suggestion || 5)
  const ratio = ASPECT_RATIOS.includes(data.aspect_ratio || "") ? data.aspect_ratio! : "9:16"

  segments.push(`${duration}s`)
  segments.push(ratio)

  return clean(segments.join(", "))
}

/**
 * 生成负面提示词。
 */
export function buildNegativePrompt(data: CreativeData): string {
  const sceneType = inferSceneType(data)
  const base = NEGATIVE_PROMPTS[sceneType] || NEGATIVE_PROMPTS["通用"]
  if (data.negative_prompt) {
    return `${base}, ${data.negative_prompt}`
  }
  return base
}

/**
 * 音画同步：根据对话和参考音频追加同步描述。
 */
export function addAudioSync(basePrompt: string, dialogue: string, audioUrl?: string): string {
  if (!dialogue && !audioUrl) return basePrompt

  const suffixes: string[] = []

  if (dialogue) {
    const snippet = dialogue.slice(0, 80)
    suffixes.push(
      `As the character says "${snippet}", the lip movements sync naturally, facial expression matches the emotion.`
    )
  }

  if (audioUrl) {
    suffixes.push("Audio reference provided, sync with the voiceover.")
  }

  return suffixes.length ? basePrompt + " " + suffixes.join(" ") : basePrompt
}

/**
 * 完整组装：prompt + negativePrompt + 音画同步。
 */
export function assemblePrompt(data: CreativeData): AssembledResult {
  let prompt = assembleSixStep(data)

  if (data.dialogue || data.audio_url) {
    prompt = addAudioSync(prompt, data.dialogue || "", data.audio_url)
  }

  return {
    prompt,
    negativePrompt: buildNegativePrompt(data),
  }
}
