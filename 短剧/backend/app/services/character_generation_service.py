"""
角色自动生成服务 - 根据剧本内容分析角色并生成图片提示词。

职责：
- 提取剧本中出现的角色
- 为每个角色生成性格、外貌、服饰描述
- 使用模板化 prompt 确保格式一致
- 全局视觉设定保证跨角色风格统一
- 支持生成角色合照 prompt
"""

import json
import logging
import re
from typing import Any

from app.services.llm import get_llm_client, LLMConnectionError, LLMGenerateError
from app.services.visual_presets import build_consistency_block, get_default_settings

logger = logging.getLogger(__name__)

# 角色生成的系统提示词
_SYSTEM_PROMPT = """你是一位专业的短剧角色设计师。用户会给你一部短剧的完整剧本内容，请你分析剧本中出现的所有角色。

⚠️ 严重警告：所有字段值必须使用中文！appearance、clothing、personality、special_features、action_expression 每一个字段都必须用中文填写。
如果你输出英文内容，系统将直接报错。请确保每个字段都是中文。

你必须且只能输出一个合法的 JSON 数组，不要输出任何其他文字、解释或 markdown 代码块标记。

直接以 [ 开头，以 ] 结尾。

JSON 数组中每个元素的结构如下（严格使用以下英文字段名，但字段值必须全部使用中文）：

[
  {{
    "name": "角色名（中文）",
    "role_type": "protagonist / antagonist / supporting / minor",
    "personality": "中文性格描述，20字内",
    "appearance": "中文外貌描述，50-80字。必须包含：性别、年龄感、发型发色（黑色或深棕色）、肤色（黄色）、东亚五官特征（内双或单眼皮、黑色瞳孔、颧骨、下颌线）、体型。全部用中文，禁止英文。",
    "clothing": "中文服饰描述，30-60字。必须是中国风格服装。现代剧：卫衣、T恤、休闲装、外卖服、工装等。古装/仙侠：汉服、道袍、古风长衫等。赛博朋克：港风霓虹街头装。全部用中文，禁止英文。",
    "special_features": "中文特殊特征描述。无特殊特征填空字符串。",
    "action_expression": "中文动作/表情提示"
  }}
]

示例（注意全部中文）：
{{
  "name": "林夕",
  "role_type": "protagonist",
  "personality": "外表冷漠内心温柔，做事果断",
  "appearance": "女性，约25岁，黑色长发及腰，鹅蛋脸，柳叶眉，内双杏眼，黑色瞳孔，小挺鼻，薄唇，暖黄色调肤色，身高165cm，纤细身材",
  "clothing": "穿着米白色针织毛衣搭配卡其色阔腿裤，脚踩白色帆布鞋，简约文艺风格",
  "special_features": "",
  "action_expression": "微低头，双手捧着一杯咖啡，眼神若有所思"
}}

分析规则：
1. 从对话、动作描述中识别所有角色（包括龙套）
2. role_type 分类：protagonist（主角）、antagonist（反派）、supporting（重要配角）、minor（龙套）
3. appearance 必须用中文描述，包含性别、年龄、发型、肤色、五官、体型。禁止英文，禁止金发蓝眼。
4. clothing 必须用中文描述中国风格服饰。禁止英文，禁止西装等非中国元素。
5. special_features 用中文，精确限定部位。无特征填 ""。
6. action_expression 用中文描述姿态和表情。

🔴 最后再次强调：appearance、clothing、personality、special_features、action_expression 全部必须用中文填写！禁止输出任何英文描述内容！"""

# 视觉设定推断提示词（扩展版）
_VISUAL_SETTINGS_PROMPT = """你是一位短剧美术风格顾问。根据以下剧本内容，推断最适合的视觉风格设定。

请输出一个 JSON 对象（不要其他文字）：

{
  "art_style": "画风，中文，如 动漫风格、半写实、中国水墨画风",
  "era": "时代感（modern / ancient / near_future / cyberpunk / fantasy / post_apocalyptic）",
  "environment": "环境描述，中文，如 霓虹灯闪烁的城市街道，古代宫殿，校园",
  "lighting": "光照风格，中文，如 暖色柔光，明暗对比布光，霓虹辉光",
  "color_palette": "色调，中文，如 粉色与暖金色，低饱和橙色与灰色",
  "camera_angle": "相机角度，中文，如 中景微俯拍，戏剧性低角度",
  "render_quality": "渲染质量，中文，如 精细4K电影级，虚幻引擎5光线追踪8K",
  "global_note": "全局一致性备注，中文"
}"""


class CharacterGenerationError(Exception):
    """角色生成失败时抛出。"""


def _extract_json_array(text: str) -> str:
    """从 AI 响应中提取 JSON 数组。"""
    text_stripped = text.strip()
    if text_stripped.startswith("["):
        return text_stripped
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text_stripped)
    if code_block_match:
        return code_block_match.group(1).strip()
    bracket_match = re.search(r"\[[\s\S]*\]", text_stripped)
    if bracket_match:
        return bracket_match.group(0)
    raise CharacterGenerationError(
        f"无法从 AI 响应中提取 JSON 数组。原始响应前200字：{text_stripped[:200]}"
    )


def _extract_json_object(text: str) -> str:
    """从 AI 响应中提取 JSON 对象。"""
    text_stripped = text.strip()
    if text_stripped.startswith("{"):
        return text_stripped
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text_stripped)
    if code_block_match:
        return code_block_match.group(1).strip()
    brace_match = re.search(r"\{[\s\S]*\}", text_stripped)
    if brace_match:
        return brace_match.group(0)
    raise CharacterGenerationError(
        f"无法从 AI 响应中提取 JSON 对象。原始响应前200字：{text_stripped[:200]}"
    )


def _serialize_script_for_prompt(script_content: dict[str, Any]) -> str:
    """将剧本内容序列化为适合 LLM 分析的文本格式。"""
    parts: list[str] = []
    title = script_content.get("title", "未命名剧本")
    parts.append(f"剧本名：{title}")
    episodes = script_content.get("episodes", [])
    parts.append(f"总集数：{len(episodes)}\n")

    for ep in episodes:
        ep_no = ep.get("episode", 1)
        hook = ep.get("hook", "")
        parts.append(f"=== 第 {ep_no} 集 ===")
        if hook:
            parts.append(f"开篇钩子：{hook}")
        for scene in ep.get("scenes", []):
            action = scene.get("action", "")
            dialogue = scene.get("dialogue", "")
            if action:
                parts.append(f"  动作：{action}")
            if dialogue:
                parts.append(f"  对话：{dialogue}")
        cliffhanger = ep.get("cliffhanger", "")
        if cliffhanger:
            parts.append(f"结尾悬念：{cliffhanger}")
        parts.append("")

    return "\n".join(parts)


def _normalize_settings(settings: dict[str, str] | None) -> dict[str, str]:
    """确保视觉设定包含所有必要字段，缺失的使用默认值。"""
    defaults = get_default_settings()
    if not settings:
        return defaults
    for key, default_val in defaults.items():
        if key not in settings or not settings[key]:
            settings[key] = default_val
    return settings


def _is_mostly_english(text: str) -> bool:
    """检测文本是否主要是英文（英文字母占比 > 40%）。"""
    if not text:
        return False
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    total = sum(1 for c in text if c.isalpha())
    if total == 0:
        return False
    return ascii_letters / total > 0.4


async def _translate_fields_to_chinese(
    client: Any,
    characters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """检测角色字段中的英文内容，调用 LLM 翻译为中文。"""
    fields_to_check = ("appearance", "clothing", "personality", "action_expression")
    need_translate = []
    for idx, char in enumerate(characters):
        for field in fields_to_check:
            val = char.get(field, "")
            if val and _is_mostly_english(val):
                need_translate.append((idx, field, val))

    if not need_translate:
        return characters

    logger.warning("检测到 %d 个字段含英文内容，调用 LLM 翻译", len(need_translate))

    # 构建翻译请求
    items_text = ""
    for i, (idx, field, val) in enumerate(need_translate):
        items_text += f"\n{i+1}. [{field}] {val}"

    translate_prompt = (
        f"请将以下角色描述翻译为中文。保持原有含义，但用中文表达。"
        f"每行格式：序号. [字段名] 中文翻译\n\n{items_text}\n\n"
        f"直接输出翻译结果，不要解释。"
    )

    translate_system = "你是翻译助手，将英文角色描述翻译为中文。只输出翻译结果。"

    try:
        raw = await client.generate(translate_prompt, system=translate_system)
        lines = raw.strip().split("\n")
        for i, (idx, field, _) in enumerate(need_translate):
            if i < len(lines):
                # 解析 "1. [appearance] 中文翻译" 格式
                line = lines[i].strip()
                # 去掉序号和字段名前缀
                match = re.match(r"\d+\.\s*\[\w+\]\s*(.*)", line)
                if match and match.group(1):
                    characters[idx][field] = match.group(1).strip()
                    logger.info("翻译字段 %s[%s] 成功", characters[idx].get("name", ""), field)
    except Exception as e:
        logger.warning("翻译失败: %s，保留原始内容", e)

    return characters


def _assemble_image_prompt(
    subject: str,
    expression: str,
    settings: dict[str, str],
) -> str:
    """
    使用模板组装完整的 image_prompt。

    模板：{subject}, {expression}, {environment}, {lighting}, {camera_angle},
           {art_style}, {color_palette}, {render_quality}, {global_note}
    """
    parts = [subject.strip().rstrip(",.")]
    if expression:
        parts.append(expression.strip().rstrip(",."))

    # 一致性块：所有角色共享
    consistency = build_consistency_block(settings)
    if consistency:
        parts.append(consistency)

    prompt = ", ".join(parts)
    # 清理多余逗号和空格
    prompt = re.sub(r",\s*,", ",", prompt)
    prompt = re.sub(r"\s+", " ", prompt).strip()
    return prompt


async def infer_visual_settings(script_content: dict[str, Any]) -> dict[str, str]:
    """
    根据剧本内容推断视觉风格设定（扩展版）。

    Returns:
        包含 art_style, era, environment, lighting, color_palette,
        camera_angle, render_quality, global_note 的字典。
    """
    client = get_llm_client()
    script_text = _serialize_script_for_prompt(script_content)

    user_prompt = (
        f"请根据以下短剧剧本内容，推断最适合的视觉风格：\n\n"
        f"{script_text[:3000]}\n\n"
        f"请直接输出 JSON 对象。"
    )

    logger.info("推断视觉设定: 剧本长度=%d", len(script_text))
    raw = await client.generate(user_prompt, system=_VISUAL_SETTINGS_PROMPT)
    json_str = _extract_json_object(raw)
    json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

    try:
        settings = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("视觉设定 JSON 解析失败: %s，使用默认值", e)
        return get_default_settings()

    logger.info("视觉设定推断完成: %s", settings)
    return _normalize_settings(settings)


async def generate_characters_from_script(
    script_content: dict[str, Any],
    visual_settings: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """
    根据剧本内容自动生成角色设计（模板化 prompt + 一致性约束）。

    Args:
        script_content: 剧本 content JSON。
        visual_settings: 可选的视觉设定。不提供则自动推断。

    Returns:
        角色列表。
    """
    client = get_llm_client()

    # 推断或补全视觉设定
    if not visual_settings:
        visual_settings = await infer_visual_settings(script_content)
    visual_settings = _normalize_settings(visual_settings)

    script_text = _serialize_script_for_prompt(script_content)

    user_prompt = (
        f"视觉基调：{json.dumps(visual_settings, ensure_ascii=False)}\n\n"
        f"请分析以下剧本中的所有角色：\n\n"
        f"{script_text[:4000]}\n\n"
        f"请直接输出 JSON 数组。"
    )

    logger.info("开始从剧本生成角色: 剧本长度=%d, 文化风格=%s", len(script_text), visual_settings.get("cultural_style", "east_asian"))

    # 根据文化风格动态调整系统提示词
    from app.services.prompt_assembler import get_cultural_style
    cultural_style = visual_settings.get("cultural_style", "east_asian")
    style_info = get_cultural_style(cultural_style)
    system_prompt = _SYSTEM_PROMPT + "\n\n" + style_info["system_prompt_hint"]

    raw = await client.generate(user_prompt, system=system_prompt)

    json_str = _extract_json_array(raw)
    json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

    try:
        characters = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise CharacterGenerationError(
            f"角色列表 JSON 解析失败: {e}. 原始内容前200字：{json_str[:200]}"
        ) from e

    if not isinstance(characters, list) or len(characters) == 0:
        raise CharacterGenerationError("AI 未返回有效的角色列表")

    # 检测英文内容，自动翻译为中文
    characters = await _translate_fields_to_chinese(client, characters)

    # 校验每个角色的必要字段，缺失的补默认值
    required_fields = {
        "role_type": "supporting",
        "personality": "",
        "appearance": "",
        "clothing": "",
        "special_features": "",
        "action_expression": "中性表情",
    }

    # 组装每个角色的模板化 prompt
    from app.services.prompt_assembler import (
        build_character_description,
        assemble_image_prompt,
        build_negative_prompt,
        validate_and_fix_prompt,
    )

    result: list[dict[str, Any]] = []
    for idx, char in enumerate(characters):
        if not isinstance(char, dict):
            logger.warning("跳过非字典角色项 [%d]: %s", idx, type(char))
            continue

        if not char.get("name"):
            logger.warning("跳过无名角色 [%d]", idx)
            continue

        # 补全缺失字段
        for field, default in required_fields.items():
            if field not in char or not char[field]:
                logger.debug("角色 '%s' 缺少字段 '%s'，使用默认值", char["name"], field)
                char[field] = default

        # 使用 prompt_assembler 组装
        era = visual_settings.get("era", "modern")
        cultural_style = visual_settings.get("cultural_style", "east_asian")
        char_desc = build_character_description(char, era, cultural_style)
        action_expr = char.get("action_expression", "neutral expression")
        image_prompt = assemble_image_prompt(char_desc, action_expr, visual_settings)
        image_prompt = validate_and_fix_prompt(image_prompt)

        negative_prompt = build_negative_prompt(char, cultural_style)

        traits = {
            "role_type": char.get("role_type", "supporting"),
            "personality": char.get("personality", ""),
            "appearance": char.get("appearance", ""),
            "clothing": char.get("clothing", ""),
            "special_features": char.get("special_features", ""),
            "image_prompt": image_prompt,
            "negative_prompt": negative_prompt,
        }

        result.append({
            "name": char["name"],
            "traits": traits,
            "image_prompt": image_prompt,
            "negative_prompt": negative_prompt,
        })

    logger.info("角色生成完成: %d 个角色", len(result))
    return result


async def generate_group_prompt(
    characters: list[dict[str, Any]],
    visual_settings: dict[str, str],
) -> str:
    """
    生成角色合照 prompt（用于宣传海报/封面）。

    Args:
        characters: 角色列表（含 traits.image_prompt）。
        visual_settings: 视觉设定。

    Returns:
        合照英文 prompt。
    """
    visual_settings = _normalize_settings(visual_settings)

    # 提取每个角色的 subject 部分
    subjects: list[str] = []
    for char in characters:
        traits = char.get("traits", {})
        name = char.get("name", "")
        role = traits.get("role_type", "supporting")
        appearance = traits.get("appearance", "")
        clothing = traits.get("clothing", "")
        expression = "confident pose" if role in ("protagonist", "antagonist") else "casual stance"
        subjects.append(f"{appearance}, {clothing}, {expression}")

    group_subject = " and ".join(subjects[:6])  # 最多 6 人合照

    from app.services.prompt_assembler import assemble_image_prompt, validate_and_fix_prompt

    prompt = assemble_image_prompt(
        f"group portrait of {len(subjects)} characters: {group_subject}",
        "dramatic composition",
        visual_settings,
    )
    prompt = validate_and_fix_prompt(prompt)

    logger.info("生成合照 prompt: %d 个角色", len(subjects))
    return prompt
