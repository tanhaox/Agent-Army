"""
视频任务服务层 - 封装视频生成任务的数据库操作和后台轮询逻辑。

支持 Seedance 2.0 和 Kling AI 两种视频生成后端，通过 VIDEO_PROVIDER 配置切换。
"""

import asyncio
import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.video_task import (
    TASK_STATUS_FAILED,
    TASK_STATUS_PENDING,
    TASK_STATUS_PROCESSING,
    TASK_STATUS_SUCCESS,
    VideoTask,
)

logger = logging.getLogger(__name__)

# 视频本地存储目录
VIDEO_LOCAL_DIR = "static/videos"


async def _download_video_to_local(video_url: str, task_id: str) -> str | None:
    """下载视频到本地存储，返回本地路径（如 /static/videos/xxx.mp4）。"""
    import httpx
    from pathlib import Path

    if not video_url:
        return None

    try:
        Path(VIDEO_LOCAL_DIR).mkdir(parents=True, exist_ok=True)
        local_path = f"{VIDEO_LOCAL_DIR}/{task_id}.mp4"

        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            async with client.stream("GET", video_url) as resp:
                resp.raise_for_status()
                with open(local_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)

        logger.info("视频已下载到本地: %s", local_path)
        return f"/static/videos/{task_id}.mp4"
    except Exception as e:
        logger.warning("下载视频到本地失败: task_id=%s, error=%s", task_id, e)
        return None


def _get_video_provider() -> str:
    return get_settings().VIDEO_PROVIDER.lower()


async def create_video_task(
    db: AsyncSession,
    storyboard_id: str,
    prompt: str,
    mode: str = "std",
    duration: str = "5",
    aspect_ratio: str = "9:16",
    project_id: str | None = None,
    image_urls: list[str] | None = None,
    negative_prompt: str = "",
) -> VideoTask:
    """
    创建视频生成任务。

    Args:
        db: 数据库会话。
        storyboard_id: 关联分镜 ID。
        prompt: 视频提示词。
        mode: 生成模式。
        duration: 视频时长。
        aspect_ratio: 画面比例。
        project_id: 关联项目 ID。
        image_urls: 参考图片 URL 列表（Seedance 多模态输入）。
        negative_prompt: 负面提示词。

    Returns:
        创建的 VideoTask 记录。
    """
    task = VideoTask(
        storyboard_id=str(storyboard_id),
        prompt=prompt,
        mode=mode,
        duration=duration,
        aspect_ratio=aspect_ratio,
        project_id=project_id,
        negative_prompt=negative_prompt or None,
        image_urls=json.dumps(image_urls, ensure_ascii=False) if image_urls else None,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    logger.info("视频任务已创建: id=%s, storyboard_id=%s, provider=%s", task.id, storyboard_id, _get_video_provider())
    return task


async def get_video_task(db: AsyncSession, task_id: uuid.UUID) -> VideoTask | None:
    """根据 ID 获取视频任务。"""
    result = await db.execute(select(VideoTask).where(VideoTask.id == task_id))
    return result.scalar_one_or_none()


async def list_video_tasks(
    db: AsyncSession,
    storyboard_id: str | None = None,
    project_id: str | None = None,
) -> list[VideoTask]:
    """
    获取视频任务列表。

    Args:
        db: 数据库会话。
        storyboard_id: 可选，按分镜 ID 过滤。
        project_id: 可选，按项目 ID 过滤。

    Returns:
        视频任务列表，按创建时间倒序。
    """
    query = select(VideoTask).order_by(VideoTask.created_at.desc())
    if storyboard_id:
        query = query.where(VideoTask.storyboard_id == storyboard_id)
    if project_id:
        query = query.where(VideoTask.project_id == project_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def submit_video_task(db: AsyncSession, task: VideoTask) -> None:
    """
    根据配置的视频生成后端提交任务并启动后台轮询。

    Args:
        db: 数据库会话。
        task: 视频任务对象。
    """
    provider = _get_video_provider()

    try:
        if provider == "seedance":
            await _submit_to_seedance(db, task)
        else:
            await _submit_to_kling(db, task)
    except Exception as e:
        task.status = TASK_STATUS_FAILED
        task.error_message = str(e)
        await db.commit()
        logger.error("提交视频任务失败: task_id=%s, provider=%s, error=%s", task.id, provider, e)


async def _submit_to_seedance(db: AsyncSession, task: VideoTask) -> None:
    """提交到 Seedance 2.0 API。"""
    from app.services.seedance_video_service import SeedanceClient, SeedanceError

    client = SeedanceClient()
    # image_urls 存储为 JSON 字符串，使用时反序列化
    img_urls = json.loads(task.image_urls) if task.image_urls else None
    seedance_task_id = await client.create_task(
        prompt=task.prompt,
        negative_prompt=task.negative_prompt or "",
        image_urls=img_urls,
        duration=int(task.duration) if task.duration else 5,
        aspect_ratio=task.aspect_ratio or "9:16",
    )
    task.provider_task_id = seedance_task_id
    task.status = TASK_STATUS_PROCESSING
    await db.commit()
    logger.info("视频任务已提交到 Seedance: task_id=%s, seedance_id=%s", task.id, seedance_task_id)

    asyncio.create_task(_poll_seedance_task(str(task.id), seedance_task_id))


async def _submit_to_kling(db: AsyncSession, task: VideoTask) -> None:
    """提交到 Kling API。"""
    from app.services.kling_service import KlingClient, KlingAPIError

    client = KlingClient()
    kling_task_id = await client.submit_text2video(
        prompt=task.prompt,
        duration=task.duration,
        aspect_ratio=task.aspect_ratio,
        mode=task.mode,
    )
    task.provider_task_id = kling_task_id
    task.status = TASK_STATUS_PROCESSING
    await db.commit()
    logger.info("视频任务已提交到 Kling: task_id=%s, kling_id=%s", task.id, kling_task_id)

    asyncio.create_task(_poll_kling_task(str(task.id), kling_task_id))


async def _poll_seedance_task(task_id_str: str, seedance_task_id: str) -> None:
    """后台轮询 Seedance 任务状态。"""
    from app.core.database import get_session_maker
    from app.services.seedance_video_service import SeedanceClient, SeedanceError

    session_maker = get_session_maker()

    # Step 1: 调用 Seedance API（不依赖 DB 会话）
    try:
        client = SeedanceClient()
        result = await client.wait_for_completion(seedance_task_id)
        video_url = result.get("video_url")
        success = True
    except SeedanceError as e:
        video_url = None
        error_msg = str(e)
        success = False
        logger.error("Seedance 视频生成失败: task_id=%s, error=%s", task_id_str, e)
    except Exception as e:
        video_url = None
        error_msg = f"内部错误: {e}"
        success = False
        logger.exception("Seedance 轮询异常: task_id=%s", task_id_str)

    # Step 2: 用独立会话更新 DB 状态
    async with session_maker() as db:
        try:
            task = await get_video_task(db, uuid.UUID(task_id_str))
            if task is None:
                logger.error("轮询时找不到任务: %s", task_id_str)
                return
            if success:
                task.status = TASK_STATUS_SUCCESS
                task.video_url = video_url
                # 下载视频到本地存储，避免外部 URL 过期
                local_path = await _download_video_to_local(video_url or "", task_id_str)
                if local_path:
                    task.output_url = local_path
                logger.info("Seedance 视频生成成功: task_id=%s, local=%s", task_id_str, local_path)
            else:
                task.status = TASK_STATUS_FAILED
                task.error_message = error_msg
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.exception("更新视频任务状态失败: task_id=%s", task_id_str)


async def _poll_kling_task(task_id_str: str, kling_task_id: str) -> None:
    """后台轮询 Kling 任务状态。"""
    from app.core.database import get_session_maker
    from app.services.kling_service import KlingClient, KlingAPIError

    session_maker = get_session_maker()

    # Step 1: 调用 Kling API（不依赖 DB 会话）
    try:
        client = KlingClient()
        result = await client.wait_for_completion(kling_task_id)
        video_url = result.get("video_url")
        success = True
    except KlingAPIError as e:
        video_url = None
        error_msg = str(e)
        success = False
        logger.error("Kling 视频生成失败: task_id=%s, error=%s", task_id_str, e)
    except Exception as e:
        video_url = None
        error_msg = f"内部错误: {e}"
        success = False
        logger.exception("Kling 轮询异常: task_id=%s", task_id_str)

    # Step 2: 用独立会话更新 DB 状态
    async with session_maker() as db:
        try:
            task = await get_video_task(db, uuid.UUID(task_id_str))
            if task is None:
                logger.error("轮询时找不到任务: %s", task_id_str)
                return
            if success:
                task.status = TASK_STATUS_SUCCESS
                task.video_url = video_url
                local_path = await _download_video_to_local(video_url or "", task_id_str)
                if local_path:
                    task.output_url = local_path
                logger.info("Kling 视频生成成功: task_id=%s, local=%s", task_id_str, local_path)
            else:
                task.status = TASK_STATUS_FAILED
                task.error_message = error_msg
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.exception("更新视频任务状态失败: task_id=%s", task_id_str)
