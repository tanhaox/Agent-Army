"""
分镜服务层 - 封装数据库 CRUD 和提示词生成逻辑。
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard

logger = logging.getLogger(__name__)

# 景别英文映射
SHOT_TYPE_MAP = {
    "远景": "wide shot",
    "全景": "full shot",
    "中景": "medium shot",
    "近景": "close shot",
    "特写": "close-up",
}

# 运镜英文映射
CAMERA_MOVE_MAP = {
    "固定": "static camera",
    "推": "camera push in",
    "拉": "camera pull out",
    "摇": "camera pan",
    "移": "camera tracking",
    "跟": "camera follow",
}


def generate_prompt_text(data: dict) -> str:
    """
    根据分镜参数生成英文视频提示词。

    模板: {shot_type}, {camera_move}, {action}, {emotion} emotion,
           {vfx}, {environment}, {lighting}, cinematic, 4k

    Args:
        data: 包含 shot_type, camera_move, action, emotion,
              environment, lighting, vfx(可选) 的字典。

    Returns:
        英文视频提示词字符串。
    """
    shot_en = SHOT_TYPE_MAP.get(data["shot_type"], data["shot_type"])
    camera_en = CAMERA_MOVE_MAP.get(data["camera_move"], data["camera_move"])

    parts = [shot_en, camera_en, data["action"], f"{data['emotion']} emotion"]

    vfx = data.get("vfx", "无")
    if vfx and vfx != "无":
        parts.append(vfx)

    parts.extend([data["environment"], data["lighting"], "cinematic, 4k"])

    prompt = ", ".join(parts)
    return prompt


async def enhance_video_prompt(item: dict, visual_settings: dict | None = None) -> dict:
    """
    调用 DeepSeek 生成增强版视频提示词。

    Returns:
        {"standard": "...", "enhanced": "...", "negative_prompt": "..."}
        DeepSeek 不可用时回退到模板拼接。
    """
    import json
    import re

    from app.services.video_prompt_templates import (
        build_standard_prompt,
        build_enhanced_prompt,
        build_negative_prompt,
    )

    # 先用模板生成兜底值
    standard = build_standard_prompt(item, visual_settings)
    enhanced = build_enhanced_prompt(item, visual_settings)
    negative = build_negative_prompt(item)

    try:
        from app.services.llm import get_llm_client

        client = get_llm_client()

        system_prompt = (
            "You are a professional cinematographer and AI video generation expert. "
            "Given storyboard parameters, generate high-quality English video prompts.\n\n"
            "Requirements:\n"
            "1. Standard version: concise, direct, suitable for quick AI video generation testing.\n"
            "2. Enhanced version: include camera movement details (e.g. 'slow push-in revealing...'), "
            "lighting descriptions (e.g. 'side-backlight', 'neon reflections'), "
            "atmosphere words (e.g. 'tense oppressive air', 'romantic dreamy glow'), "
            "and consistency directives ('maintain subject identity').\n"
            "3. Negative prompt: list things to AVOID - distortion, flicker, low resolution, "
            "unnatural motion, morphing artifacts.\n"
            "4. If action involves fast movement, add 'smooth motion, no stutter'.\n"
            "5. If character has special features, emphasize 'keep subject identity consistent'.\n"
            "6. Keep standard under 200 chars, enhanced under 500 chars.\n\n"
            "Output ONLY a JSON object with keys: standard, enhanced, negative_prompt. No other text."
        )

        emotion = item.get("emotion", "")
        vfx = item.get("vfx", "无")
        vs = visual_settings or {}

        user_prompt = (
            f"Storyboard:\n"
            f"- Shot type: {item.get('shot_type', '')}\n"
            f"- Camera move: {item.get('camera_move', '')}\n"
            f"- Action: {item.get('action', '')}\n"
            f"- Emotion: {emotion}\n"
            f"- VFX: {vfx}\n"
            f"- Environment: {item.get('environment', '')}\n"
            f"- Lighting: {item.get('lighting', '')}\n"
            f"- Art style: {vs.get('art_style', '')}\n"
            f"- Color palette: {vs.get('color_palette', '')}\n"
            f"- Render quality: {vs.get('render_quality', '')}\n\n"
            f"Generate the three prompts as JSON."
        )

        raw = await client.generate(user_prompt, system=system_prompt)

        # 解析 JSON
        text = raw.strip()
        if text.startswith("```"):
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if match:
                text = match.group(1).strip()
        if not text.startswith("{"):
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                text = match.group(0)

        result = json.loads(text)

        if "standard" in result and result["standard"]:
            standard = result["standard"]
        if "enhanced" in result and result["enhanced"]:
            enhanced = result["enhanced"]
        if "negative_prompt" in result and result["negative_prompt"]:
            negative = result["negative_prompt"]

        logger.info("DeepSeek 提示词增强成功: standard=%dchars, enhanced=%dchars", len(standard), len(enhanced))

    except Exception as e:
        logger.warning("DeepSeek 提示词增强失败，使用模板兜底: %s", e)

    return {
        "standard": standard,
        "enhanced": enhanced,
        "negative_prompt": negative,
    }


async def create_storyboard(
    db: AsyncSession,
    **fields,
) -> Storyboard:
    """创建分镜卡。"""
    storyboard = Storyboard(**fields)
    db.add(storyboard)
    await db.commit()
    await db.refresh(storyboard)
    logger.info("分镜已创建: id=%s, ep=%d, shot=%d", storyboard.id, storyboard.episode_no, storyboard.shot_no)
    return storyboard


async def get_storyboard(db: AsyncSession, storyboard_id: uuid.UUID) -> Storyboard | None:
    """根据 ID 获取分镜。"""
    result = await db.execute(select(Storyboard).where(Storyboard.id == storyboard_id))
    return result.scalar_one_or_none()


async def list_storyboards(
    db: AsyncSession,
    script_id: str | None = None,
    project_id: str | None = None,
) -> list[Storyboard]:
    """
    获取分镜列表。

    Args:
        db: 数据库会话。
        script_id: 可选，按剧本 ID 过滤。
        project_id: 可选，按项目 ID 过滤。

    Returns:
        分镜列表，按集数和镜头序号排序。
    """
    query = select(Storyboard).order_by(Storyboard.episode_no, Storyboard.shot_no)
    if script_id:
        query = query.where(Storyboard.script_id == script_id)
    if project_id:
        query = query.where(Storyboard.project_id == project_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_storyboard(
    db: AsyncSession,
    storyboard: Storyboard,
    **fields,
) -> Storyboard:
    """更新分镜字段。"""
    for key, value in fields.items():
        if value is not None:
            setattr(storyboard, key, value)
    await db.commit()
    await db.refresh(storyboard)
    logger.info("分镜已更新: id=%s", storyboard.id)
    return storyboard


async def delete_storyboard(db: AsyncSession, storyboard: Storyboard) -> None:
    """删除分镜。"""
    await db.delete(storyboard)
    await db.commit()
    logger.info("分镜已删除: id=%s", storyboard.id)
