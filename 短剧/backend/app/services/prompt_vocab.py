"""
Seedance 2.0 视频提示词标准化词汇库。

提供景别、运镜、稳定方式、风格、光照、负面约束等中英文映射，
供 PromptAssembler 生成符合 Seedance 2.0 规范的 prompt。
"""

# ── 景别 ──────────────────────────────────────────────────────
SHOT_TYPES: dict[str, str] = {
    "极特写": "extreme close-up",
    "特写": "close-up",
    "近景": "medium close-up",
    "中景": "medium shot",
    "中远景": "medium long shot",
    "全景": "full shot",
    "远景": "wide shot",
    "大远景": "extreme wide shot",
}

# ── 运镜 ──────────────────────────────────────────────────────
CAMERA_MOVEMENTS: dict[str, str] = {
    "固定": "static tripod",
    "推": "slow push-in",
    "拉": "pull back",
    "左摇": "pan left",
    "右摇": "pan right",
    "上摇": "tilt up",
    "下摇": "tilt down",
    "环绕": "orbit",
    "跟拍": "tracking shot",
    "手持": "handheld",
    "升降": "crane shot",
    "甩镜": "whip pan",
}

# ── 稳定方式 ──────────────────────────────────────────────────
STABILITY: dict[str, str] = {
    "三脚架": "tripod",
    "手持": "handheld",
    "稳定器": "gimbal",
    "滑轨": "slider",
}

# ── 视觉风格 ──────────────────────────────────────────────────
STYLES: dict[str, str] = {
    "电影感": "cinematic",
    "纪录片": "documentary",
    "动漫": "anime",
    "写实": "photorealistic",
    "胶片": "35mm film grain",
    "赛博朋克": "cyberpunk",
    "复古": "vintage retro",
    "梦幻": "dreamy soft focus",
    "暗黑": "dark moody",
    "清新": "bright and airy",
}

# ── 光照 ──────────────────────────────────────────────────────
LIGHTING: dict[str, str] = {
    "自然光": "soft natural light",
    "黄金时刻": "golden hour",
    "蓝调时刻": "blue hour",
    "霓虹": "neon lighting",
    "高调": "high-key lighting",
    "低调": "low-key dramatic lighting",
    "逆光": "backlit silhouette",
    "侧光": "side lighting with shadows",
    "顶光": "overhead lighting",
    "烛光": "warm candlelight",
}

# ── 画面比例 ──────────────────────────────────────────────────
ASPECT_RATIOS: list[str] = ["16:9", "9:16", "4:3", "1:1", "21:9"]

# ── 时长范围（秒）──────────────────────────────────────────────
DURATION_RANGE: tuple[int, int] = (3, 15)

# ── 负面提示模板 ──────────────────────────────────────────────
NEGATIVE_PROMPTS: dict[str, str] = {
    "通用": (
        "no text overlays, no watermarks, no extra characters, "
        "no bent limbs, no distorted hands, no melting edges, "
        "no logos, no jump cuts, no blurry frames"
    ),
    "动作": (
        "no slow motion unless specified, no shaky camera, no blur, "
        "no distorted limbs, no extra characters"
    ),
    "对话": (
        "no lip sync errors, no unnatural expressions, "
        "no frozen face, no extra characters in frame"
    ),
    "特写": (
        "no distorted facial features, no extra fingers, "
        "no blurry details, no text overlays"
    ),
    "远景": (
        "no empty sky, no flat horizon, no overexposure, "
        "no floating objects"
    ),
}

# ── 时长建议映射（按动作复杂度）───────────────────────────────
DURATION_SUGGESTIONS: dict[str, int] = {
    "简单动作": 3,
    "单一动作": 5,
    "复合动作": 7,
    "复杂动作": 10,
}


def resolve_shot(shot_cn: str) -> str:
    return SHOT_TYPES.get(shot_cn, shot_cn)


def resolve_movement(movement_cn: str) -> str:
    return CAMERA_MOVEMENTS.get(movement_cn, movement_cn)


def resolve_stability(stability_cn: str) -> str:
    return STABILITY.get(stability_cn, stability_cn)


def resolve_style(style_cn: str) -> str:
    return STYLES.get(style_cn, style_cn)


def resolve_lighting(lighting_cn: str) -> str:
    return LIGHTING.get(lighting_cn, lighting_cn)


def get_negative_prompt(scene_type: str = "通用") -> str:
    return NEGATIVE_PROMPTS.get(scene_type, NEGATIVE_PROMPTS["通用"])


def clamp_duration(duration: int) -> int:
    lo, hi = DURATION_RANGE
    return max(lo, min(hi, duration))


# ── TTS 音色库（火山引擎豆包）──────────────────────────────────
TTS_VOICES: dict[str, dict[str, str]] = {
    "zh_female_vv_uranus": {
        "label": "女声-温柔知性",
        "gender": "female",
        "language": "zh",
    },
    "zh_male_V_bignews": {
        "label": "男声-沉稳播音",
        "gender": "male",
        "language": "zh",
    },
    "zh_female_lhhai": {
        "label": "女声-活泼可爱",
        "gender": "female",
        "language": "zh",
    },
    "zh_male_chunhou": {
        "label": "男声-醇厚深情",
        "gender": "male",
        "language": "zh",
    },
    "zh_female_qingxin": {
        "label": "女声-清新甜美",
        "gender": "female",
        "language": "zh",
    },
    "zh_male_lengjun": {
        "label": "男声-冷酷低沉",
        "gender": "male",
        "language": "zh",
    },
    "zh_female_gaoleng": {
        "label": "女声-高冷御姐",
        "gender": "female",
        "language": "zh",
    },
    "zh_male_yangguang": {
        "label": "男声-阳光少年",
        "gender": "male",
        "language": "zh",
    },
}


def list_tts_voices() -> list[dict[str, str]]:
    """返回前端可选的音色列表。"""
    return [
        {"id": vid, "label": v["label"], "gender": v["gender"]}
        for vid, v in TTS_VOICES.items()
    ]
