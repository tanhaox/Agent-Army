"""
项目视觉风格服务 — 风格锁定与注入。

提供风格 CRUD + prompt 风格注入，确保 Seedream 生图和 Seedance 生视频的视觉一致性。
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_visual_style import ProjectVisualStyle

logger = logging.getLogger(__name__)


async def get_or_create_style(db: AsyncSession, project_id: str) -> ProjectVisualStyle:
    """获取或自动创建项目视觉风格配置。"""
    result = await db.execute(
        select(ProjectVisualStyle).where(ProjectVisualStyle.project_id == project_id)
    )
    style = result.scalar_one_or_none()
    if style:
        return style

    style = ProjectVisualStyle(project_id=project_id)
    db.add(style)
    await db.commit()
    await db.refresh(style)
    logger.info("自动创建视觉风格: project=%s", project_id[:8])
    return style


async def update_style(db: AsyncSession, project_id: str, **kwargs) -> ProjectVisualStyle:
    """更新项目视觉风格（部分更新）。"""
    style = await get_or_create_style(db, project_id)
    for key, value in kwargs.items():
        if hasattr(style, key) and value is not None:
            setattr(style, key, value)
    await db.commit()
    await db.refresh(style)
    logger.info("视觉风格已更新: project=%s, fields=%s", project_id[:8], list(kwargs.keys()))
    return style


def apply_style_to_prompt(
    prompt: str,
    style: ProjectVisualStyle,
    is_video: bool = False,
) -> str:
    """
    将风格约束注入 prompt。

    拼接顺序: art_style + lighting_rule + color_palette tones
    视频模式额外追加一致性约束。
    """
    parts: list[str] = []

    if style.art_style:
        parts.append(style.art_style)
    if style.lighting_rule:
        parts.append(style.lighting_rule)
    if style.color_palette and isinstance(style.color_palette, list):
        colors = ", ".join(style.color_palette[:5])
        parts.append(f"{colors} color tones")

    if not parts:
        return prompt

    suffix = ", ".join(parts)
    result = f"{prompt.rstrip(', .')}, {suffix}, style consistent"

    if is_video:
        result += ", maintain visual consistency with the first reference image"

    return result


def has_style_config(style: ProjectVisualStyle) -> bool:
    """检查是否有任何风格配置。"""
    return bool(
        style.style_reference_image
        or style.art_style
        or style.lighting_rule
        or style.camera_style
        or style.color_palette
    )
