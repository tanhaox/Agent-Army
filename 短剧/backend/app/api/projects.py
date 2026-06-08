"""
项目 API 端点 - 项目 CRUD、快照操作、快照对比。
"""

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.schemas.project import (
    CompareRequest,
    CompareResponse,
    GenerateStoryboardsRequest,
    GenerateStoryboardsResponse,
    ProjectCharacterRequest,
    ProjectCharacterResponse,
    ProjectCreate,
    ProjectDashboardResponse,
    ProjectResponse,
    ProjectUpdate,
    SnapshotBriefResponse,
    SnapshotCreateRequest,
    SnapshotDetailResponse,
)
from app.services import project_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


def _safe_static_path(url: str) -> Path | None:
    """将 /static/ URL 映射为安全本地路径，防止路径遍历。"""
    if not url.startswith("/static/"):
        return None
    static_dir = Path("static").resolve()
    relative = url[len("/static/"):]
    resolved = (static_dir / relative).resolve()
    if not str(resolved).startswith(str(static_dir)):
        return None
    return resolved


def _ref_image_exists(url: str) -> bool:
    """检查本地引用图片是否存在。"""
    safe_path = _safe_static_path(url)
    if safe_path is None:
        return bool(url) and url.startswith("http")
    return safe_path.exists()


# ========== 项目 CRUD ==========

@router.post(
    "",
    response_model=ProjectResponse,
    summary="创建项目",
)
async def create_project(
    req: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """创建新项目。"""
    try:
        project = await project_service.create_project(db, name=req.name, description=req.description)
        logger.info("项目已创建: %s (%s)", project.id, project.name)
        return ProjectResponse.model_validate(project)
    except Exception as e:
        logger.error("创建项目失败: %s", e)
        raise HTTPException(status_code=500, detail=f"创建项目失败: {e}") from e


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="获取项目列表",
)
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """获取所有项目。"""
    try:
        projects = await project_service.list_projects(db)
        return [ProjectResponse.model_validate(p) for p in projects]
    except Exception as e:
        logger.error("获取项目列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {e}") from e


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="获取项目详情",
    responses={404: {"description": "项目不存在"}},
)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """根据 ID 获取项目。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        return ProjectResponse.model_validate(project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取项目详情失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"获取项目详情失败: {e}") from e


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="更新项目",
    responses={404: {"description": "项目不存在"}},
)
async def update_project(
    project_id: str,
    req: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """更新项目信息。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        fields = {k: v for k, v in req.model_dump().items() if v is not None}
        project = await project_service.update_project(db, project, **fields)
        logger.info("项目已更新: %s", project_id)
        return ProjectResponse.model_validate(project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("更新项目失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"更新项目失败: {e}") from e


@router.delete(
    "/{project_id}",
    summary="删除项目",
    responses={404: {"description": "项目不存在"}},
)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """删除项目及其所有快照（不删除原始剧本/分镜数据）。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        await project_service.delete_project(db, project)
        logger.info("项目已删除: %s (%s)", project_id, project.name)
        return {"detail": f"项目 {project.name} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除项目失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"删除项目失败: {e}") from e


# ========== 快照操作 ==========

@router.post(
    "/{project_id}/snapshots",
    response_model=SnapshotDetailResponse,
    summary="创建快照",
    description="为项目当前状态创建快照（保存剧本和分镜数据）。",
)
async def create_snapshot(
    project_id: str,
    req: SnapshotCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SnapshotDetailResponse:
    """创建项目快照。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        snapshot = await project_service.create_snapshot(
            db, project,
            snapshot_name=req.snapshot_name,
            remark=req.remark,
        )
        logger.info("快照已创建: %s (项目 %s)", snapshot.id, project_id)
        return SnapshotDetailResponse.model_validate(snapshot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建快照失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"创建快照失败: {e}") from e


@router.get(
    "/{project_id}/snapshots",
    response_model=list[SnapshotBriefResponse],
    summary="获取快照列表",
)
async def list_snapshots(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[SnapshotBriefResponse]:
    """获取项目的所有快照。"""
    try:
        snapshots = await project_service.list_snapshots(db, project_id)
        return [SnapshotBriefResponse.model_validate(s) for s in snapshots]
    except Exception as e:
        logger.error("获取快照列表失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"获取快照列表失败: {e}") from e


@router.get(
    "/{project_id}/snapshots/{snapshot_id}",
    response_model=SnapshotDetailResponse,
    summary="获取快照详情",
    responses={404: {"description": "快照不存在"}},
)
async def get_snapshot(
    project_id: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
) -> SnapshotDetailResponse:
    """获取快照完整数据。"""
    try:
        snapshot = await project_service.get_snapshot(db, snapshot_id)
        if snapshot is None or snapshot.project_id != str(project_id):
            raise HTTPException(status_code=404, detail=f"快照 {snapshot_id} 不存在")
        return SnapshotDetailResponse.model_validate(snapshot)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取快照详情失败: %s — %s", snapshot_id, e)
        raise HTTPException(status_code=500, detail=f"获取快照详情失败: {e}") from e


@router.post(
    "/{project_id}/snapshots/{snapshot_id}/restore",
    response_model=ProjectResponse,
    summary="从快照恢复",
    description="从快照恢复项目数据（创建新剧本和分镜，旧数据保留）。",
)
async def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """从快照恢复项目。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        snapshot = await project_service.get_snapshot(db, snapshot_id)
        if snapshot is None or snapshot.project_id != str(project_id):
            raise HTTPException(status_code=404, detail=f"快照 {snapshot_id} 不存在")
        project = await project_service.restore_snapshot(db, project, snapshot)
        logger.info("快照已恢复: %s → 项目 %s", snapshot_id, project_id)
        return ProjectResponse.model_validate(project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("恢复快照失败: %s → %s — %s", snapshot_id, project_id, e)
        raise HTTPException(status_code=500, detail=f"恢复快照失败: {e}") from e


@router.post(
    "/{project_id}/snapshots/compare",
    response_model=CompareResponse,
    summary="对比两个快照",
    description="对比两个快照的剧本和分镜差异。",
)
async def compare_snapshots(
    project_id: str,
    req: CompareRequest,
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    """对比两个快照。"""
    try:
        result = await project_service.compare_snapshots(
            db, req.snapshot_id_1, req.snapshot_id_2,
        )
        return CompareResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("对比快照失败: %s vs %s — %s", req.snapshot_id_1, req.snapshot_id_2, e)
        raise HTTPException(status_code=500, detail=f"对比快照失败: {e}") from e


# ========== 仪表盘 ==========

@router.get(
    "/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    summary="获取项目仪表盘",
    description="获取项目统计数据和最近活动。",
    responses={404: {"description": "项目不存在"}},
)
async def get_project_dashboard(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectDashboardResponse:
    """获取项目仪表盘。"""
    try:
        dashboard = await project_service.get_project_dashboard(db, project_id)
        if dashboard is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        return ProjectDashboardResponse(
            project=ProjectResponse.model_validate(dashboard["project"]),
            script_count=dashboard["script_count"],
            storyboard_count=dashboard["storyboard_count"],
            character_count=dashboard["character_count"],
            video_task_count=dashboard["video_task_count"],
            recent_scripts=dashboard["recent_scripts"],
            recent_video_tasks=dashboard["recent_video_tasks"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取项目仪表盘失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"获取项目仪表盘失败: {e}") from e


# ========== AI 生成分镜 ==========

@router.post(
    "/{project_id}/generate-storyboards",
    response_model=GenerateStoryboardsResponse,
    summary="AI 自动生成分镜",
    description="根据项目当前剧本内容，调用 AI 自动生成分镜草稿。",
    responses={
        400: {"description": "项目没有剧本"},
        404: {"description": "项目不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
async def generate_storyboards(
    project_id: str,
    req: GenerateStoryboardsRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateStoryboardsResponse:
    """AI 自动生成分镜。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from app.services.storyboard_generation_service import (
            StoryboardGenerationService,
            StoryboardGenerationError,
        )
        from app.services.llm.base import LLMConnectionError, LLMGenerateError

        service = StoryboardGenerationService()
        storyboards = await service.generate_storyboards(
            db, project_id, regenerate=req.regenerate,
        )

        from app.schemas.storyboard import StoryboardResponse
        sb_list = [StoryboardResponse.model_validate(sb).model_dump() for sb in storyboards]

        logger.info("AI 分镜生成完成: project=%s, %d条", project_id, len(sb_list))
        return GenerateStoryboardsResponse(
            generated_count=len(sb_list),
            storyboards=sb_list,
        )
    except StoryboardGenerationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except LLMConnectionError as e:
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI 生成分镜失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"AI 生成分镜失败: {e}") from e


# ========== 项目角色管理 ==========

@router.get(
    "/{project_id}/characters",
    response_model=list[ProjectCharacterResponse],
    summary="获取项目角色列表",
    description="获取项目中关联的所有角色及其剧中角色名。",
    responses={404: {"description": "项目不存在"}},
)
async def list_project_characters(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ProjectCharacterResponse]:
    """获取项目关联的角色列表。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        characters = await project_service.list_project_characters(db, project_id)
        return [ProjectCharacterResponse(**c) for c in characters]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取项目角色列表失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"获取项目角色列表失败: {e}") from e


@router.post(
    "/{project_id}/characters",
    response_model=ProjectCharacterResponse,
    summary="添加角色到项目",
    description="将角色库中的角色添加到项目，可指定剧中角色名。",
    responses={
        400: {"description": "角色已存在或角色不存在"},
        404: {"description": "项目不存在"},
    },
)
async def add_project_character(
    project_id: str,
    req: ProjectCharacterRequest,
    db: AsyncSession = Depends(get_db),
) -> ProjectCharacterResponse:
    """添加角色到项目。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        pc = await project_service.add_project_character(
            db, project_id, req.character_id, req.role_name,
        )
        # 获取角色信息构造响应
        from app.services.character_service import get_character
        char = await get_character(db, req.character_id)
        return ProjectCharacterResponse(
            character_id=pc.character_id,
            character_name=char.name if char else "",
            role_name=pc.role_name,
            traits=char.traits if char else {},
            reference_images=char.reference_images if char else [],
            created_at=pc.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("添加角色到项目失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"添加角色到项目失败: {e}") from e


@router.delete(
    "/{project_id}/characters/{character_id}",
    summary="从项目移除角色",
    responses={404: {"description": "项目不存在"}},
)
async def remove_project_character(
    project_id: str,
    character_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """从项目移除角色。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")
        await project_service.remove_project_character(db, project_id, character_id)
        return {"detail": "角色已从项目移除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("移除项目角色失败: %s/%s — %s", project_id, character_id, e)
        raise HTTPException(status_code=500, detail=f"移除项目角色失败: {e}") from e


@router.post(
    "/{project_id}/generate-characters",
    response_model=list,
    summary="从剧本自动生成角色",
    description="根据项目当前剧本内容，AI 自动分析角色并生成含图片提示词的角色设计。",
    responses={
        400: {"description": "项目无剧本"},
        404: {"description": "项目不存在"},
        503: {"description": "AI 服务不可用"},
    },
)
@limiter.limit("5/minute")
async def generate_characters_from_script(
    request: Request,
    project_id: str,
    req: dict | None = None,
    db: AsyncSession = Depends(get_db),
) -> list:
    """从剧本自动生成角色并关联到项目。"""
    try:
        from sqlalchemy import select

        from app.models.character import Character
        from app.models.script import Script
        from app.services.character_generation_service import (
            CharacterGenerationError,
            generate_characters_from_script as do_generate,
        )
        from app.services.llm import LLMConnectionError, LLMGenerateError

        # 获取项目
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        # 获取当前剧本
        if not project.current_script_id:
            raise HTTPException(status_code=400, detail="项目没有当前剧本，请先生成剧本")

        result = await db.execute(
            select(Script).where(Script.id == project.current_script_id)
        )
        script = result.scalar_one_or_none()
        if script is None:
            raise HTTPException(status_code=400, detail="关联剧本不存在")
        if not script.content:
            raise HTTPException(status_code=400, detail="剧本内容为空，无法分析角色")

        # 提取视觉设定
        visual_settings = None
        if req and req.get("visual_settings"):
            visual_settings = req["visual_settings"]
            logger.info("使用自定义视觉设定: %s", list(visual_settings.keys()))

        # 调用生成服务
        logger.info("开始调用角色生成服务: project=%s", project_id)
        generated = await do_generate(script.content, visual_settings)
        logger.info("角色生成服务返回: %d 个角色", len(generated))

        # 为每个角色创建 Character 记录并关联项目
        from app.models.project_character import ProjectCharacter

        response_list: list[dict] = []
        for char_data in generated:
            char_name = char_data.get("name", "")
            if not char_name:
                logger.warning("跳过无名角色: %s", char_data)
                continue

            # 检查是否已存在同名角色
            existing = await db.execute(
                select(Character).where(Character.name == char_name)
            )
            existing_char = existing.scalar_one_or_none()

            if existing_char:
                existing_char.traits = char_data["traits"]
                character = existing_char
                logger.info("更新已有角色: %s (%s)", char_name, character.id)
            else:
                character = Character(
                    name=char_name,
                    traits=char_data["traits"],
                )
                db.add(character)
                await db.flush()
                logger.info("创建新角色: %s (%s)", char_name, character.id)

            # 关联到项目
            existing_link = await db.execute(
                select(ProjectCharacter).where(
                    ProjectCharacter.project_id == project_id,
                    ProjectCharacter.character_id == str(character.id),
                )
            )
            if existing_link.scalar_one_or_none() is None:
                link = ProjectCharacter(
                    project_id=project_id,
                    character_id=str(character.id),
                    role_name=char_data["traits"].get("role_type", "supporting"),
                )
                db.add(link)
                logger.info("关联角色到项目: %s → %s", char_name, project_id)

            response_list.append({
                "id": str(character.id),
                "name": char_name,
                "traits": char_data["traits"],
                "image_prompt": char_data.get("image_prompt", ""),
            })

        await db.commit()

        logger.info("从剧本生成角色完成: project=%s, %d个角色", project_id, len(response_list))
        return response_list

    except CharacterGenerationError as e:
        logger.error("角色数据解析失败: %s", e, exc_info=True)
        raise HTTPException(status_code=422, detail=f"角色数据解析失败: {e}") from e
    except LLMConnectionError as e:
        logger.error("LLM 连接失败: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail=f"AI 服务不可用: {e}") from e
    except LLMGenerateError as e:
        logger.error("LLM 生成失败: %s", e, exc_info=True)
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {e}") from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("从剧本生成角色失败: project=%s — %s", project_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"生成角色失败: {type(e).__name__}: {e}",
        ) from e


@router.post(
    "/{project_id}/generate-group-prompt",
    summary="生成角色合照 prompt",
    description="根据项目角色的视觉信息生成合照图片提示词，用于宣传海报。",
    responses={404: {"description": "项目不存在"}},
)
async def generate_group_prompt(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """生成角色合照 prompt。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from sqlalchemy import select
        from app.models.project_character import ProjectCharacter
        from app.models.character import Character
        from app.services.character_generation_service import (
            generate_group_prompt as do_group_prompt,
            _normalize_settings,
        )

        # 获取项目角色
        result = await db.execute(
            select(ProjectCharacter).where(
                ProjectCharacter.project_id == project_id
            )
        )
        links = result.scalars().all()
        if not links:
            raise HTTPException(status_code=400, detail="项目暂无角色，请先生成角色")

        characters = []
        for link in links:
            char_result = await db.execute(
                select(Character).where(Character.id == link.character_id)
            )
            char = char_result.scalar_one_or_none()
            if char:
                characters.append({
                    "name": char.name,
                    "traits": char.traits or {},
                })

        if not characters:
            raise HTTPException(status_code=400, detail="无有效角色数据")

        # 从第一个角色的 traits 中提取视觉设定（如果有）
        visual_settings = _normalize_settings({})
        prompt = await do_group_prompt(characters, visual_settings)
        return {"group_prompt": prompt}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("生成合照 prompt 失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"生成合照 prompt 失败: {e}") from e


@router.post(
    "/{project_id}/optimize-storyboards-by-rhythm",
    summary="节奏分析驱动的自动分镜优化",
    description="根据节奏分析结果自动修复分镜问题（添加高潮镜头、悬念结尾、补充分镜等）。",
)
async def optimize_storyboards_by_rhythm(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """自动优化分镜。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from app.services.storyboard_optimizer import optimize_storyboards_by_rhythm as do_optimize
        result = await do_optimize(db, project_id)
        logger.info("分镜优化完成: project=%s, 新增%d, 修改%d", project_id, result["total_added"], result["total_modified"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("分镜优化失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"分镜优化失败: {e}") from e


@router.get(
    "/{project_id}/review-storyboards",
    summary="分镜审核（爆款标准）",
    description="基于短视频爆款标准对项目分镜进行多维度评估，输出评分和改进建议。",
)
async def review_storyboards(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """分镜审核。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from collections import defaultdict
        from sqlalchemy import select
        from app.models.storyboard import Storyboard
        from app.services.storyboard_review_standards import evaluate_project

        result = await db.execute(
            select(Storyboard)
            .where(Storyboard.project_id == project_id)
            .order_by(Storyboard.episode_no, Storyboard.shot_no)
        )
        sbs = result.scalars().all()

        if not sbs:
            raise HTTPException(status_code=404, detail="该项目暂无分镜")

        episodes: dict[int, list[dict]] = defaultdict(list)
        for sb in sbs:
            episodes[sb.episode_no].append({
                "episode_no": sb.episode_no,
                "shot_no": sb.shot_no,
                "shot_type": sb.shot_type,
                "camera_move": sb.camera_move,
                "action": sb.action,
                "emotion": sb.emotion,
                "vfx": sb.vfx or "无",
                "environment": sb.environment,
                "lighting": sb.lighting,
                "duration_seconds": sb.duration_seconds or 5,
                "is_key_moment": sb.is_key_moment or False,
            })

        report = evaluate_project(episodes)
        logger.info("分镜审核完成: project=%s, score=%d", project_id, report["overall_score"])
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error("分镜审核失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"分镜审核失败: {e}") from e


@router.post(
    "/{project_id}/optimize-storyboards-by-review",
    summary="审核驱动的自动分镜优化",
    description="根据审核报告自动修复分镜问题（情绪曲线、钩子密度、悬念结尾等）。",
)
async def optimize_by_review(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """根据审核报告自动优化。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from app.services.storyboard_optimizer import optimize_storyboards_by_rhythm as do_optimize
        result = await do_optimize(db, project_id)
        logger.info("审核优化完成: project=%s", project_id)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("审核优化失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"审核优化失败: {e}") from e


@router.post(
    "/{project_id}/add-climax-shots",
    summary="自动添加高潮镜头",
    description="根据审核报告为指定集（或自动检测）添加情绪高潮镜头，由LLM生成内容。",
)
async def add_climax_shots(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """自动添加高潮镜头。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        from app.services.storyboard_optimizer import add_climax_shots as do_add
        result = await do_add(db, project_id, episodes=None)
        logger.info("高潮镜头添加: project=%s, 新增%d", project_id, result["total_added"])
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("添加高潮镜头失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"添加高潮镜头失败: {e}") from e


@router.post(
    "/{project_id}/reconstruct-storyboards",
    summary="爆款分镜重构",
    description="基于爆款心理机制重新设计分镜。默认仅预览，传 apply=true 时应用到数据库。",
)
async def reconstruct_storyboards(
    project_id: str,
    apply: bool = False,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """爆款分镜重构（预览或应用）。"""
    try:
        project = await project_service.get_project(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail=f"项目 {project_id} 不存在")

        if apply:
            # 应用模式：需要 raw_shots 数据
            return await _apply_reconstruct(db, project_id)

        # 预览模式
        from app.services.blockbuster_reconstructor import reconstruct_storyboards_preview
        result = await reconstruct_storyboards_preview(db, project_id)

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        logger.info("爆款重构预览: project=%s, %d集%d镜", project_id, result["total_episodes"], result["total_shots"])
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("爆款重构失败: %s — %s", project_id, e)
        raise HTTPException(status_code=500, detail=f"爆款重构失败: {e}") from e


async def _apply_reconstruct(db: AsyncSession, project_id: str) -> dict:
    """应用重构：从 session 状态或请求体获取 raw_shots。"""
    from fastapi import Request
    # 通过临时存储获取上一次预览的数据
    from app.services.blockbuster_reconstructor import (
        reconstruct_storyboards_preview,
        reconstruct_storyboards_apply,
    )

    # 先重新生成预览数据（确保一致性），然后应用
    preview = await reconstruct_storyboards_preview(db, project_id)
    if "error" in preview:
        raise HTTPException(status_code=400, detail=preview["error"])

    raw_shots = preview.get("raw_shots", [])
    if not raw_shots:
        raise HTTPException(status_code=400, detail="无可应用的重构数据，请先预览")

    result = await reconstruct_storyboards_apply(db, project_id, raw_shots)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    logger.info("爆款重构已应用: project=%s, %d集%d镜, snapshot=%s",
                project_id, result["total_episodes"], result["total_shots"], result.get("snapshot_id"))
    return result


@router.get(
    "/{project_id}/referenceable-materials",
    summary="获取可引用素材列表（分类）",
    description="返回项目中所有可用于 @引用 的素材，按角色/场景/道具/已生成素材分类。",
)
async def get_referenceable_materials(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.services.project_service import list_project_characters

    # 1. 角色图
    characters: list[dict] = []
    char_list = await list_project_characters(db, project_id)
    for c in char_list:
        name = c.get("character_name", "") or c.get("role_name", "")
        traits = c.get("traits", {})
        if isinstance(traits, dict):
            name = traits.get("name", name) or name
        ref_images = c.get("reference_images", [])
        image_url = ""
        if isinstance(ref_images, list):
            # 优先取实际存在的参考图
            for ref in ref_images:
                candidate = ref.get("url", "") if isinstance(ref, dict) else ref
                if candidate and _ref_image_exists(candidate):
                    image_url = candidate
                    break
            # 回退：取第一个非空 URL
            if not image_url:
                for ref in ref_images:
                    candidate = ref.get("url", "") if isinstance(ref, dict) else ref
                    if candidate:
                        image_url = candidate
                        break
        if name and image_url:
            characters.append({
                "id": c.get("character_id", name),
                "name": name,
                "type": "character",
                "thumbnail_url": image_url,
                "reference_mark": f"@{name}",
            })

    # 2. 遍历项目素材，按类型分类
    from app.services import storyboard_service
    scenes: list[dict] = []
    props: list[dict] = []
    generated_materials: list[dict] = []
    seen_urls: set[str] = set()

    storyboards_list = await storyboard_service.list_storyboards(db, project_id=project_id)
    for sb in storyboards_list:
        pm = sb.pregen_materials
        if not pm or not isinstance(pm, dict):
            continue
        source_label = f"第{sb.episode_no}集 镜{sb.shot_no}"

        # background → scene
        bg = pm.get("background")
        if isinstance(bg, str) and bg not in seen_urls:
            seen_urls.add(bg)
            scenes.append({
                "id": f"bg_{sb.id[:8]}",
                "name": f"背景-{source_label}",
                "type": "scene",
                "thumbnail_url": bg,
                "reference_mark": f"@场景:背景{sb.episode_no}集",
            })

        # vfx_ref → generated_material
        vfx = pm.get("vfx_ref")
        if isinstance(vfx, str) and vfx not in seen_urls:
            seen_urls.add(vfx)
            generated_materials.append({
                "id": f"vfx_{sb.id[:8]}",
                "name": f"特效-{source_label}",
                "type": "material",
                "thumbnail_url": vfx,
                "reference_mark": f"@素材:特效{sb.episode_no}集",
            })

        # props → prop
        prop_dict = pm.get("props")
        if isinstance(prop_dict, dict):
            for prop_name, url in prop_dict.items():
                if isinstance(url, str) and url not in seen_urls:
                    seen_urls.add(url)
                    props.append({
                        "id": f"prop_{sb.id[:8]}_{prop_name[:6]}",
                        "name": prop_name,
                        "type": "prop",
                        "thumbnail_url": url,
                        "reference_mark": f"@道具:{prop_name}",
                    })

        # 其他键 → generated_material
        for key, val in pm.items():
            if key in ("background", "vfx_ref", "props"):
                continue
            if isinstance(val, str) and val not in seen_urls:
                seen_urls.add(val)
                generated_materials.append({
                    "id": f"mat_{sb.id[:8]}_{key[:6]}",
                    "name": f"{key}-{source_label}",
                    "type": "material",
                    "thumbnail_url": val,
                    "reference_mark": f"@素材:{key}",
                })

    return {
        "characters": characters,
        "scenes": scenes,
        "props": props,
        "generated_materials": generated_materials,
    }
