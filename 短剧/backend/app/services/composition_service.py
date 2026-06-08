"""
合成编排服务 - 串联视频下载、TTS 配音、FFmpeg 拼接、字幕嵌入的完整流水线。

合成流程:
  1. 获取分镜对应的已成功视频片段
  2. 下载视频到临时目录
  3. 对有对话的分镜生成 TTS 音频
  4. 将 TTS 音频与视频合并
  5. 拼接所有片段
  6. 生成 SRT 字幕并嵌入
  7. 转码为最终格式
  8. 返回输出文件 URL
"""

import asyncio
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.storyboard import Storyboard
from app.models.video_task import TASK_STATUS_SUCCESS, VideoTask
from app.services import subtitle_service
from app.services.ffmpeg_service import FFmpegError
from app.services import ffmpeg_service, tts_service

logger = logging.getLogger(__name__)

# 合成输出根目录
OUTPUT_DIR = Path("static/compositions")

# 合成任务内存状态（第一期不建表，用内存字典 + 文件系统）
_composition_tasks: dict[str, dict[str, Any]] = {}


def _ensure_output_dir() -> Path:
    """确保合成输出目录存在。"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


async def start_composition(
    db: AsyncSession,
    script_id: str | None,
    episode_no: int,
    storyboard_ids: list[str],
    project_id: str | None = None,
) -> str:
    """
    创建并启动合成任务。

    Args:
        db: 数据库会话。
        script_id: 剧本 ID。
        episode_no: 集数。
        storyboard_ids: 要合成的分镜 ID 列表。
        project_id: 关联项目 ID。

    Returns:
        合成任务 ID。
    """
    task_id = str(uuid.uuid4())
    _composition_tasks[task_id] = {
        "id": task_id,
        "script_id": script_id,
        "episode_no": episode_no,
        "storyboard_ids": storyboard_ids,
        "project_id": project_id,
        "status": "pending",
        "output_url": None,
        "error_message": None,
        "progress": "已提交",
    }
    logger.info("合成任务已创建: id=%s, episode=%d, 分镜数=%d", task_id, episode_no, len(storyboard_ids))

    # 后台执行合成
    asyncio.create_task(_run_composition(task_id))

    return task_id


def get_composition_status(task_id: str) -> dict[str, Any] | None:
    """
    查询合成任务状态。

    Args:
        task_id: 合成任务 ID。

    Returns:
        任务状态字典，不存在返回 None。
    """
    return _composition_tasks.get(task_id)


def list_compositions(project_id: str | None = None) -> list[dict[str, Any]]:
    """获取所有合成任务，可选按项目过滤。"""
    tasks = list(_composition_tasks.values())
    if project_id:
        tasks = [t for t in tasks if t.get("project_id") == project_id]
    return tasks


async def _run_composition(task_id: str) -> None:
    """
    后台执行完整合成流水线。

    Args:
        task_id: 合成任务 ID。
    """
    from app.core.database import get_session_maker

    task = _composition_tasks[task_id]
    session_maker = get_session_maker()

    async with session_maker() as db:
        try:
            task["status"] = "processing"
            task["progress"] = "获取分镜数据..."

            # 1. 获取分镜数据
            storyboards = await _fetch_storyboards(db, task["storyboard_ids"])
            if not storyboards:
                raise ValueError("未找到指定的分镜")

            # 2. 获取已完成的视频任务
            task["progress"] = "检查视频片段..."
            video_map = await _fetch_video_urls(db, task["storyboard_ids"])
            missing = [sid for sid in task["storyboard_ids"] if sid not in video_map]
            if missing:
                raise ValueError(f"以下分镜未生成视频: {missing[:5]}")

            # 3. 创建临时工作目录
            with tempfile.TemporaryDirectory(prefix="composition_") as tmpdir:
                # 4. 下载视频片段
                task["progress"] = f"下载 {len(video_map)} 个视频片段..."
                local_videos = await _download_videos(video_map, tmpdir)

                # 5. TTS 配音 + 音视频合并
                task["progress"] = "生成配音..."
                dubbed_videos = await _generate_and_merge_tts(
                    storyboards, local_videos, tmpdir
                )

                # 6. 拼接视频
                task["progress"] = "拼接视频片段..."
                _ensure_output_dir()
                concat_path = os.path.join(tmpdir, "concat_output.mp4")
                if len(dubbed_videos) > 1:
                    await ffmpeg_service.concat_videos(dubbed_videos, concat_path)
                else:
                    concat_path = dubbed_videos[0]

                # 7. 生成并嵌入字幕
                task["progress"] = "生成字幕..."
                srt_content = subtitle_service.generate_srt(
                    [_sb_to_dict(sb) for sb in storyboards]
                )
                subtitled_path = concat_path
                if srt_content.strip():
                    srt_path = os.path.join(tmpdir, "subtitles.srt")
                    subtitle_service.save_srt(srt_content, srt_path)
                    subtitled_path = os.path.join(tmpdir, "subtitled.mp4")
                    await ffmpeg_service.embed_subtitle(concat_path, srt_path, subtitled_path)

                # 8. 转码为最终格式
                task["progress"] = "转码中..."
                final_name = f"ep{task['episode_no']}_{task_id[:8]}.mp4"
                final_path = str(OUTPUT_DIR / final_name)
                await ffmpeg_service.convert_format(
                    subtitled_path, final_path,
                    target_resolution=(1080, 1920),
                    target_bitrate="2M",
                )

                # 9. 完成
                task["status"] = "success"
                task["output_url"] = f"/static/compositions/{final_name}"
                task["progress"] = "合成完成"
                logger.info("合成完成: task_id=%s, output=%s", task_id, final_name)

        except Exception as e:
            task["status"] = "failed"
            task["error_message"] = str(e)
            task["progress"] = f"失败: {str(e)[:100]}"
            logger.exception("合成失败: task_id=%s", task_id)


async def _fetch_storyboards(
    db: AsyncSession,
    storyboard_ids: list[str],
) -> list[Storyboard]:
    """从数据库获取分镜列表。"""
    result = await db.execute(
        select(Storyboard)
        .where(Storyboard.id.in_(storyboard_ids))
        .order_by(Storyboard.episode_no, Storyboard.shot_no)
    )
    return list(result.scalars().all())


async def _fetch_video_urls(
    db: AsyncSession,
    storyboard_ids: list[str],
) -> dict[str, str]:
    """
    获取分镜对应的已完成视频 URL。

    Returns:
        {storyboard_id: video_url} 映射。
    """
    result = await db.execute(
        select(VideoTask)
        .where(
            VideoTask.storyboard_id.in_(storyboard_ids),
            VideoTask.status == TASK_STATUS_SUCCESS,
        )
    )
    tasks = result.scalars().all()

    video_map: dict[str, str] = {}
    for vt in tasks:
        if vt.video_url:
            video_map[str(vt.storyboard_id)] = vt.video_url
    return video_map


async def _download_videos(
    video_map: dict[str, str],
    tmpdir: str,
) -> list[str]:
    """
    下载视频片段到本地临时目录。

    Returns:
        本地文件路径列表（按 storyboard_ids 顺序）。
    """
    local_paths: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=60) as client:
        for sb_id, url in video_map.items():
            filename = f"segment_{sb_id[:8]}.mp4"
            local_path = os.path.join(tmpdir, filename)
            resp = await client.get(url)
            resp.raise_for_status()
            with open(local_path, "wb") as f:
                f.write(resp.content)
            local_paths[sb_id] = local_path
            logger.debug("视频已下载: %s -> %s", url[:60], local_path)

    # 按 storyboard_ids 顺序排列
    ordered = [local_paths[sid] for sid in video_map if sid in local_paths]
    return ordered


async def _generate_and_merge_tts(
    storyboards: list[Storyboard],
    video_paths: list[str],
    tmpdir: str,
) -> list[str]:
    """
    为有对话的分镜生成 TTS 并合并到视频中。

    Returns:
        合并后的视频路径列表。
    """
    # 建立 storyboard_id -> video_path 映射
    sb_id_to_path: dict[str, str] = {}
    for idx, sb in enumerate(storyboards):
        if idx < len(video_paths):
            sb_id_to_path[str(sb.id)] = video_paths[idx]

    result_paths: list[str] = []

    for idx, sb in enumerate(storyboards):
        video_path = video_paths[idx] if idx < len(video_paths) else None
        if not video_path:
            continue

        # 如果有对话，生成 TTS 并合并
        if sb.dialogue and sb.dialogue.strip():
            audio_path = os.path.join(tmpdir, f"tts_{str(sb.id)[:8]}.mp3")
            await tts_service.generate_speech_to_file(
                sb.dialogue.strip(),
                audio_path,
            )
            merged_path = os.path.join(tmpdir, f"merged_{str(sb.id)[:8]}.mp4")
            await ffmpeg_service.merge_audio_video(video_path, audio_path, merged_path)
            result_paths.append(merged_path)
        else:
            result_paths.append(video_path)

    return result_paths


def _sb_to_dict(sb: Storyboard) -> dict:
    """将 Storyboard 模型转为字典（用于字幕生成）。"""
    return {
        "episode_no": sb.episode_no,
        "shot_no": sb.shot_no,
        "dialogue": sb.dialogue,
    }
