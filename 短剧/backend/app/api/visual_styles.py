"""
项目视觉风格 API — 风格锁定配置端点。
"""

import logging
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.visual_style_service import get_or_create_style, update_style

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/visual-style", tags=["视觉风格"])


class VisualStyleUpdate(BaseModel):
    style_reference_image: str | None = None
    color_palette: list[str] | None = None
    lighting_rule: str | None = None
    camera_style: str | None = None
    art_style: str | None = None


class VisualStyleResponse(BaseModel):
    project_id: str
    style_reference_image: str | None = None
    color_palette: list[str] | None = None
    lighting_rule: str | None = None
    camera_style: str | None = None
    art_style: str | None = None


@router.get("", response_model=VisualStyleResponse, summary="获取项目视觉风格")
async def get_visual_style(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> VisualStyleResponse:
    style = await get_or_create_style(db, project_id)
    return VisualStyleResponse(
        project_id=style.project_id,
        style_reference_image=style.style_reference_image,
        color_palette=style.color_palette,
        lighting_rule=style.lighting_rule,
        camera_style=style.camera_style,
        art_style=style.art_style,
    )


@router.put("", response_model=VisualStyleResponse, summary="更新项目视觉风格")
async def update_visual_style(
    project_id: str,
    req: VisualStyleUpdate,
    db: AsyncSession = Depends(get_db),
) -> VisualStyleResponse:
    kwargs = {k: v for k, v in req.model_dump().items() if v is not None}
    if not kwargs:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")
    style = await update_style(db, project_id, **kwargs)
    return VisualStyleResponse(
        project_id=style.project_id,
        style_reference_image=style.style_reference_image,
        color_palette=style.color_palette,
        lighting_rule=style.lighting_rule,
        camera_style=style.camera_style,
        art_style=style.art_style,
    )


@router.post("/upload-reference", response_model=VisualStyleResponse, summary="上传风格参考图")
async def upload_style_reference(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> VisualStyleResponse:
    content = await file.read()
    save_dir = FilePath("static/styles")
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{project_id[:8]}_{file.filename}"
    (save_dir / filename).write_bytes(content)
    url = f"/static/styles/{filename}"

    style = await update_style(db, project_id, style_reference_image=url)
    logger.info("风格参考图已上传: project=%s, url=%s", project_id[:8], url)
    return VisualStyleResponse(
        project_id=style.project_id,
        style_reference_image=style.style_reference_image,
        color_palette=style.color_palette,
        lighting_rule=style.lighting_rule,
        camera_style=style.camera_style,
        art_style=style.art_style,
    )
