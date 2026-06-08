"""
系统设置 API - 按服务商分组的配置管理。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.system_config_service import (
    get_all_providers,
    get_provider_config,
    update_provider_config,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/system-settings", tags=["系统设置"])


@router.get(
    "/providers",
    summary="获取所有服务商列表及配置",
    description="返回所有服务商的配置 schema、当前值（敏感字段掩码）和配置状态。",
)
async def list_providers(
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await get_all_providers(db)


@router.get(
    "/providers/{provider}",
    summary="获取指定服务商配置",
    description="返回指定服务商的配置 schema 和当前值（敏感字段掩码）。",
)
async def get_provider(
    provider: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await get_provider_config(db, provider)
    if result is None:
        raise HTTPException(status_code=404, detail=f"服务商 {provider} 不存在")
    return result


@router.put(
    "/providers/{provider}",
    summary="更新指定服务商配置",
    description="部分更新配置，仅修改传入的字段。敏感字段加密存储。",
)
async def update_provider(
    provider: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    configs = body.get("configs")
    if not configs or not isinstance(configs, dict):
        raise HTTPException(status_code=400, detail="请求体需包含 configs 字段（JSON 对象）")

    result = await update_provider_config(db, provider, configs)
    if result is None:
        raise HTTPException(status_code=404, detail=f"服务商 {provider} 不存在")

    return result
