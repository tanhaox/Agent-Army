"""
视频提示词模板 - 融合专业拍摄技巧 + AI视频生成最佳实践。

提供标准版/增强版模板、情绪光影预设、负面提示生成。
"""

import logging

logger = logging.getLogger(__name__)

# ── 景别详细描述 ──────────────────────────────────────────────
SHOT_TYPE_DETAIL_MAP: dict[str, str] = {
    "远景": "extreme wide shot, vast landscape, tiny subject silhouette against environment",
    "全景": "full shot, subject visible from head to toe, establishing spatial context",
    "中景": "medium shot, waist up, balanced composition showing body language and expression",
    "近景": "medium close-up, chest up, facial expression clearly readable",
    "特写": "extreme close-up, shallow depth of field, focusing on fine facial details and micro-expressions",
}

# ── 运镜详细描述 ──────────────────────────────────────────────
CAMERA_MOVE_DETAIL_MAP: dict[str, str] = {
    "固定": "locked-off static camera, stable frame, subject moves within composition",
    "推": "slow deliberate camera push in, gradually tightening framing to intensify emotion",
    "拉": "smooth camera pull out, revealing wider context and environment",
    "摇": "fluid camera pan, horizontal sweep following subject movement",
    "移": "lateral camera tracking shot, parallel movement maintaining consistent framing",
    "跟": "steady camera follow shot, moving with the subject maintaining distance",
}

# ── 情绪光影/色调/节奏预设 ──────────────────────────────────
EMOTION_PRESETS: dict[str, dict[str, str]] = {
    "紧张": {
        "lighting": "high-contrast chiaroscuro, harsh directional light with deep shadows",
        "color": "desaturated cool tones, teal and dark steel blue",
        "atmosphere": "tense oppressive atmosphere, uneasy anticipation",
        "motion": "subtle camera shake, tight framing increasing claustrophobia",
    },
    "恐惧": {
        "lighting": "under-lit, flickering light source, long menacing shadows",
        "color": "cold sickly green-yellow tones, near-monochrome darkness",
        "atmosphere": "dread-filled atmosphere, something lurking beyond the frame",
        "motion": "slow creeping camera movement,揭示 horrific reveals",
    },
    "愤怒": {
        "lighting": "hard red-tinted light, dramatic rim lighting, intense hot spots",
        "color": "deep crimson, burnt orange, dark shadows with red undertones",
        "atmosphere": "explosive volatile energy, air vibrating with rage",
        "motion": "rapid camera push, aggressive framing cuts",
    },
    "悲伤": {
        "lighting": "soft diffused overcast light, gentle backlight with no harsh shadows",
        "color": "muted blue-gray, desaturated melancholic tones",
        "atmosphere": "somber quiet emptiness, weight of sorrow hanging in the air",
        "motion": "slow contemplative camera drift, gentle pull away",
    },
    "喜悦": {
        "lighting": "warm golden sunlight, soft fill light, natural lens flare",
        "color": "bright warm tones, golden yellows and soft whites",
        "atmosphere": "uplifting joyful energy, light and airy feeling",
        "motion": "smooth gentle camera movement, buoyant floating sensation",
    },
    "甜蜜": {
        "lighting": "warm soft bokeh backlight, slight overexposure for dreamy quality",
        "color": "pastel pink, warm peach, soft cream tones",
        "atmosphere": "intimate romantic warmth, tender and gentle mood",
        "motion": "delicate slow camera drift, soft dreamy motion blur",
    },
    "平静": {
        "lighting": "even natural light, soft ambient illumination",
        "color": "balanced neutral tones, gentle earth colors",
        "atmosphere": "serene tranquil mood, stillness and composure",
        "motion": "minimal camera movement, composed and steady framing",
    },
    "期待": {
        "lighting": "warm directional light with long shadows, horizon glow",
        "color": "rich amber, deep gold, warm orange gradient",
        "atmosphere": "anticipation building, something about to happen",
        "motion": "gradual camera reveal, building tension through framing",
    },
    "感动": {
        "lighting": "soft warm backlight with gentle lens flare, ethereal glow",
        "color": "warm golden tones with slight desaturation, nostalgic palette",
        "atmosphere": "emotional weight, bittersweet tenderness",
        "motion": "slow emotional camera hold, lingering on expression",
    },
    "困惑": {
        "lighting": "uneven mixed lighting, conflicting color temperatures",
        "color": "unusual color combinations, slightly off-kilter palette",
        "atmosphere": "disorienting uncertainty, reality slightly warped",
        "motion": "slight Dutch angle, uneasy framing suggests instability",
    },
    "惊喜": {
        "lighting": "bright sudden burst of light, sparkle and lens flare",
        "color": "vibrant saturated colors, joyful vivid palette",
        "atmosphere": "sudden exciting revelation, energy burst",
        "motion": "quick dynamic camera movement, capturing reaction",
    },
}

# ── 情绪默认值（不在预设中的情绪）──────────────────────────────
_DEFAULT_PRESET: dict[str, str] = {
    "lighting": "balanced cinematic lighting",
    "color": "natural color palette",
    "atmosphere": "",
    "motion": "smooth camera work",
}

# ── 负面提示基础词库 ──────────────────────────────────────────
BASE_NEGATIVE_PROMPT = (
    "distorted face, deformed anatomy, extra limbs, blurry, low resolution, "
    "watermark, text overlay, static noise, frame flickering, jittery motion, "
    "unnatural body movement, morphing artifacts, duplicate subjects"
)

MOTION_NEGATIVE = ", stuttering motion, jerky transitions, frame skip, inconsistent motion blur"

IDENTITY_NEGATIVE = ", inconsistent subject appearance, changing face, different clothing mid-scene"


def get_emotion_preset(emotion: str) -> dict[str, str]:
    """获取情绪对应的光影/色调/氛围预设。"""
    return EMOTION_PRESETS.get(emotion, _DEFAULT_PRESET)


def build_standard_prompt(item: dict, visual_settings: dict | None = None) -> str:
    """
    构建标准版视频提示词。

    基于模板拼接，快速可执行，用于测试和预览。
    """
    from app.services.storyboard_service import SHOT_TYPE_MAP, CAMERA_MOVE_MAP

    shot_en = SHOT_TYPE_MAP.get(item.get("shot_type", ""), item.get("shot_type", ""))
    camera_en = CAMERA_MOVE_MAP.get(item.get("camera_move", ""), item.get("camera_move", ""))
    action = item.get("action", "")
    emotion = item.get("emotion", "")
    environment = item.get("environment", "")
    lighting = item.get("lighting", "")
    vfx = item.get("vfx", "无")

    parts = [shot_en, camera_en, action, f"{emotion} emotion"]

    if vfx and vfx != "无":
        parts.append(vfx)

    parts.append(environment)
    parts.append(lighting)

    if visual_settings:
        for key in ("art_style", "color_palette", "render_quality"):
            val = visual_settings.get(key, "")
            if val:
                parts.append(val)

    parts.append("cinematic, 4k, high quality")

    prompt = ", ".join(parts)
    return _clean_prompt(prompt)


def build_enhanced_prompt(item: dict, visual_settings: dict | None = None) -> str:
    """
    构建增强版视频提示词。

    融合专业拍摄技巧：镜头运动细节、光影情绪描述、氛围词、一致性指令。
    """
    shot_type = item.get("shot_type", "中景")
    camera_move = item.get("camera_move", "固定")
    action = item.get("action", "")
    emotion = item.get("emotion", "平静")
    environment = item.get("environment", "")
    lighting = item.get("lighting", "")
    vfx = item.get("vfx", "无")

    # 获取详细描述
    shot_detail = SHOT_TYPE_DETAIL_MAP.get(shot_type, shot_type)
    camera_detail = CAMERA_MOVE_DETAIL_MAP.get(camera_move, camera_move)

    # 获取情绪预设
    preset = get_emotion_preset(emotion)

    # 构建增强版
    sections = []

    # 镜头
    sections.append(f"[Shot]: {shot_detail}, {camera_detail}.")

    # 主体
    sections.append(f"[Subject]: {action}, expressing {emotion}.")

    # 环境+光影+氛围
    env_parts = [environment, lighting]
    if preset.get("lighting"):
        env_parts.append(preset["lighting"])
    if preset.get("atmosphere"):
        env_parts.append(preset["atmosphere"])
    sections.append(f"[Environment]: {', '.join(p for p in env_parts if p)}.")

    # 视觉风格
    style_parts = []
    if visual_settings:
        for key in ("art_style", "color_palette", "render_quality"):
            val = visual_settings.get(key, "")
            if val:
                style_parts.append(val)
    if preset.get("color"):
        style_parts.append(preset["color"])
    if style_parts:
        sections.append(f"[Visual Style]: {', '.join(style_parts)}.")

    # 特效
    if vfx and vfx != "无":
        sections.append(f"[VFX]: {vfx}, seamlessly integrated into scene.")

    # 运动提示
    motion_hint = preset.get("motion", "")
    if motion_hint:
        sections.append(f"[Motion]: {motion_hint}.")

    # 一致性指令
    sections.append("[Guidelines]: Maintain subject identity throughout shot, avoid distortion, smooth natural motion, cinematic depth of field.")

    prompt = " ".join(sections)
    return _clean_prompt(prompt)


def build_negative_prompt(item: dict) -> str:
    """
    根据情绪和特效生成负面提示词。

    包含基础负面词 + 情绪特定负面词 + 运动负面词。
    """
    parts = [BASE_NEGATIVE_PROMPT]

    emotion = item.get("emotion", "")
    preset = get_emotion_preset(emotion)

    # 快速运动时添加运动负面提示
    action = item.get("action", "")
    fast_keywords = ("奔跑", "追赶", "冲出", "打斗", "搏斗", "闪避", "飞起", "跳跃")
    if any(kw in action for kw in fast_keywords):
        parts.append("smooth motion, no stutter" + MOTION_NEGATIVE)

    # 有特殊特征时强调主体一致性
    vfx = item.get("vfx", "无")
    if vfx and vfx != "无":
        parts.append(IDENTITY_NEGATIVE)

    # 情绪特定的负面提示
    emotion_negatives = {
        "紧张": ", flat lighting, bright cheerful colors",
        "恐惧": ", bright well-lit scene, comforting atmosphere",
        "愤怒": ", soft pastel colors, calm serene mood",
        "悲伤": ", vibrant saturated colors, cheerful expressions",
        "甜蜜": ", harsh shadows, cold sterile environment",
    }
    neg = emotion_negatives.get(emotion)
    if neg:
        parts.append(neg)

    return ", ".join(parts)


def _clean_prompt(prompt: str) -> str:
    """清理提示词：去多余空格和逗号。"""
    import re
    prompt = re.sub(r",\s*,", ",", prompt)
    prompt = re.sub(r"\s+", " ", prompt).strip()
    # 确保包含质量词
    if "cinematic" not in prompt.lower():
        prompt += ", cinematic"
    if "4k" not in prompt.lower() and "8k" not in prompt.lower():
        prompt += ", 4k"
    # 限制长度（AI视频生成通常500字符以内）
    if len(prompt) > 500:
        prompt = prompt[:497] + "..."
    return prompt
