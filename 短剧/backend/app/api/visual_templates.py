"""
视觉模板 API 端点 - 模板 CRUD 管理。

系统模板只读，用户模板可增删改。
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.visual_template import VisualTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/visual-templates", tags=["视觉模板"])


def _normalize_settings(settings: dict | str | None) -> dict:
    """确保 settings 返回为 dict，兼容字符串存储的情况。"""
    if isinstance(settings, dict):
        return settings
    if isinstance(settings, str):
        try:
            return json.loads(settings)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


class TemplateCreateRequest(BaseModel):
    """创建模板请求体。"""
    name: str
    description: str | None = None
    settings: dict


class TemplateUpdateRequest(BaseModel):
    """更新模板请求体。"""
    name: str | None = None
    description: str | None = None
    settings: dict | None = None


class TemplateResponse(BaseModel):
    """模板响应体。"""
    id: str
    name: str
    description: str | None
    settings: dict
    is_system: bool
    created_at: str
    updated_at: str


@router.get("", response_model=list[TemplateResponse], summary="获取模板列表")
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[TemplateResponse]:
    """返回所有模板（系统预设 + 用户自定义）。"""
    result = await db.execute(
        select(VisualTemplate).order_by(VisualTemplate.is_system.desc(), VisualTemplate.created_at)
    )
    templates = result.scalars().all()
    return [
        TemplateResponse(
            id=str(t.id),
            name=t.name,
            description=t.description,
            settings=_normalize_settings(t.settings),
            is_system=t.is_system,
            created_at=t.created_at.isoformat() if t.created_at else "",
            updated_at=t.updated_at.isoformat() if t.updated_at else "",
        )
        for t in templates
    ]


@router.post("", response_model=TemplateResponse, summary="创建用户模板")
async def create_template(
    req: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """创建用户自定义模板。"""
    template = VisualTemplate(
        name=req.name,
        description=req.description,
        settings=req.settings,
        is_system=False,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    logger.info("用户模板已创建: %s (%s)", template.name, template.id)
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        settings=template.settings,
        is_system=template.is_system,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.put("/{template_id}", response_model=TemplateResponse, summary="更新模板")
async def update_template(
    template_id: str,
    req: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TemplateResponse:
    """更新模板（系统模板不允许修改）。"""
    result = await db.execute(
        select(VisualTemplate).where(VisualTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在")
    if template.is_system:
        raise HTTPException(status_code=403, detail="系统模板不允许修改")

    if req.name is not None:
        template.name = req.name
    if req.description is not None:
        template.description = req.description
    if req.settings is not None:
        template.settings = req.settings

    await db.commit()
    await db.refresh(template)
    logger.info("模板已更新: %s (%s)", template.name, template.id)
    return TemplateResponse(
        id=str(template.id),
        name=template.name,
        description=template.description,
        settings=template.settings,
        is_system=template.is_system,
        created_at=template.created_at.isoformat() if template.created_at else "",
        updated_at=template.updated_at.isoformat() if template.updated_at else "",
    )


@router.delete("/{template_id}", summary="删除模板")
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除模板（系统模板不允许删除）。"""
    result = await db.execute(
        select(VisualTemplate).where(VisualTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail="模板不存在")
    if template.is_system:
        raise HTTPException(status_code=403, detail="系统模板不允许删除")

    await db.delete(template)
    await db.commit()
    logger.info("模板已删除: %s (%s)", template.name, template_id)
    return {"detail": f"模板 {template.name} 已删除"}
