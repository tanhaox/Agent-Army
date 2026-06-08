"""
素材预生成服务 - 智能分析镜头需求并调用 Seedream 生成素材。

流程：
1. analyze_material_requirements: 用 LLM 分析 action/environment/vfx/dialogue，输出素材需求列表
2. pregen_materials_for_shot: 根据需求列表逐个调用 Seedream 生图
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import storyboard_service
from app.services.llm import get_llm_client, LLMConnectionError, LLMGenerateError
from app.services.seedream_service import (
    SeedreamClient,
    SeedreamConnectionError,
    SeedreamGenerationError,
)

logger = logging.getLogger(__name__)

_ANALYZE_SYSTEM_PROMPT = """你是一位短剧视觉素材分析师。用户会给你一个分镜的详细描述，请你分析这个镜头需要哪些额外的视觉素材（用于后续 AI 生图）。

你必须且只能输出一个合法的 JSON 数组，不要输出任何其他文字或 markdown 代码块标记。直接以 [ 开头，以 ] 结尾。

每个元素的结构：
{
  "type": "background 或 prop 或 vfx",
  "name": "素材名称（中文，简短）",
  "description": "中文详细描述这个素材应该长什么样",
  "prompt": "用于 AI 生图的英文提示词，详细描述素材的外观、光照、构图",
  "reason": "为什么需要这个素材（中文，简短）"
}

分析规则：
1. **背景图（background）**：每个镜头必须有背景图。根据 environment 和 lighting 字段生成背景提示词。提示词需描述环境场景，不含人物。
2. **道具图（prop）**：分析 action 字段，找出角色与之互动的具体物品（如：旧照片、打火机、剑、玉佩、钥匙、信件等）。每个道具生成一个素材需求。如果没有明确道具则不生成。
3. **特效参考图（vfx）**：如果 vfx 不为"无"，生成一个特效视觉参考图需求。

提示词要求：
- background 的 prompt 用英文，描述环境场景，4K，masterpiece，no people
- prop 的 prompt 用英文，聚焦物品本身，干净背景，高细节，4K
- vfx 的 prompt 用英文，描述视觉特效效果，动态，4K

示例输入：action="一只戴着昂贵腕表的手，正用打火机点燃一张泛黄的旧照片" environment="商场奢侈品店外" lighting="冷色调" vfx="光效"
示例输出：
[
  {"type": "background", "name": "商场奢侈品店外", "description": "夜晚的奢侈品店外场景，背景虚化，冷色调灯光", "prompt": "Exterior of a luxury boutique store at night, cold blue ambient lighting, blurred background with soft bokeh lights, no people, cinematic composition, 4K, masterpiece", "reason": "环境背景"},
  {"type": "prop", "name": "泛黄的旧照片", "description": "一张边缘泛黄烧焦的旧照片，照片中有模糊人影", "prompt": "A weathered yellowed old photograph with charred edges being consumed by flame, sepia tones, detailed paper texture, close-up shot, dark background, high detail, 4K, masterpiece", "reason": "动作中点燃的照片"},
  {"type": "prop", "name": "银色打火机", "description": "精致的银色打火机，火苗正旺", "prompt": "A sleek silver lighter with a bright steady flame, metallic reflective surface, warm fire glow, close-up macro shot, dark background, high detail, 4K, masterpiece", "reason": "动作中使用的打火机"},
  {"type": "vfx", "name": "光效特效", "description": "火焰光效映照在物体上的视觉效果", "prompt": "Warm fire glow lighting effect illuminating objects, dramatic light and shadow, cinematic lighting, dynamic flame particles, 4K, masterpiece", "reason": "特效需求"}
]"""


def _extract_json(text: str) -> str:
    """从 LLM 响应中提取 JSON。"""
    text = text.strip()
    if text.startswith("["):
        return text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"\[[\s\S]*\]", text)
    if m:
        return m.group(0)
    raise ValueError(f"无法提取 JSON。响应前200字：{text[:200]}")


async def analyze_material_requirements(storyboard_dict: dict[str, Any]) -> list[dict[str, Any]]:
    """
    用 LLM 分析分镜内容，返回素材需求列表。
    每个需求包含 type, name, description, prompt, reason。
    """
    action = storyboard_dict.get("action", "")
    environment = storyboard_dict.get("environment", "")
    lighting = storyboard_dict.get("lighting", "")
    vfx = storyboard_dict.get("vfx", "")
    dialogue = storyboard_dict.get("dialogue", "")
    emotion = storyboard_dict.get("emotion", "")

    # 如果环境、动作、特效都为空，无需分析
    if not any([action, environment, vfx]):
        return []

    user_prompt = (
        f"分镜信息：\n"
        f"- 动作：{action}\n"
        f"- 环境：{environment}\n"
        f"- 光线：{lighting}\n"
        f"- 特效：{vfx}\n"
        f"- 对话：{dialogue or '无'}\n"
        f"- 情绪：{emotion}\n\n"
        f"请分析这个镜头需要的视觉素材。"
    )

    client = get_llm_client()
    raw = await client.generate(user_prompt, system=_ANALYZE_SYSTEM_PROMPT)

    json_str = _extract_json(raw)
    json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

    try:
        requirements = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning("素材需求 JSON 解析失败: %s", e)
        return []

    if not isinstance(requirements, list):
        return []

    # 过滤有效项
    valid = []
    for req in requirements:
        if not isinstance(req, dict):
            continue
        if req.get("type") in ("background", "prop", "vfx") and req.get("prompt"):
            valid.append(req)

    logger.info("素材需求分析完成: %d 个需求", len(valid))
    return valid


async def pregen_materials_for_shot(
    db: AsyncSession,
    storyboard_id: str,
) -> dict[str, Any]:
    """
    为单个镜头智能分析需求并生成缺失素材。

    Returns:
        更新后的 pregen_materials 字典。
    """
    storyboard = await storyboard_service.get_storyboard(db, storyboard_id)
    if storyboard is None:
        raise ValueError(f"分镜 {storyboard_id} 不存在")

    existing = dict(storyboard.pregen_materials or {})

    # 将 storyboard 转为字典供 LLM 分析
    sb_dict = {
        "action": storyboard.action or "",
        "environment": storyboard.environment or "",
        "lighting": storyboard.lighting or "",
        "vfx": storyboard.vfx or "",
        "dialogue": storyboard.dialogue or "",
        "emotion": storyboard.emotion or "",
    }

    # 用 LLM 分析需求
    requirements = await analyze_material_requirements(sb_dict)
    if not requirements:
        logger.info("镜头 %s 无素材需求", storyboard_id[:8])
        return existing

    # 生成素材
    client = SeedreamClient()
    save_dir = Path("static/storyboards") / storyboard_id[:8]
    save_dir.mkdir(parents=True, exist_ok=True)
    generated: dict[str, Any] = dict(existing)

    # 统计各类型的序号
    type_counters: dict[str, int] = {}
    for req in requirements:
        rtype = req["type"]
        if rtype == "background" and existing.get("background"):
            logger.debug("背景图已存在，跳过")
            continue
        if rtype == "vfx" and existing.get("vfx_ref"):
            logger.debug("特效图已存在，跳过")
            continue
        if rtype == "prop":
            # 检查同名道具是否已存在
            name = req.get("name", "")
            prop_key = f"prop_{name}"
            if existing.get("props", {}).get(name):
                logger.debug("道具 '%s' 已存在，跳过", name)
                continue

        try:
            image_bytes, _ = await client.text_to_image(req["prompt"])
            idx = type_counters.get(rtype, 0)
            type_counters[rtype] = idx + 1

            if rtype == "background":
                filename = f"background_{storyboard.shot_no}.jpg"
                generated["background"] = f"/static/storyboards/{storyboard_id[:8]}/{filename}"
            elif rtype == "vfx":
                filename = f"vfx_{storyboard.shot_no}.jpg"
                generated["vfx_ref"] = f"/static/storyboards/{storyboard_id[:8]}/{filename}"
            elif rtype == "prop":
                filename = f"prop_{idx}_{storyboard.shot_no}.jpg"
                props = dict(generated.get("props", {}) or {})
                props[req.get("name", f"prop_{idx}")] = f"/static/storyboards/{storyboard_id[:8]}/{filename}"
                generated["props"] = props

            (save_dir / filename).write_bytes(image_bytes)
            logger.info("素材已生成: %s/%s — %s", storyboard_id[:8], filename, req.get("name", rtype))
        except (SeedreamConnectionError, SeedreamGenerationError) as e:
            logger.warning("素材生成失败 (%s): %s", req.get("name", rtype), e)

    # 保存到数据库
    if generated != existing:
        await storyboard_service.update_storyboard(
            db, storyboard, pregen_materials=generated,
        )

    return generated
