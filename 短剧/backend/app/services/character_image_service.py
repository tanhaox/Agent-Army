"""
角色参考图生成服务 - 根据角色描述调用 ComfyUI 生成标准参考图。
"""

import logging
from pathlib import Path
from typing import Any

from app.core.database import AsyncSession
from app.services import character_service
from app.services.comfyui_service import (
    ComfyUIClient,
    ComfyUIConnectionError,
    ComfyUIGenerationError,
)

logger = logging.getLogger(__name__)

# 角度对应的提示词模板
ANGLE_PROMPTS: dict[str, str] = {
    "front": "正面视角, 面朝镜头, front view, portrait",
    "three_quarter": "3/4侧面视角, slightly turned, three-quarter view",
    "side": "侧面视角, profile view, side view",
}

# 角度对应的中文标签
ANGLE_LABELS: dict[str, str] = {
    "front": "正面",
    "three_quarter": "3/4侧面",
    "side": "侧面",
}

# 通用反向提示词
NEGATIVE_PROMPT = (
    "低质量, 模糊, 畸形, 多余肢体, 水印, 文字, 变形, "
    "bad anatomy, bad hands, missing fingers, extra digits, "
    "low quality, blurry, deformed, watermark, text"
)


def _build_character_prompt(traits: dict[str, Any], angle: str) -> str:
    """
    根据角色特征和角度构建正向提示词。

    Args:
        traits: 角色特征字典（age, personality, appearance 等）。
        angle: 拍摄角度（front/three_quarter/side）。

    Returns:
        完整的正向提示词。
    """
    parts = ["1girl" if traits.get("gender", "female") != "male" else "1boy"]

    if traits.get("age"):
        parts.append(f"{traits['age']}岁")
    if traits.get("appearance"):
        parts.append(str(traits["appearance"]))
    if traits.get("personality"):
        parts.append(str(traits["personality"]))

    # 通用质量提升词
    parts.extend([
        "现代都市风格", "高质量", "细节丰富", "白色背景",
        "柔和光线", "摄影棚风格", "masterpiece", "best quality",
    ])

    # 角度描述
    angle_text = ANGLE_PROMPTS.get(angle, ANGLE_PROMPTS["front"])
    parts.append(angle_text)

    return ", ".join(parts)


async def generate_reference_image(
    db: AsyncSession,
    character_id: str,
    angle: str = "front",
) -> str:
    """
    为角色生成参考图并保存。

    流程：
    1. 查询角色信息
    2. 根据特征构建提示词
    3. 调用 ComfyUI 生成图片
    4. 保存到 static/characters/ 目录
    5. 更新数据库 reference_images

    Args:
        db: 数据库会话。
        character_id: 角色 UUID。
        angle: 拍摄角度。

    Returns:
        图片 URL 路径。

    Raises:
        ValueError: 角色不存在或角度无效。
        ComfyUIConnectionError: ComfyUI 不可用。
        ComfyUIGenerationError: 生成失败。
    """
    import uuid as uuid_mod

    # 校验角度
    if angle not in ANGLE_PROMPTS:
        raise ValueError(f"不支持的角度: {angle}，可选: {', '.join(ANGLE_PROMPTS.keys())}")

    # 查询角色
    character = await character_service.get_character(db, uuid_mod.UUID(character_id))
    if character is None:
        raise ValueError(f"角色 {character_id} 不存在")

    # 构建提示词
    prompt = _build_character_prompt(character.traits, angle)
    logger.info("生成角色参考图: name=%s, angle=%s, prompt前60字=%s", character.name, angle, prompt[:60])

    # 调用 ComfyUI 生成
    client = ComfyUIClient()
    image_data = await client.generate_image(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        width=768,
        height=1024,
    )

    # 保存图片
    filename = f"{character_id[:8]}_{angle}.png"
    save_dir = Path("static/characters")
    save_dir.mkdir(parents=True, exist_ok=True)
    filepath = save_dir / filename

    with open(filepath, "wb") as f:
        f.write(image_data)

    url_path = f"/static/characters/{filename}"
    logger.info("角色参考图已保存: %s", url_path)

    # 更新数据库
    images = list(character.reference_images or [])
    # 如果同角度已有图，替换
    angle_key = f"{angle}:"
    images = [img for img in images if not (isinstance(img, str) and angle_key in str(img))]
    images.append(url_path)

    await character_service.update_character(db, character, reference_images=images)

    return url_path
