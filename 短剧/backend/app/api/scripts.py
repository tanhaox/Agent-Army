"""
剧本 API 端点 - 剧本生成、查询、列表。
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models.narrative_tree import NarrativeTree
from app.models.script import Script
from app.schemas.script import (
    GenerateScriptFromOutlineRequest,
    ScriptDetailResponse,
    ScriptResponse,
    ScriptUpdateRequest,
)
from app.services.llm.base import LLMConnectionError, LLMGenerateError
from app.services.script_generation_service import (
    ScriptGenerationService,
    ScriptParseError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scripts", tags=["剧本"])


@router.get(
    "/",
    response_model=list[ScriptResponse],
    summary="获取剧本列表",
    description="返回所有剧本的摘要信息（不含完整 content）。",
)
async def list_scripts(
    db: AsyncSession = Depends(get_db),
) -> list[ScriptResponse]:
    """获取剧本列表，按创建时间倒序。"""
    result = await db.execute(
        select(Script).order_by(Script.created_at.desc())
    )
    scripts = result.scalars().all()
    return [ScriptResponse.model_validate(s) for s in scripts]


@router.get(
    "/{script_id}",
    response_model=ScriptDetailResponse,
    summary="获取剧本详情",
    description="根据 ID 返回剧本的完整内容。",
    responses={404: {"description": "剧本不存在"}},
)
async def get_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    """根据 ID 获取单个剧本的完整详情。"""
    result = await db.execute(
        select(Script).where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()

    if script is None:
        raise HTTPException(status_code=404, detail=f"剧本 {script_id} 不存在")

    return ScriptDetailResponse.model_validate(script)


@router.put(
    "/{script_id}",
    response_model=ScriptDetailResponse,
    summary="更新剧本内容",
    description="更新剧本的 content 字段（完整替换）。",
    responses={404: {"description": "剧本不存在"}},
)
async def update_script(
    script_id: str,
    req: ScriptUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    """更新剧本内容。"""
    result = await db.execute(
        select(Script).where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()

    if script is None:
        raise HTTPException(status_code=404, detail=f"剧本 {script_id} 不存在")

    script.content = req.content
    await db.commit()
    await db.refresh(script)

    logger.info("剧本已更新: script=%s", script_id)
    return ScriptDetailResponse.model_validate(script)


@router.post(
    "/generate-from-outline",
    response_model=ScriptDetailResponse,
    summary="从剧情概要生成剧本",
    description="根据剧情概要和风格，调用 AI 生成结构化剧本（含质量检测和自动重试）。",
    responses={
        404: {"description": "项目不存在"},
        422: {"description": "AI 返回内容无法解析"},
        503: {"description": "AI 服务不可用"},
    },
)
@limiter.limit("5/minute")
async def generate_script_from_outline(
    request: Request,
    req: GenerateScriptFromOutlineRequest,
    db: AsyncSession = Depends(get_db),
) -> ScriptDetailResponse:
    """从剧情概要生成完整剧本。"""
    try:
        # 验证项目存在
        from app.services import project_service
        project = await project_service.get_project(db, req.project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {req.project_id} 不存在")

        service = ScriptGenerationService()
        content = await service.generate_from_outline(
            outline_text=req.outline_text,
            style=req.style,
            project_name=project.name,
        )

        # 保存剧本（含来源追踪）
        script = Script(
            project_name=project.name,
            theme=f"[{req.style}] {req.outline_text[:100]}",
            content=content,
            project_id=req.project_id,
            source_narrative_tree_id=req.source_narrative_tree_id,
            source_outline_id=req.source_outline_id,
        )
        db.add(script)
        await db.flush()

        # 更新项目 current_script_id
        project.current_script_id = str(script.id)

        # 更新叙事树的 final_outline_id
        if req.source_narrative_tree_id and req.source_outline_id:
            tree_result = await db.execute(
                select(NarrativeTree).where(NarrativeTree.id == req.source_narrative_tree_id)
            )
            tree = tree_result.scalar_one_or_none()
            if tree:
                tree.final_outline_id = req.source_outline_id

        await db.commit()
        await db.refresh(script)

        logger.info(
            "从概要生成剧本成功: script=%s, project=%s, source_tree=%s, source_outline=%s",
            script.id, req.project_id, req.source_narrative_tree_id, req.source_outline_id,
        )
        return ScriptDetailResponse.model_validate(script)

    except LLMConnectionError as e:
        logger.error("从概要生成剧本 - LLM 连接失败: %s", e)
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        logger.error("从概要生成剧本 - AI 生成失败: %s", e)
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except ScriptParseError as e:
        logger.error("从概要生成剧本 - JSON 解析失败: %s", e)
        raise HTTPException(
            status_code=422,
            detail=f"AI 返回的内容无法解析为有效剧本: {e}",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("从概要生成剧本失败: %s", e)
        raise HTTPException(status_code=500, detail=f"生成剧本失败: {e}") from e
