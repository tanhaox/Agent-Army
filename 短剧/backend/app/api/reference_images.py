"""
角色参考图 API 端点 - 多角度参考图管理。

支持上传、删除、更新元数据、生成多角度提示词。
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.character import Character

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/characters", tags=["角色参考图"])

VALID_ANGLES = {"front", "left_side", "right_side", "back", "full_body", "half_body"}
VALID_POSES = {"standing", "sitting", "action", "walking", "dynamic_pose"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


class UpdateReferenceImageRequest(BaseModel):
    angle: str | None = None
    pose: str | None = None
    is_primary: bool | None = None


class GenerateAnglePromptsRequest(BaseModel):
    angles: list[str] | None = None


# ---------- 辅助函数 ----------

async def _get_character(db: AsyncSession, character_id: str) -> Character:
    result = await db.execute(select(Character).where(Character.id == character_id))
    char = result.scalar_one_or_none()
    if char is None:
        raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
    return char


def _parse_reference_images(raw) -> list[dict]:
    """兼容旧格式（字符串列表）和新格式（对象列表）。"""
    if not raw:
        return []
    result = []
    for item in raw:
        if isinstance(item, str):
            result.append({
                "id": str(uuid.uuid4()),
                "url": item,
                "angle": "front",
                "pose": "standing",
                "is_primary": len(result) == 0,
                "created_at": datetime.utcnow().isoformat(),
            })
        elif isinstance(item, dict):
            result.append(item)
    return result


# ---------- 端点 ----------

@router.post(
    "/{character_id}/reference-images",
    summary="上传角色参考图",
    description="上传图片到角色，支持标记角度和姿态。",
)
async def upload_reference_image(
    character_id: str,
    file: UploadFile = File(...),
    angle: str = Form("front"),
    pose: str = Form("standing"),
    is_primary: bool = Form(False),
    db: AsyncSession = Depends(get_db),
) -> dict:
    character = await _get_character(db, character_id)

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file.content_type}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")

    if angle not in VALID_ANGLES:
        raise HTTPException(status_code=400, detail=f"无效角度: {angle}，可选: {VALID_ANGLES}")

    # 保存文件
    ext = Path(file.filename or "upload.jpg").suffix or ".jpg"
    filename = f"{character_id}_{uuid.uuid4().hex[:8]}{ext}"
    save_dir = Path("static/characters")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir / filename
    save_path.write_bytes(content)
    url_path = f"/static/characters/{filename}"

    # 更新 reference_images
    images = _parse_reference_images(character.reference_images)

    # 如果设为主视觉，清除其他主视觉
    if is_primary:
        for img in images:
            img["is_primary"] = False

    new_image = {
        "id": str(uuid.uuid4()),
        "url": url_path,
        "angle": angle,
        "pose": pose,
        "is_primary": is_primary,
        "created_at": datetime.utcnow().isoformat(),
    }
    images.append(new_image)

    character.reference_images = images
    await db.commit()
    logger.info("参考图已上传: character=%s, angle=%s", character_id, angle)
    return new_image


@router.put(
    "/{character_id}/reference-images/{image_id}",
    summary="更新参考图元数据",
)
async def update_reference_image(
    character_id: str,
    image_id: str,
    req: UpdateReferenceImageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    character = await _get_character(db, character_id)
    images = _parse_reference_images(character.reference_images)

    target = None
    for img in images:
        if img["id"] == image_id:
            target = img
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"参考图 {image_id} 不存在")

    if req.angle is not None:
        if req.angle not in VALID_ANGLES:
            raise HTTPException(status_code=400, detail=f"无效角度: {req.angle}")
        target["angle"] = req.angle

    if req.pose is not None:
        if req.pose not in VALID_POSES:
            raise HTTPException(status_code=400, detail=f"无效姿态: {req.pose}")
        target["pose"] = req.pose

    if req.is_primary is True:
        for img in images:
            img["is_primary"] = img["id"] == image_id

    character.reference_images = images
    await db.commit()
    logger.info("参考图已更新: character=%s, image=%s", character_id, image_id)
    return target


@router.delete(
    "/{character_id}/reference-images/{image_id}",
    summary="删除参考图",
)
async def delete_reference_image(
    character_id: str,
    image_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    character = await _get_character(db, character_id)
    images = _parse_reference_images(character.reference_images)

    target = None
    for img in images:
        if img["id"] == image_id:
            target = img
            break

    if target is None:
        raise HTTPException(status_code=404, detail=f"参考图 {image_id} 不存在")

    # 删除文件
    url = target.get("url", "")
    if url.startswith("/static/"):
        file_path = Path(url.lstrip("/"))
        if file_path.exists():
            file_path.unlink()
            logger.info("图片文件已删除: %s", url)

    images.remove(target)
    character.reference_images = images
    await db.commit()
    logger.info("参考图已删除: character=%s, image=%s", character_id, image_id)
    return {"detail": "参考图已删除"}


@router.post(
    "/{character_id}/generate-angle-prompts",
    summary="生成多角度图片提示词",
    description="基于角色特征和项目视觉设定，为指定角度生成英文提示词（不实际生成图片）。",
)
async def generate_angle_prompts(
    character_id: str,
    req: GenerateAnglePromptsRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.llm import get_llm_client
    from app.services.prompt_assembler import get_cultural_style

    character = await _get_character(db, character_id)

    angles = req.angles or ["front", "left_side", "right_side", "full_body"]
    for a in angles:
        if a not in VALID_ANGLES:
            raise HTTPException(status_code=400, detail=f"无效角度: {a}")

    traits = character.traits or {}
    appearance = traits.get("appearance", "")
    clothing = traits.get("clothing", "")
    special = traits.get("special_features", "")
    cultural_style = traits.get("cultural_style", "east_asian")
    style_info = get_cultural_style(cultural_style)
    race_prefix = style_info["race_prefix"]

    angle_descriptions = {
        "front": "正面视图，直视镜头，完整面部可见",
        "left_side": "左侧轮廓，面部向左转90度",
        "right_side": "右侧轮廓，面部向右转90度",
        "back": "背面视图，展示后脑勺和服装背面",
        "full_body": "全身照，从头到脚，站直",
        "half_body": "半身照，腰部以上，微转",
    }

    system_prompt = (
        "你是一位角色设计提示词工程师。"
        "为每个角度生成一段中文图像提示词。"
        "每段提示词必须描述同一个角色从不同角度的样子。"
        "输出一个 JSON 对象，键为角度名，值为中文提示词字符串。"
        "不要输出其他文字。"
        "⚠️ 严重警告：所有提示词必须使用中文！禁止输出英文！"
    )

    user_prompt = (
        f"角色描述：{appearance}\n"
        f"服饰：{clothing}\n"
    )
    if special:
        user_prompt += f"特殊特征：{special}\n"
    user_prompt += (
        f"\n请为以下角度生成中文提示词：{', '.join(angles)}\n"
        f"角度指引：\n"
    )
    for a in angles:
        user_prompt += f"- {a}: {angle_descriptions.get(a, a)}\n"
    user_prompt += "\nOutput only the JSON object."

    client = get_llm_client()
    raw = await client.generate(user_prompt, system=system_prompt)

    # 解析 JSON
    import json, re
    text = raw.strip()
    if text.startswith("```"):
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()
    if not text.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            text = match.group(0)

    try:
        prompts = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("角度提示词 JSON 解析失败: %s", e)
        # 降级：使用模板生成
        prompts = {}
        for a in angles:
            parts = [race_prefix, appearance, f"wearing {clothing}"]
            if special:
                parts.append(special)
            parts.append(angle_descriptions.get(a, a))
            prompts[a] = ", ".join(parts)

    logger.info("多角度提示词生成完成: character=%s, %d个角度", character_id, len(prompts))
    return prompts
