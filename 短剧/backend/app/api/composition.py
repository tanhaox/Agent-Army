"""
合成 API 端点 - 视频合成任务提交和状态查询。
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.composition import CompositionRequest, CompositionResponse
from app.services import composition_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/composition", tags=["后期合成"])


@router.post(
    "/generate-episode",
    response_model=CompositionResponse,
    summary="合成一集完整视频",
    description="根据分镜列表，将视频片段拼接、配音、嵌字幕，输出完整一集。",
)
async def generate_episode(
    req: CompositionRequest,
    db: AsyncSession = Depends(get_db),
) -> CompositionResponse:
    """提交合成任务。"""
    try:
        task_id = await composition_service.start_composition(
            db,
            script_id=req.script_id,
            episode_no=req.episode_no,
            storyboard_ids=req.storyboard_ids,
            project_id=req.project_id,
        )

        task = composition_service.get_composition_status(task_id)
        logger.info("合成任务已提交: %s (第%d集)", task_id, req.episode_no)
        return CompositionResponse(
            id=task["id"],
            script_id=task.get("script_id"),
            episode_no=task["episode_no"],
            status=task["status"],
            output_url=task.get("output_url"),
            error_message=task.get("error_message"),
            progress=task.get("progress"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("合成任务提交失败: %s", e)
        raise HTTPException(status_code=500, detail=f"合成任务提交失败: {e}") from e


@router.get(
    "/task/{task_id}",
    response_model=CompositionResponse,
    summary="查询合成任务状态",
    responses={404: {"description": "任务不存在"}},
)
async def get_composition_task(task_id: str) -> CompositionResponse:
    """查询合成任务状态。"""
    try:
        task = composition_service.get_composition_status(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"合成任务 {task_id} 不存在")
        return CompositionResponse(
            id=task["id"],
            script_id=task.get("script_id"),
            episode_no=task["episode_no"],
            status=task["status"],
            output_url=task.get("output_url"),
            error_message=task.get("error_message"),
            progress=task.get("progress"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查询合成任务失败: %s — %s", task_id, e)
        raise HTTPException(status_code=500, detail=f"查询合成任务失败: {e}") from e


@router.get(
    "",
    response_model=list[CompositionResponse],
    summary="获取所有合成任务",
)
async def list_compositions(
    project_id: str | None = Query(default=None, description="按项目 ID 过滤"),
) -> list[CompositionResponse]:
    """获取所有合成任务。"""
    try:
        tasks = composition_service.list_compositions(project_id=project_id)
        return [
            CompositionResponse(
                id=t["id"],
                script_id=t.get("script_id"),
                episode_no=t["episode_no"],
                status=t["status"],
                output_url=t.get("output_url"),
                error_message=t.get("error_message"),
                progress=t.get("progress"),
            )
            for t in tasks
        ]
    except Exception as e:
        logger.error("获取合成任务列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取合成任务列表失败: {e}") from e
