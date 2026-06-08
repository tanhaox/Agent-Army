"""
角色多角度参考图生成服务 - 基于 Seedream img2img 工作流。

流程：
1. generate_candidates: 文生图生成 4-8 张候选正面照
2. set_base_image: 用户选择基准图
3. generate_angles_from_base: 基于基准图图生图生成多角度
"""

import logging
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import character_service
from app.services.seedream_service import (
    SeedreamClient,
    SeedreamConnectionError,
    SeedreamGenerationError,
)

logger = logging.getLogger(__name__)

# 图生图角度提示词模板（中文，强调一致性）
ANGLE_PROMPTS: dict[str, str] = {
    "left_side": (
        "参考这张图片的人物和服装，生成同一个人的左侧面半身照。要求：\n"
        "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
        "- 服装样式、颜色、细节必须与参考图一致。\n"
        "- 背景保持简洁，不分散注意力。\n"
        "- 高质量，4K，电影级布光。"
    ),
    "right_side": (
        "参考这张图片的人物和服装，生成同一个人的右侧面半身照。要求：\n"
        "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
        "- 服装样式、颜色、细节必须与参考图一致。\n"
        "- 背景保持简洁。\n"
        "- 高质量，4K，电影级布光。"
    ),
    "back": (
        "参考这张图片的人物和服装，生成同一个人的背面全身照。要求：\n"
        "- 发型、服装必须与参考图完全相同。\n"
        "- 站姿自然。\n"
        "- 背景保持简洁。\n"
        "- 高质量，4K，电影级布光。"
    ),
    "closeup_face": (
        "参考这张图片的人物和服装，生成同一个人的正面特写。要求：\n"
        "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
        "- 聚焦面部，展示五官细节。\n"
        "- 高质量，4K，超细节皮肤质感，浅景深。"
    ),
    "front_full": (
        "参考这张图片的人物和服装，生成同一个人的正面全身照。要求：\n"
        "- 脸部特征、发型、肤色必须与参考图完全相同。\n"
        "- 全身服装样式细节必须与参考图一致。\n"
        "- 自然站姿。\n"
        "- 高质量，4K，电影级布光。"
    ),
}


def _build_candidate_prompt(traits: dict[str, Any]) -> str:
    """根据角色特征构建正面候选照提示词。"""
    parts = []
    gender = "男性" if traits.get("gender") == "male" else "女性"
    age = traits.get("age", "")
    if age:
        parts.append(f"{age}岁")
    parts.append(f"东亚{gender}")

    if traits.get("appearance"):
        parts.append(str(traits["appearance"]))
    if traits.get("clothing"):
        parts.append(str(traits["clothing"]))
    if traits.get("special_features"):
        parts.append(str(traits["special_features"]))

    parts.extend([
        "正面半身肖像照，胸部以上构图，面朝镜头正前方，双眼直视镜头",
        "平视角度拍摄，相机与面部齐平，禁止俯拍和仰拍",
        "表情自然自信，类似学术讲座或商业论坛专家宣传照风格",
        "浅灰色或白色干净背景，摄影棚布光，柔和正面补光",
        "高质量，细节丰富，4K，masterpiece",
    ])
    return "，".join(parts)


async def generate_candidates(
    db: AsyncSession,
    character_id: str,
    count: int = 4,
    prompt_hint: str | None = None,
) -> list[str]:
    """
    为角色生成正面候选照。

    Args:
        db: 数据库会话。
        character_id: 角色 UUID。
        count: 生成数量（4-8）。
        prompt_hint: 可选的提示词补充。

    Returns:
        图片 URL 列表。
    """
    if not 1 <= count <= 8:
        raise ValueError("候选数量必须在 1-8 之间")

    character = await character_service.get_character(db, character_id)
    if character is None:
        raise ValueError(f"角色 {character_id} 不存在")

    prompt = _build_candidate_prompt(character.traits)
    if prompt_hint:
        prompt = f"{prompt}，{prompt_hint}"

    logger.info("生成角色候选照: name=%s, count=%d", character.name, count)

    client = SeedreamClient()
    candidate_urls: list[str] = []
    save_dir = Path("static/characters/candidates")
    save_dir.mkdir(parents=True, exist_ok=True)

    for i in range(count):
        try:
            image_bytes, metadata = await client.text_to_image(prompt)
            filename = f"{character_id[:8]}_candidate_{i+1}.jpg"
            filepath = save_dir / filename
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            url_path = f"/static/characters/candidates/{filename}"
            candidate_urls.append(url_path)
            logger.info("候选照 %d/%d 已保存: %s", i + 1, count, url_path)
        except SeedreamGenerationError as e:
            logger.error("生成候选照 %d 失败: %s", i + 1, e)

    if not candidate_urls:
        raise SeedreamGenerationError("所有候选照生成均失败")

    return candidate_urls


async def set_base_image(
    db: AsyncSession,
    character_id: str,
    image_url: str,
) -> Any:
    """设置角色的基准图。"""
    character = await character_service.get_character(db, character_id)
    if character is None:
        raise ValueError(f"角色 {character_id} 不存在")

    updated = await character_service.update_character(
        db, character, base_image_url=image_url,
    )
    logger.info("角色基准图已设置: id=%s, url=%s", character_id, image_url)
    return updated


async def generate_angles_from_base(
    db: AsyncSession,
    character_id: str,
    angles: list[str] | None = None,
) -> dict[str, str]:
    """
    基于基准图生成多角度图片。

    Args:
        db: 数据库会话。
        character_id: 角色 UUID。
        angles: 角度列表，默认 ["left_side", "right_side", "back", "closeup_face"]。

    Returns:
        {角度: 图片URL} 字典。
    """
    if angles is None:
        angles = ["left_side", "right_side", "back", "closeup_face"]

    invalid = [a for a in angles if a not in ANGLE_PROMPTS]
    if invalid:
        raise ValueError(f"无效的角度: {invalid}，可选: {', '.join(ANGLE_PROMPTS.keys())}")

    character = await character_service.get_character(db, character_id)
    if character is None:
        raise ValueError(f"角色 {character_id} 不存在")

    if not character.base_image_url:
        raise ValueError(f"角色 {character_id} 未设置基准图，请先选择基准图")

    # 读取基准图（直接从本地文件系统读取，避免网络请求）
    base_url = character.base_image_url
    if base_url.startswith("/static/"):
        local_path = Path(base_url.lstrip("/"))
        if not local_path.exists():
            raise ValueError(f"基准图文件不存在: {local_path}")
        base_image_bytes = local_path.read_bytes()
    else:
        if base_url.startswith("/static"):
            base_url = f"http://localhost:8000{base_url}"
        resp = httpx.get(base_url, timeout=30)
        resp.raise_for_status()
        base_image_bytes = resp.content

    logger.info("开始生成多角度: name=%s, angles=%d", character.name, len(angles))

    client = SeedreamClient()
    angle_urls: dict[str, str] = {}
    save_dir = Path("static/characters/angles")
    save_dir.mkdir(parents=True, exist_ok=True)

    for angle in angles:
        try:
            prompt = ANGLE_PROMPTS[angle]
            image_bytes, metadata = await client.image_to_image(
                prompt=prompt,
                base_image_bytes=base_image_bytes,
            )
            filename = f"{character_id[:8]}_{angle}.jpg"
            filepath = save_dir / filename
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            url_path = f"/static/characters/angles/{filename}"
            angle_urls[angle] = url_path
            logger.info("角度 %s 已生成: %s", angle, url_path)
        except SeedreamGenerationError as e:
            logger.error("生成角度 %s 失败: %s", angle, e)

    if not angle_urls:
        raise SeedreamGenerationError("所有角度生成均失败")

    # 更新 reference_images
    images = list(character.reference_images or [])
    for url in angle_urls.values():
        images.append(url)
    await character_service.update_character(db, character, reference_images=images)

    return angle_urls
