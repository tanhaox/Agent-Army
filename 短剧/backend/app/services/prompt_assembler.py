"""
角色图片提示词组装引擎。

职责：
- 根据 cultural_style 动态生成人种描述和服装风格
- 将 LLM 返回的结构化角色数据组装为精确的 image_prompt
- 自动生成 negative_prompt（根据文化风格动态调整禁止项）
- 后处理校验，自动修正危险模式
"""

import logging
import re

logger = logging.getLogger(__name__)

# ==================== 文化风格配置 ====================

CULTURAL_STYLE_MAP: dict[str, dict] = {
    "east_asian": {
        "race_prefix": "东亚中国人",
        "features_hint": "单眼皮或内双，黑发，暖黄色调肤色",
        "era_clothing": {
            "modern": "现代中国都市日常服饰",
            "ancient": "传统汉服或道袍",
            "near_future": "中式赛博朋克街头装",
            "cyberpunk": "港风霓虹街头风格，中式赛博服装",
            "fantasy": "中式仙侠古装",
            "post_apocalyptic": "末日中式生存装备",
        },
        "negative_forbidden": (
            "白人, 西方人, 欧美人, 非裔, 拉丁裔, "
            "牛仔帽, 燕尾服, 西装, 欧式中世纪铠甲, "
            "和服, 韩服, 金发, 蓝眼, 欧美面孔"
        ),
        "system_prompt_hint": (
            "所有角色均为东亚/中国人种，服装必须符合中国背景。"
            "appearance 用中文描述东亚人种特征：黑/深棕发色、黄色皮肤、东亚五官。"
            "clothing 用中文描述中国风格服饰：现代→中国都市服饰；古代→汉服/古装；赛博朋克→中式赛博街头装。"
            "禁止出现西装、晚礼服、牛仔帽、欧式铠甲、和服、韩服等非中国元素。"
            "所有字段值必须使用中文。"
        ),
    },
    "western": {
        "race_prefix": "Caucasian Western",
        "features_hint": "diverse eye and hair colors, light to medium skin tone",
        "era_clothing": {
            "modern": "Western casual wear, jeans, leather jacket, hoodie",
            "ancient": "medieval European armor or robes",
            "near_future": "Western sci-fi tactical gear",
            "cyberpunk": "Blade Runner inspired Western cyberpunk fashion",
            "fantasy": "Western fantasy armor or wizard robes",
            "post_apocalyptic": "post-apocalyptic Western survivor gear",
        },
        "negative_forbidden": (
            "East Asian, Chinese, Japanese, Korean, monolid, hanfu, qipao, "
            "kimono, hanbok, daoist robe"
        ),
        "system_prompt_hint": (
            "All characters are Caucasian/Western ethnicity. "
            "Clothing should reflect Western fashion appropriate to the setting. "
            "Prohibit: hanfu, qipao, kimono, hanbok, daoist robes."
        ),
    },
    "japanese": {
        "race_prefix": "Japanese",
        "features_hint": "typically dark straight hair, fair skin, distinct Japanese features",
        "era_clothing": {
            "modern": "Japanese street fashion, Harajuku style, school uniform",
            "ancient": "traditional Japanese kimono or samurai armor",
            "near_future": "Japanese anime cyberpunk fashion",
            "cyberpunk": "Tokyo neon street style, techwear",
            "fantasy": "Japanese fantasy attire, shrine maiden or oni gear",
            "post_apocalyptic": "Japanese post-apocalyptic survivor wear",
        },
        "negative_forbidden": "Western, Chinese hanfu, Korean hanbok, Caucasian",
        "system_prompt_hint": (
            "All characters are Japanese ethnicity. "
            "Clothing should reflect Japanese fashion. "
            "Prohibit: Chinese hanfu, Korean hanbok, Western suits."
        ),
    },
    "korean": {
        "race_prefix": "Korean",
        "features_hint": "typically dark hair, fair skin, Korean facial features",
        "era_clothing": {
            "modern": "Korean fashion, K-style streetwear, minimal chic",
            "ancient": "traditional Korean hanbok",
            "near_future": "Korean futuristic fashion",
            "cyberpunk": "Seoul neon street style",
            "fantasy": "Korean fantasy sageuk attire",
            "post_apocalyptic": "Korean post-apocalyptic gear",
        },
        "negative_forbidden": "Western, Chinese hanfu, Japanese kimono, Caucasian",
        "system_prompt_hint": (
            "All characters are Korean ethnicity. "
            "Clothing should reflect Korean fashion. "
            "Prohibit: Chinese hanfu, Japanese kimono, Western suits."
        ),
    },
}

# 通用负面提示（所有风格共享）
_BASE_NEGATIVE = (
    "runes on face, face tattoos, excessive markings, disfigured face, "
    "ugly, deformed, blurry, low quality, watermark, text, signature"
)

# 需要自动替换的危险正则模式
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"chaotic\s+patterns\s+on\s+face", "chaotic patterns only in pupils"),
    (r"runes\s+(all\s+)?over\s+face", "runes only on forehead center"),
    (r"marks?\s+on\s+cheeks?\s+and\s+nose", ""),
    (r"face\s+covered\s+with\s+\w+", "clean face, no facial marks"),
    (r"facial\s+tattoos?", "no facial tattoos"),
    (r"glowing\s+patterns\s+on\s+skin", "subtle glow only on specified area"),
]

# 部位关键词 → 禁止扩散描述
_BODY_PART_GUARDS: dict[str, str] = {
    "瞳孔": "no patterns outside pupils, clean face",
    "额头": "no marks on cheeks or nose, clean skin",
    "眼睛": "no patterns around eyes",
    "手臂": "no marks on hands or torso",
    "背部": "no marks on chest or arms",
}


def get_cultural_style(style_key: str) -> dict:
    """获取文化风格配置，不存在则返回默认东亚。"""
    return CULTURAL_STYLE_MAP.get(style_key, CULTURAL_STYLE_MAP["east_asian"])


def build_character_description(
    character: dict,
    era: str = "modern",
    cultural_style: str = "east_asian",
) -> str:
    """
    组装角色基础描述：人种前缀 + 外貌 + 服饰 + 特殊特征。

    根据 cultural_style 动态选择人种前缀和服装引导。
    """
    style = get_cultural_style(cultural_style)
    parts: list[str] = [style["race_prefix"]]

    appearance = character.get("appearance", "")
    if appearance:
        parts.append(appearance)

    clothing = character.get("clothing", "")
    if clothing:
        hint = style["era_clothing"].get(era, "")
        if hint:
            parts.append(f"穿着{clothing}，{hint}")
        else:
            parts.append(f"穿着{clothing}")

    special = character.get("special_features", "")
    if special:
        parts.append(special)

    desc = "，".join(parts)
    desc = re.sub(r"，\s*，", "，", desc)
    desc = re.sub(r"\s+", " ", desc).strip()
    return desc


def assemble_image_prompt(
    character_desc: str,
    action_expr: str,
    visual_settings: dict[str, str],
) -> str:
    """模板化组装完整正向提示词。character_desc 已包含人种前缀。"""
    segments = [character_desc.strip().rstrip(",.")]

    if action_expr:
        segments.append(action_expr.strip().rstrip(",."))

    for key in ("environment", "lighting", "camera_angle", "art_style", "color_palette", "render_quality"):
        val = visual_settings.get(key, "")
        if val:
            segments.append(val.strip().rstrip(",."))

    global_note = visual_settings.get("global_note", "")
    if global_note:
        segments.append(global_note.strip().rstrip(",."))

    prompt = ", ".join(segments)
    prompt = re.sub(r",\s*,", ",", prompt)
    prompt = re.sub(r"\s+", " ", prompt).strip()
    return prompt


def build_negative_prompt(
    character: dict,
    cultural_style: str = "east_asian",
) -> str:
    """
    根据文化风格和角色特征自动生成负面提示。

    通用禁止项 + 文化特定禁止项 + 部位扩散禁止项。
    """
    style = get_cultural_style(cultural_style)
    parts = [_BASE_NEGATIVE, style["negative_forbidden"]]

    special = character.get("special_features", "")
    for body_part, guard in _BODY_PART_GUARDS.items():
        if body_part in special:
            parts.append(guard)

    result = ", ".join(parts)
    items = [s.strip() for s in result.split(",") if s.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        low = item.lower()
        if low not in seen:
            seen.add(low)
            unique.append(item)

    return ", ".join(unique)


def validate_and_fix_prompt(prompt: str) -> str:
    """后处理校验：检查危险模式，自动修正。"""
    fixed = prompt
    for pattern, replacement in FORBIDDEN_PATTERNS:
        match = re.search(pattern, fixed, flags=re.IGNORECASE)
        new_text = re.sub(pattern, replacement, fixed, flags=re.IGNORECASE)
        if new_text != fixed and match:
            logger.info("提示词修正: '%s' → '%s'", match.group(0), replacement or "(removed)")
            fixed = new_text

    fixed = re.sub(r",\s*,", ",", fixed)
    fixed = re.sub(r"\s+", " ", fixed).strip()
    return fixed.strip(", ")
