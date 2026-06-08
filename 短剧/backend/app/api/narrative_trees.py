"""
叙事树 API 端点 - 生成叙事树、确认分支、从叙事树生成剧本。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.narrative_tree import NarrativeTree
from app.schemas.narrative_tree import (
    ConfirmBranchesRequest,
    ExpandNodeRequest,
    GenerateNarrativeTreeRequest,
    GenerateOutlinesRequest,
    GenerateOutlinesResponse,
    GenerateScriptFromTreeRequest,
    NarrativeOutlineResponse,
    NarrativeTreeResponse,
    OutlineItem,
)
from app.services import project_service
from app.services.narrative_tree_service import (
    NarrativeTreeService,
    NarrativeTreeError,
)
from app.services.llm.base import LLMConnectionError, LLMGenerateError
from app.services.script_generation_service import ScriptGenerationService, ScriptParseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["叙事树"])


@router.post(
    "/{project_id}/narrative-trees",
    response_model=NarrativeTreeResponse,
    summary="生成叙事树",
    description="根据创意主题调用 AI 生成分支叙事树。",
    responses={
        404: {"description": "项目不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
async def generate_narrative_tree(
    project_id: str,
    req: GenerateNarrativeTreeRequest,
    db: AsyncSession = Depends(get_db),
) -> NarrativeTreeResponse:
    """生成叙事树。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        service = NarrativeTreeService()
        tree = await service.generate_tree(
            db, project_id,
            theme=req.theme,
            max_breadth=req.max_breadth,
            max_depth=req.max_depth,
        )
        return NarrativeTreeResponse.model_validate(tree)
    except NarrativeTreeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LLMConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("生成叙事树失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"生成叙事树失败: {e}") from e


@router.get(
    "/{project_id}/narrative-trees",
    response_model=list[NarrativeTreeResponse],
    summary="获取叙事树列表",
    description="获取项目的所有叙事树。",
)
async def list_narrative_trees(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[NarrativeTreeResponse]:
    """获取项目的叙事树列表。"""
    result = await db.execute(
        select(NarrativeTree)
        .where(NarrativeTree.project_id == project_id)
        .order_by(NarrativeTree.created_at.desc())
    )
    trees = result.scalars().all()
    return [NarrativeTreeResponse.model_validate(t) for t in trees]


@router.get(
    "/{project_id}/narrative-trees/{tree_id}",
    response_model=NarrativeTreeResponse,
    summary="获取叙事树详情",
    responses={404: {"description": "叙事树不存在"}},
)
async def get_narrative_tree(
    project_id: str,
    tree_id: str,
    db: AsyncSession = Depends(get_db),
) -> NarrativeTreeResponse:
    """获取单个叙事树详情。"""
    result = await db.execute(
        select(NarrativeTree).where(
            NarrativeTree.id == tree_id,
            NarrativeTree.project_id == project_id,
        )
    )
    tree = result.scalar_one_or_none()
    if tree is None:
        raise HTTPException(status_code=404, detail=f"叙事树 {tree_id} 不存在")
    return NarrativeTreeResponse.model_validate(tree)


@router.put(
    "/{project_id}/narrative-trees/{tree_id}/confirm",
    response_model=NarrativeTreeResponse,
    summary="确认分支选择",
    description="用户选择从根到叶子的分支路径。",
    responses={
        400: {"description": "路径不连续"},
        404: {"description": "叙事树不存在"},
    },
)
async def confirm_branches(
    project_id: str,
    tree_id: str,
    req: ConfirmBranchesRequest,
    db: AsyncSession = Depends(get_db),
) -> NarrativeTreeResponse:
    """确认用户选择的分支。"""
    result = await db.execute(
        select(NarrativeTree).where(
            NarrativeTree.id == tree_id,
            NarrativeTree.project_id == project_id,
        )
    )
    tree = result.scalar_one_or_none()
    if tree is None:
        raise HTTPException(status_code=404, detail=f"叙事树 {tree_id} 不存在")

    # 校验路径连续性
    if not NarrativeTreeService.validate_path(tree.tree_data, req.selected_branch_ids):
        raise HTTPException(
            status_code=400,
            detail="选中的节点不构成从根到叶子的连续路径",
        )

    tree.selected_branch_ids = req.selected_branch_ids
    tree.status = "confirmed"
    await db.commit()
    await db.refresh(tree)

    logger.info("叙事树分支已确认: tree=%s, branches=%s", tree_id, req.selected_branch_ids)
    return NarrativeTreeResponse.model_validate(tree)


@router.post(
    "/{project_id}/narrative-trees/{tree_id}/expand-node",
    response_model=NarrativeTreeResponse,
    summary="扩展节点分支",
    description="针对指定节点调用 AI 生成额外的子分支，合并到原有叙事树。",
    responses={
        404: {"description": "叙事树或节点不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
async def expand_node(
    project_id: str,
    tree_id: str,
    req: ExpandNodeRequest,
    db: AsyncSession = Depends(get_db),
) -> NarrativeTreeResponse:
    """扩展指定节点，生成更多分支选项。"""
    try:
        service = NarrativeTreeService()
        tree = await service.expand_node(
            db=db,
            tree_id=tree_id,
            node_id=req.node_id,
            count=req.count,
        )
        return NarrativeTreeResponse.model_validate(tree)
    except NarrativeTreeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LLMConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("扩展节点失败: tree=%s, node=%s — %s", tree_id, req.node_id, e)
        raise HTTPException(status_code=500, detail=f"扩展节点失败: {e}") from e


@router.post(
    "/{project_id}/narrative-trees/{tree_id}/generate-outlines",
    response_model=GenerateOutlinesResponse,
    summary="生成多版本剧情概要",
    description="根据用户选中的叙事树路径，生成 3 个不同风格的剧情概要。",
    responses={
        400: {"description": "路径不连续"},
        404: {"description": "叙事树不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
async def generate_outlines(
    project_id: str,
    tree_id: str,
    req: GenerateOutlinesRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateOutlinesResponse:
    """根据叙事树路径生成多版本剧情概要。"""
    try:
        result = await db.execute(
            select(NarrativeTree).where(
                NarrativeTree.id == tree_id,
                NarrativeTree.project_id == project_id,
            )
        )
        tree = result.scalar_one_or_none()
        if tree is None:
            raise HTTPException(status_code=404, detail=f"叙事树 {tree_id} 不存在")

        # 校验路径
        if not NarrativeTreeService.validate_path(tree.tree_data, req.selected_branch_ids):
            raise HTTPException(
                status_code=400,
                detail="选中的节点不构成从根到叶子的连续路径",
            )

        service = NarrativeTreeService()
        outlines_data, storyline = await service.generate_outlines(
            db=db,
            tree_id=tree_id,
            tree_data=tree.tree_data,
            selected_ids=req.selected_branch_ids,
            user_theme=tree.user_theme,
            styles=req.styles,
        )

        outline_items = [OutlineItem(**o) for o in outlines_data]
        logger.info("概要生成完成: tree=%s, %d个版本", tree_id, len(outline_items))

        return GenerateOutlinesResponse(
            outlines=outline_items,
            storyline=storyline,
        )
    except LLMConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("生成概要失败: tree=%s — %s", tree_id, e)
        raise HTTPException(status_code=500, detail=f"生成概要失败: {e}") from e


@router.post(
    "/{project_id}/narrative-trees/{tree_id}/generate-script",
    response_model=dict,
    summary="从叙事树生成剧本",
    description="根据用户确认的主线分支生成完整剧本。",
    responses={
        400: {"description": "路径不连续或树未确认"},
        404: {"description": "叙事树不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
async def generate_script_from_tree(
    project_id: str,
    tree_id: str,
    req: GenerateScriptFromTreeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """从叙事树选中路径生成剧本。"""
    try:
        # 获取叙事树
        result = await db.execute(
            select(NarrativeTree).where(
                NarrativeTree.id == tree_id,
                NarrativeTree.project_id == project_id,
            )
        )
        tree = result.scalar_one_or_none()
        if tree is None:
            raise HTTPException(status_code=404, detail=f"叙事树 {tree_id} 不存在")

        # 校验路径
        if not NarrativeTreeService.validate_path(tree.tree_data, req.selected_branch_ids):
            raise HTTPException(
                status_code=400,
                detail="选中的节点不构成从根到叶子的连续路径",
            )

        # 构建主线描述
        storyline = NarrativeTreeService.collect_node_texts(
            tree.tree_data, req.selected_branch_ids,
        )
        logger.info("从叙事树构建主线: %s", storyline[:100])

        # 生成剧本（使用主线描述替代原始主题）
        script_service = ScriptGenerationService()
        content = await script_service.generate_script(
            theme=f"根据以下故事主线创作短剧剧本：{storyline}",
            project_name=tree.user_theme[:50],
        )

        # 保存剧本
        from app.models.script import Script
        script = Script(
            project_name=tree.user_theme[:50],
            theme=storyline,
            content=content,
            project_id=project_id,
        )
        db.add(script)
        await db.flush()

        # 更新项目 current_script_id
        project = await project_service.get_project(db, project_id)
        if project:
            project.current_script_id = str(script.id)

        # 更新叙事树状态
        tree.selected_branch_ids = req.selected_branch_ids
        tree.status = "converted"

        await db.commit()
        await db.refresh(script)

        logger.info("从叙事树生成剧本成功: tree=%s, script=%s", tree_id, script.id)

        from app.schemas.script import ScriptDetailResponse
        return {
            "script": ScriptDetailResponse.model_validate(script).model_dump(),
            "storyline": storyline,
        }

    except NarrativeTreeError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except LLMConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except ScriptParseError as e:
        raise HTTPException(status_code=422, detail=f"剧本解析失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("从叙事树生成剧本失败: tree=%s — %s", tree_id, e)
        raise HTTPException(status_code=500, detail=f"生成剧本失败: {e}") from e


@router.get(
    "/{project_id}/narrative-trees/{tree_id}/outlines",
    response_model=list[NarrativeOutlineResponse],
    summary="获取叙事树的所有概要",
    description="获取指定叙事树生成的所有剧情概要。",
    responses={404: {"description": "叙事树不存在"}},
)
async def list_outlines(
    project_id: str,
    tree_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[NarrativeOutlineResponse]:
    """获取叙事树的所有概要。"""
    result = await db.execute(
        select(NarrativeTree).where(
            NarrativeTree.id == tree_id,
            NarrativeTree.project_id == project_id,
        )
    )
    tree = result.scalar_one_or_none()
    if tree is None:
        raise HTTPException(status_code=404, detail=f"叙事树 {tree_id} 不存在")

    from app.models.narrative_outline import NarrativeOutline
    result = await db.execute(
        select(NarrativeOutline)
        .where(NarrativeOutline.narrative_tree_id == tree_id)
        .order_by(NarrativeOutline.created_at.asc())
    )
    outlines = result.scalars().all()
    return [NarrativeOutlineResponse.model_validate(o) for o in outlines]
