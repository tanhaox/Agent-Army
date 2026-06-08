"""
视频任务 API 端点 - 视频生成任务提交、查询。
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.video_task import VideoGenerateRequest, VideoTaskResponse
from app.services import video_task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video-tasks", tags=["视频生成"])


@router.post(
    "",
    response_model=VideoTaskResponse,
    summary="提交视频生成任务",
    description="根据分镜提示词提交视频生成任务到 Kling API。",
)
async def create_video_task(
    req: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> VideoTaskResponse:
    """提交视频生成任务。"""
    try:
        task = await video_task_service.create_video_task(
            db,
            storyboard_id=req.storyboard_id,
            prompt=req.prompt,
            mode=req.mode,
            duration=req.duration,
            aspect_ratio=req.aspect_ratio,
            project_id=req.project_id,
        )

        # 提交到 Kling API（内部会启动后台轮询）
        await video_task_service.submit_to_kling(db, task)

        # 重新读取以获取最新状态
        await db.refresh(task)
        logger.info("视频任务已创建: %s", task.id)
        return VideoTaskResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建视频任务失败: %s", e)
        raise HTTPException(status_code=500, detail=f"创建视频任务失败: {e}") from e


@router.get(
    "",
    response_model=list[VideoTaskResponse],
    summary="获取视频任务列表",
    description="获取所有视频生成任务，可选按分镜 ID 过滤。",
)
async def list_video_tasks(
    storyboard_id: str | None = Query(default=None, description="按分镜 ID 过滤"),
    project_id: str | None = Query(default=None, description="按项目 ID 过滤"),
    db: AsyncSession = Depends(get_db),
) -> list[VideoTaskResponse]:
    """获取视频任务列表。"""
    try:
        tasks = await video_task_service.list_video_tasks(
            db, storyboard_id=storyboard_id, project_id=project_id,
        )
        return [VideoTaskResponse.model_validate(t) for t in tasks]
    except Exception as e:
        logger.error("获取视频任务列表失败: %s", e)
        raise HTTPException(status_code=500, detail=f"获取视频任务列表失败: {e}") from e


@router.get(
    "/{task_id}",
    response_model=VideoTaskResponse,
    summary="获取视频任务详情",
    responses={404: {"description": "任务不存在"}},
)
async def get_video_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> VideoTaskResponse:
    """根据 ID 获取视频任务详情。"""
    try:
        task = await video_task_service.get_video_task(db, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail=f"视频任务 {task_id} 不存在")
        return VideoTaskResponse.model_validate(task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取视频任务详情失败: %s — %s", task_id, e)
        raise HTTPException(status_code=500, detail=f"获取视频任务详情失败: {e}") from e
