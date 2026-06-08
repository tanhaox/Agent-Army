"""
角色服务层 - 封装数据库操作和图片文件管理。
"""

import logging
import os
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character

logger = logging.getLogger(__name__)

# 允许的图片类型和最大文件大小
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# 静态文件存储目录
STATIC_DIR = Path("static/characters")


def _ensure_static_dir() -> None:
    """确保静态文件目录存在。"""
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


def _validate_image(filename: str, content_size: int) -> str | None:
    """
    校验上传图片的文件名和大小。

    Returns:
        错误信息字符串，校验通过返回 None。
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return f"不支持的文件类型: .{ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}"
    if content_size > MAX_FILE_SIZE:
        return f"文件过大 ({content_size // 1024 // 1024}MB)，最大允许 10MB"
    return None


def _generate_filename(original: str) -> str:
    """生成唯一文件名，避免冲突。"""
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "jpg"
    return f"{uuid.uuid4().hex[:12]}.{ext}"


async def save_image(file_content: bytes, original_filename: str) -> tuple[str, str]:
    """
    保存图片到本地文件系统。

    Args:
        file_content: 文件二进制内容。
        original_filename: 原始文件名。

    Returns:
        (存储文件名, 相对路径) 元组。

    Raises:
        ValueError: 文件校验失败。
    """
    error = _validate_image(original_filename, len(file_content))
    if error:
        raise ValueError(error)

    _ensure_static_dir()
    filename = _generate_filename(original_filename)
    filepath = STATIC_DIR / filename

    with open(filepath, "wb") as f:
        f.write(file_content)

    logger.info("图片已保存: %s", filepath)
    return filename, f"/static/characters/{filename}"


def delete_image(url_path: str) -> None:
    """
    删除本地图片文件。

    Args:
        url_path: 图片的 URL 路径（如 /static/characters/xxx.jpg）。
    """
    filename = url_path.rsplit("/", 1)[-1]
    filepath = STATIC_DIR / filename
    if filepath.exists():
        filepath.unlink()
        logger.info("图片已删除: %s", filepath)


async def create_character(
    db: AsyncSession,
    name: str,
    traits: dict,
    voice_id: str | None,
    platform_bindings: dict,
) -> Character:
    """创建角色。"""
    character = Character(
        name=name,
        traits=traits,
        voice_id=voice_id,
        platform_bindings=platform_bindings,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    logger.info("角色已创建: id=%s, name=%s", character.id, character.name)
    return character


async def get_character(db: AsyncSession, character_id: uuid.UUID) -> Character | None:
    """根据 ID 获取角色。"""
    result = await db.execute(select(Character).where(Character.id == character_id))
    return result.scalar_one_or_none()


async def list_characters(db: AsyncSession) -> list[Character]:
    """获取所有角色列表。"""
    result = await db.execute(select(Character).order_by(Character.created_at.desc()))
    return list(result.scalars().all())


async def update_character(
    db: AsyncSession,
    character: Character,
    **fields,
) -> Character:
    """更新角色字段。"""
    for key, value in fields.items():
        if value is not None:
            setattr(character, key, value)
    await db.commit()
    await db.refresh(character)
    logger.info("角色已更新: id=%s", character.id)
    return character


async def delete_character(db: AsyncSession, character: Character) -> None:
    """删除角色及其关联的图片文件。"""
    images = character.reference_images or []
    for img_url in images:
        try:
            delete_image(img_url)
        except Exception as e:
            logger.warning("删除图片失败: %s, 错误: %s", img_url, e)
    await db.delete(character)
    await db.commit()
    logger.info("角色已删除: id=%s, name=%s", character.id, character.name)
