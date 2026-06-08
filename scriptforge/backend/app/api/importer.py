import asyncio
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.progress import ProgressStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["Import"])


# ── Sync ASR runner (for thread-pool execution in parallel pipeline) ──
def _run_asr_sync(audio_path: str, timeout: int = 600) -> dict | None:
    """Run ASR subprocess synchronously and return parsed result dict."""
    import subprocess as _sp
    from pathlib import Path as _P

    _asr_worker = _P(__file__).resolve().parent.parent / "services" / "asr_worker.py"

    # Use venv python to ensure all dependencies are available
    _venv_python = _P(__file__).resolve().parent.parent.parent / ".venv-py312" / "Scripts" / "python.exe"
    _python = str(_venv_python) if _venv_python.exists() else sys.executable

    proc = _sp.Popen(
        [_python, str(_asr_worker), audio_path],
        stdout=_sp.PIPE, stderr=_sp.PIPE,
        encoding="utf-8", errors="replace",
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except _sp.TimeoutExpired:
        proc.kill()
        proc.wait()
        raise RuntimeError(f"ASR worker timed out after {timeout}s")

    if proc.returncode != 0:
        err = stderr[:200] if stderr else "unknown error"
        raise RuntimeError(f"ASR worker exit {proc.returncode}: {err}")

    # Parse stdout lines — last "done" event contains the full result
    for line in reversed(stdout.strip().split("\n")):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("phase") == "done":
                return {
                    "text": data["text"],
                    "segments": data["segments"],
                    "duration": data["duration"],
                }
        except json.JSONDecodeError:
            continue

    return None


# ── Asset saving helper (async, for streaming/online path) ──
async def _save_asset_async(
    task_id: str,
    anchor_name: str,
    video_title: str,
    asset_type: str,
    file_path: str,
    file_size: int = 0,
    duration: float = 0.0,
    transcription_text: str | None = None,
):
    """Insert an asset record — usable inside an existing async context."""
    from app.core.database import async_session_factory
    from app.models.asset import Asset, AssetType

    try:
        async with async_session_factory() as session:
            asset = Asset(
                task_id=task_id,
                anchor_name=anchor_name,
                video_title=video_title[:500],
                asset_type=AssetType(asset_type),
                file_path=file_path,
                file_size=file_size,
                duration=duration,
                transcription_text=transcription_text,
            )
            session.add(asset)
            await session.commit()
    except Exception as e:
        logger.warning("Failed to save asset record: %s", e)


class ImportRequest(BaseModel):
    url: str


class DouyinUserRequest(BaseModel):
    url: str = Field(..., description="抖音用户主页链接")
    count: int = Field(default=5, ge=1, le=20, description="下载视频数量")
    exclude_persona_id: str | None = Field(default=None, description="排除此人设已处理的视频")


class DouyinUserProfileRequest(BaseModel):
    url: str = Field(..., description="抖音用户主页链接")


@router.post("/url")
async def import_from_url(req: ImportRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    try:
        from app.services.importer import check_url_support
        check_url_support(url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        from app.services.importer import VideoImporter, VideoImportError
        result = await asyncio.to_thread(VideoImporter().import_and_transcribe, url)
        return {
            "task_id": str(uuid.uuid4()),
            "status": "SUCCESS",
            "result": result,
        }
    except VideoImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Import failed for %s", url)
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")


@router.get("/task/{task_id}")
async def get_import_task_status(task_id: str):
    """Poll task status from TaskRecord with step-level progress details."""
    from sqlalchemy import select
    from app.core.database import get_db
    from app.models.task_record import TaskRecord

    async for db in get_db():
        row = (await db.execute(
            select(TaskRecord).where(TaskRecord.task_id == task_id)
        )).scalar_one_or_none()
        break

    if not row:
        return {"task_id": task_id, "status": "not_found"}

    rs = row.result_summary or {}
    status = row.status

    if status == "running":
        return {
            "task_id": task_id,
            "status": "processing",
            "step": rs.get("step", ""),
            "message": rs.get("message", ""),
            "current": rs.get("current"),
            "total": rs.get("total"),
            "progress_pct": rs.get("progress_pct"),
            "meta": rs,
            "profile": rs.get("profile"),
            "follower_count": rs.get("follower_count"),
        }
    elif status == "completed":
        return {
            "task_id": task_id,
            "status": "completed",
            "result_summary": rs,
        }
    elif status == "failed":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": row.error_message or rs.get("error", "任务执行失败"),
            "meta": rs,
        }
    else:
        return {"task_id": task_id, "status": status}


@router.post("/douyin-user-profile")
def get_douyin_user_profile(req: DouyinUserProfileRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    try:
        from app.services.douyin_service import DouyinDownloader
        downloader = DouyinDownloader()
        profile = downloader.get_user_profile(url)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Douyin user profile fetch failed for %s", url)
        raise HTTPException(status_code=500, detail=f"获取博主信息失败: {e}")


@router.post("/douyin-user")
def import_douyin_user_videos(req: DouyinUserRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    try:
        from app.services.douyin_service import DouyinUserDownloader
        downloader = DouyinUserDownloader()
        results = downloader.download_user_top_videos(url, count=req.count)

        downloaded = [r for r in results if r["status"] == "downloaded"]
        failed = [r for r in results if r["status"] == "failed"]

        if not downloaded and failed:
            raise HTTPException(
                status_code=422,
                detail=f"所有视频下载失败: {failed[0].get('error', '未知错误')}",
            )

        return {
            "total": len(results),
            "downloaded": downloaded,
            "failed": failed,
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Douyin user import failed for %s", url)
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")


@router.post("/douyin-user/task")
async def submit_douyin_user_task(req: DouyinUserRequest):
    """提交异步任务：下载并处理抖音用户视频。

    立即返回 task_id，后台 asyncio 任务执行完整流水线：
    获取信息 → 翻页搜索 → 下载 → 转写 → AI分析 → 保存人设 → 生成策略

    前端通过 GET /api/import/task/{task_id} 轮询进度。
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")

    try:
        from app.tasks.importer_tasks import process_douyin_user_task
        task_id = str(uuid.uuid4())
        asyncio.create_task(asyncio.to_thread(process_douyin_user_task, url, req.count, task_id))
        return {
            "task_id": task_id,
            "status": "queued",
            "message": f"任务已提交，将处理 Top {req.count} 视频",
        }
    except Exception as e:
        logger.exception("Failed to submit douyin user task")
        raise HTTPException(status_code=500, detail=f"任务提交失败: {e}")


@router.get("/douyin-user/tasks")
async def list_douyin_user_tasks():
    """列出当前活跃的 douyin-user 处理任务。"""
    try:
        from sqlalchemy import select
        from app.core.database import get_db
        from app.models.task_record import TaskRecord

        tasks = []
        async for db in get_db():
            rows = (await db.execute(
                select(TaskRecord).where(
                    TaskRecord.trigger == "douyin_user_import",
                    TaskRecord.status == "running",
                ).order_by(TaskRecord.created_at.desc())
            )).scalars().all()
            for r in rows:
                tasks.append({
                    "task_id": r.task_id,
                    "status": "processing",
                    "url": r.url,
                })
            break

        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.warning("Failed to list tasks: %s", e)
        return {"tasks": [], "count": 0, "error": str(e)}


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}秒"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}分{secs}秒"


def _format_size(n_bytes: float) -> str:
    if n_bytes < 1024:
        return f"{n_bytes:.0f} B"
    if n_bytes < 1048576:
        return f"{n_bytes / 1024:.1f} KB"
    return f"{n_bytes / 1048576:.1f} MB"


async def _read_worker_lines(proc, callback):
    """Read subprocess stdout line by line, call callback for each parsed JSON line."""
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, proc.stdout.readline)
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        await callback(data)


@router.post("/douyin-user/stream")
async def douyin_user_import_stream(req: DouyinUserRequest):
    """流式导入抖音用户视频，含搜索增强步骤，SSE 实时推送进度。"""

    async def event_generator():
        import subprocess as _sp
        from pathlib import Path as _P
        from app.core.database import async_session_factory as _async_sf
        from app.models.task_record import TaskRecord as _TR

        _procs: list[_sp.Popen] = []  # Track subprocesses for cleanup on disconnect
        url = req.url.strip()
        count = req.count
        task_id = str(uuid.uuid4())

        # Create TaskRecord at start
        try:
            async with _async_sf() as _tr_db:
                _tr = _TR(
                    task_id=task_id, trigger="stream", url=url,
                    status="running",
                )
                _tr_db.add(_tr)
                await _tr_db.commit()
        except Exception as _tr_err:
            logger.warning("Failed to create TaskRecord: %s", _tr_err)

        def _update_task_record(**kwargs):
            """Schedule a TaskRecord update (fire-and-forget via asyncio.create_task)."""
            async def _do():
                try:
                    from sqlalchemy import select as _sa_select
                    async with _async_sf() as _tr_db:
                        _row = (await _tr_db.execute(
                            _sa_select(_TR).where(_TR.task_id == task_id)
                        )).scalar_one_or_none()
                        if _row:
                            for k, v in kwargs.items():
                                setattr(_row, k, v)
                            await _tr_db.commit()
                except Exception as e:
                    logger.warning("Failed to update TaskRecord: %s", e)
            asyncio.create_task(_do())

        # ── Live counters for incremental TaskRecord updates (Bug 2 fix) ──
        _live_dl_count = 0
        _live_tr_count = 0

        def _increment_task_counts(dl: bool = False, tr: bool = False):
            """Increment downloaded_count / transcribed_count on TaskRecord."""
            nonlocal _live_dl_count, _live_tr_count
            updates: dict = {}
            if dl:
                _live_dl_count += 1
                updates["downloaded_count"] = _live_dl_count
                updates["result_summary"] = {"current_step": "downloading", "message": f"已下载 {_live_dl_count}/{total or '?'}", "progress_pct": min(20 + _live_dl_count * 8, 50)}
            if tr:
                _live_tr_count += 1
                updates["transcribed_count"] = _live_tr_count
                updates["result_summary"] = {"current_step": "transcribing", "message": f"已转写 {_live_tr_count}/{total or '?'}", "progress_pct": min(50 + _live_tr_count * 8, 70)}
            if updates:
                _update_task_record(**updates)

        # === Step 0: 返回 task_id ===
        yield _sse({"step": "task_init", "task_id": task_id, "message": "任务已启动"})

        # === Step 1: 获取博主信息 ===
        yield _sse({"step": ProgressStep.FETCHING_PROFILE, "message": "正在获取博主信息..."})
        try:
            from app.services.douyin_service import DouyinDownloader
            downloader = DouyinDownloader()
            profile = await asyncio.to_thread(downloader.get_user_profile, url)
            follower_count = profile.get("follower_count", 0)
            fc_str = f"{follower_count / 10000:.1f}万" if follower_count >= 10000 else str(follower_count)
            yield _sse({
                "step": "profile_done",
                "message": f"已获取博主: {profile.get('anchor_name')}（{fc_str} 粉丝）",
                "profile": profile,
                "follower_count": follower_count,
            })
            _update_task_record(
                anchor_name=profile.get("anchor_name", ""),
                anchor_avatar=profile.get("avatar_url"),
                follower_count=follower_count,
                result_summary={"current_step": "profile_done", "message": f"博主: {profile.get('anchor_name', '')}", "progress_pct": 10},
            )
        except Exception as e:
            yield _sse({"step": ProgressStep.ERROR, "message": f"获取博主信息失败: {e}"})
            _update_task_record(status="failed", error_message=str(e)[:500])
            return

        anchor_name = profile.get("anchor_name", "") if profile else ""

        # === Step 2-4: 获取视频列表 + 筛选排序 + Top N（流式 Popen） ===
        yield _sse({"step": ProgressStep.FETCHING_VIDEO_LIST, "message": "正在搜索视频列表..."})

        # 查询已处理的视频 ID（补充素材模式）
        exclude_ids: set[str] = set()
        if req.exclude_persona_id:
            try:
                from sqlalchemy import select as _ex_select
                from app.models.persona_slice import PersonaSlice as _PSlice
                async with _async_sf() as _edb:
                    _rows = await _edb.execute(
                        _ex_select(_PSlice.source_url)
                        .where(_PSlice.persona_id == uuid.UUID(req.exclude_persona_id))
                        .where(_PSlice.source_url.isnot(None))
                    )
                    for (_src_url,) in _rows.all():
                        if _src_url and "/video/" in _src_url:
                            _aid = _src_url.rsplit("/", 1)[-1].split("?")[0]
                            exclude_ids.add(_aid)
                if exclude_ids:
                    yield _sse({
                        "step": "exclude_loaded",
                        "message": f"已排除 {len(exclude_ids)} 个已学习视频",
                        "excluded_count": len(exclude_ids),
                    })
            except Exception as _ex:
                logger.warning("Failed to load exclude list: %s", _ex)

        _worker = _P(__file__).resolve().parent.parent / "services" / "douyin_video_list_worker.py"
        _log_dir = _P(__file__).resolve().parent.parent.parent / "logs"
        _log_dir.mkdir(parents=True, exist_ok=True)

        video_ids = []

        # Use Popen for real-time stdout streaming (same pattern as ASR)
        _exclude_arg = ",".join(exclude_ids) if exclude_ids else ""
        _proc = await asyncio.to_thread(
            _sp.Popen,
            [sys.executable, str(_worker),
             profile.get("sec_uid") or profile.get("anchor_id") or "",
             str(count),
             _exclude_arg],
            stdout=_sp.PIPE,
            stderr=_sp.PIPE,
            encoding="utf-8",
            errors="replace",
        )
        _procs.append(_proc)

        # Stream stdout line by line, yielding SSE events in real time
        def _read_proc_lines():
            for line in iter(_proc.stdout.readline, ""):
                yield line.strip()

        for line in await asyncio.to_thread(list, _read_proc_lines()):
            if not line:
                continue
            # Also write to playwright log
            with open(_log_dir / "playwright.log", "a", encoding="utf-8") as _log_fh:
                _log_fh.write(line + "\n")
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            step = data.get("step")
            if step == "fetching_video_list":
                yield _sse({
                    "step": ProgressStep.FETCHING_VIDEO_LIST,
                    "message": f"正在搜索视频列表（第 {data['page']} 页，已发现 {data['total_collected']} 个作品）...",
                    "page": data["page"],
                    "total_collected": data["total_collected"],
                })
            elif step == "filtering":
                yield _sse({
                    "step": ProgressStep.FILTERING_AND_SORTING,
                    "message": f"正在筛选（时长 {15}-{180} 秒），{data['total_before_filter']} 个作品中 {data['filtered_count']} 个符合条件...",
                    "total_before_filter": data["total_before_filter"],
                    "filtered_count": data["filtered_count"],
                })
            elif step == "top_selected":
                play_str = " / ".join(data.get("play_strs", []))
                yield _sse({
                    "step": ProgressStep.TOP_SELECTED,
                    "message": f"已选定 Top {data['selected_count']} 视频（播放量：{play_str}）",
                    "selected_count": data["selected_count"],
                    "top_videos": data.get("top_videos", []),
                })
                _update_task_record(
                    video_count=data["selected_count"],
                    result_summary={"current_step": "top_selected", "message": f"已选定 {data['selected_count']} 个视频", "progress_pct": 20},
                )
            elif step == "done":
                video_ids = data.get("video_ids", [])
            elif step == "error":
                yield _sse({"step": ProgressStep.ERROR, "message": data["error"]})
                _update_task_record(status="failed", error_message=data["error"][:500])
                return

        _proc.wait(timeout=10)

        if _proc.returncode != 0 and not video_ids:
            stderr = _proc.stderr.read() if _proc.stderr else ""
            logger.error("Video list worker failed (exit %d): %s", _proc.returncode, stderr[:200])
            yield _sse({"step": ProgressStep.ERROR, "message": "获取视频列表失败，详情请查看 logs/playwright.log"})
            _update_task_record(status="failed", error_message=f"Video list worker exit {_proc.returncode}")
            return

        if not video_ids:
            yield _sse({"step": ProgressStep.ERROR, "message": "该用户暂无公开视频或 cookies 已过期"})
            _update_task_record(status="failed", error_message="该用户暂无公开视频或 cookies 已过期")
            return

        yield _sse({
            "step": "video_list_done",
            "message": f"视频列表搜索完成，共选定 {len(video_ids)} 个视频",
            "total": len(video_ids),
        })
        _update_task_record(video_count=len(video_ids))

        # === Steps 5-7: Two-pass pipeline: Download ALL → Build Voice Profile → Batch Transcribe ===
        results: list = []
        total = len(video_ids)
        event_queue: asyncio.Queue = asyncio.Queue()
        downloaded_audios: list[dict] = []  # Collected for voice profile + batch transcription

        download_sem = asyncio.Semaphore(3)
        transcribe_sem = asyncio.Semaphore(1)

        # ── Phase 1: Download ALL videos (no transcription yet) ──
        async def download_one_video(idx: int, vid: dict):
            """Download one video, save video+audio assets, collect for batch transcription."""
            title = vid.get("desc", "") or vid.get("aweme_id", "")
            video_duration = vid.get("duration", 0)

            await event_queue.put({
                "step": ProgressStep.DOWNLOADING_VIDEOS,
                "message": f"[{idx + 1}/{total}] 开始下载：《{title[:30]}》...",
                "current": idx + 1, "total": total, "title": title, "phase": "start",
            })

            audio_path = None
            try:
                async with download_sem:
                    start_time = time.time()
                    audio_path = await asyncio.to_thread(downloader.download_video, vid["url"])
                    download_time = time.time() - start_time

                mp4_path = audio_path.replace(".wav", ".mp4") if audio_path and audio_path.endswith(".wav") else audio_path
                file_size = os.path.getsize(mp4_path) if mp4_path and os.path.exists(mp4_path) else 0

                await _save_asset_async(
                    task_id=task_id, anchor_name=anchor_name,
                    video_title=title, asset_type="video",
                    file_path=mp4_path, file_size=file_size, duration=video_duration,
                )
                if audio_path and os.path.exists(audio_path):
                    await _save_asset_async(
                        task_id=task_id, anchor_name=anchor_name,
                        video_title=title, asset_type="audio",
                        file_path=audio_path, file_size=os.path.getsize(audio_path),
                        duration=video_duration,
                    )

                await event_queue.put({
                    "step": ProgressStep.DOWNLOADING_VIDEOS,
                    "message": f"[{idx + 1}/{total}] 下载完成：《{title[:30]}》（{_format_size(file_size)}，{download_time:.1f}s）",
                    "current": idx + 1, "total": total, "title": title, "phase": "done",
                    "file_size": file_size, "download_seconds": round(download_time, 1),
                })
                _increment_task_counts(dl=True)

                await event_queue.put({
                    "step": ProgressStep.EXTRACTING_AUDIO,
                    "message": f"[{idx + 1}/{total}] 音频已提取",
                    "current": idx + 1, "total": total, "phase": "done",
                })

                # Collect for batch transcription
                downloaded_audios.append({
                    "idx": idx, "vid": vid, "title": title,
                    "audio_path": audio_path, "duration": video_duration,
                })

            except Exception as e:
                logger.error("Failed to download video %s: %s", vid.get("aweme_id"), e)
                results.append({
                    "index": idx + 1, "aweme_id": vid.get("aweme_id", ""),
                    "desc": vid.get("desc", ""), "source_url": vid["url"],
                    "author": vid.get("author", ""), "duration": vid.get("duration", 0),
                    "play_count": vid.get("play_count", 0),
                    "status": "failed", "error": str(e),
                })
                await event_queue.put({
                    "step": ProgressStep.DOWNLOADING_VIDEOS,
                    "message": f"[{idx + 1}/{total}] 下载失败：《{title[:30]}》— {str(e)[:60]}",
                    "current": idx + 1, "total": total, "phase": "failed", "error": str(e),
                })

            await event_queue.put({"step": "_download_done", "index": idx})

        # Launch all downloads in parallel
        download_tasks = [
            asyncio.create_task(download_one_video(i, vid))
            for i, vid in enumerate(video_ids)
        ]

        # Stream download events
        dl_completed = 0
        while dl_completed < total:
            event = await event_queue.get()
            if event.get("step") == "_download_done":
                dl_completed += 1
                continue
            yield _sse(event)

        await asyncio.gather(*download_tasks, return_exceptions=True)

        # ── Phase 2: Build voice profile ──
        VOICE_PROFILE_THRESHOLD = 8
        audio_paths = [a["audio_path"] for a in downloaded_audios if a.get("audio_path")]
        voice_profile_built = False

        if len(audio_paths) >= VOICE_PROFILE_THRESHOLD:
            yield _sse({
                "step": "building_voice_profile",
                "message": f"正在构建声纹档案（基于 {len(audio_paths)} 个音频）...",
                "audio_count": len(audio_paths),
            })
            try:
                from app.services.voice_profile_builder import build_voice_profile
                await asyncio.to_thread(build_voice_profile, anchor_name, audio_paths)
                voice_profile_built = True
                yield _sse({
                    "step": "building_voice_profile",
                    "message": f"声纹档案构建完成（{len(audio_paths)} 个音频），将用于精确说话人识别",
                    "voice_profile_built": True,
                })
            except Exception as e:
                logger.warning("Voice profile build failed in SSE stream: %s", e)
                yield _sse({
                    "step": "building_voice_profile",
                    "message": f"声纹档案构建失败，将使用聚类模式（{str(e)[:60]}）",
                    "voice_profile_built": False,
                })
        else:
            yield _sse({
                "step": "building_voice_profile",
                "message": f"音频数量不足（{len(audio_paths)} 个，需 ≥{VOICE_PROFILE_THRESHOLD}），使用聚类模式识别",
                "voice_profile_built": False,
            })

        # ── Phase 3: Batch transcribe ALL audio ──
        tr_event_queue: asyncio.Queue = asyncio.Queue()

        async def transcribe_one_audio(audio_info: dict):
            """Transcribe one audio with speaker diarization, save transcript asset."""
            idx = audio_info["idx"]
            vid = audio_info["vid"]
            title = audio_info["title"]
            audio_path = audio_info["audio_path"]
            video_duration = audio_info["duration"]

            await tr_event_queue.put({
                "step": ProgressStep.TRANSCRIBING,
                "message": f"[{idx + 1}/{len(downloaded_audios)}] 开始转写：《{title[:30]}》...",
                "current": idx + 1, "total": len(downloaded_audios), "phase": "start",
                "video_duration": video_duration,
            })

            transcription = None
            try:
                async with transcribe_sem:
                    asr_result = await asyncio.to_thread(_run_asr_sync, audio_path, 600)

                if asr_result:
                    transcription = {
                        "text": asr_result["text"],
                        "segments": asr_result["segments"],
                        "duration": asr_result["duration"],
                    }
                    word_count = len(asr_result["text"])

                    await _save_asset_async(
                        task_id=task_id, anchor_name=anchor_name,
                        video_title=title, asset_type="transcript",
                        file_path=audio_path or "",
                        duration=asr_result.get("duration", 0),
                        transcription_text=asr_result["text"],
                    )

                    await tr_event_queue.put({
                        "step": ProgressStep.TRANSCRIBING,
                        "message": f"[{idx + 1}/{len(downloaded_audios)}] 转写完成：《{title[:30]}》（{word_count}字）",
                        "current": idx + 1, "total": len(downloaded_audios), "phase": "done",
                        "word_count": word_count,
                    })
                    _increment_task_counts(tr=True)
                else:
                    await tr_event_queue.put({
                        "step": ProgressStep.TRANSCRIBING,
                        "message": f"[{idx + 1}/{len(downloaded_audios)}] 转写失败（无输出）：《{title[:30]}》",
                        "current": idx + 1, "total": len(downloaded_audios), "phase": "failed",
                    })

            except Exception as e:
                logger.warning("Transcription failed for %s: %s", vid["aweme_id"], e)
                await tr_event_queue.put({
                    "step": ProgressStep.TRANSCRIBING,
                    "message": f"[{idx + 1}/{len(downloaded_audios)}] 转写失败：《{title[:30]}》— {str(e)[:50]}",
                    "current": idx + 1, "total": len(downloaded_audios), "phase": "failed",
                })

            results.append({
                "index": idx + 1, "aweme_id": vid.get("aweme_id", ""),
                "desc": vid.get("desc", ""), "source_url": vid["url"],
                "author": vid.get("author", ""), "duration": vid.get("duration", 0),
                "play_count": vid.get("play_count", 0),
                "audio_path": audio_path,
                "transcription": transcription,
                "status": "downloaded",
            })

            await tr_event_queue.put({"step": "_tr_done", "index": idx})

        # Launch all transcriptions in parallel
        transcribe_tasks = [
            asyncio.create_task(transcribe_one_audio(info))
            for info in downloaded_audios
        ]

        # Stream transcription events
        tr_completed = 0
        tr_total = len(downloaded_audios)
        while tr_completed < tr_total:
            event = await tr_event_queue.get()
            if event.get("step") == "_tr_done":
                tr_completed += 1
                continue
            yield _sse(event)

        await asyncio.gather(*transcribe_tasks, return_exceptions=True)

        # ── 汇总 ──
        has_transcription = any(r.get("transcription") for r in results if r["status"] == "downloaded")
        yield _sse({
            "step": "transcribe_done",
            "message": "全部视频转写完成" if has_transcription else "ASR 不可用，将基于视频描述分析",
            "results": results,
            "downloaded": len([r for r in results if r["status"] == "downloaded"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
        })

        # === Step 8: 搜索增强（仅 ≥100 万粉触发） ===
        if follower_count >= 1_000_000:
            yield _sse({
                "step": ProgressStep.SEARCH_ENHANCING,
                "message": "检测到头部大V，正在搜索网络公开资料构建增强档案...",
            })
            try:
                from app.services.search_enhancer import search_enhancer
                enhanced_data = await search_enhancer.enhance(
                    profile["anchor_name"], follower_count
                )
                yield _sse({
                    "step": "search_done",
                    "message": "增强档案构建完成，已整合外部认知",
                    "enhanced": True,
                    "enhanced_data": enhanced_data,
                })
            except Exception as e:
                logger.warning("Search enhancement failed: %s", e)
                yield _sse({
                    "step": "search_done",
                    "message": "增强档案构建部分失败，降级为常规分析",
                    "enhanced": False,
                })

        # === Step 9: AI 深度分析 ===
        yield _sse({"step": ProgressStep.ANALYZING, "message": "正在进行 AI 深度分析..."})
        _update_task_record(result_summary={"current_step": "analyzing", "message": "AI 深度分析中...", "progress_pct": 75})

        downloaded = [r for r in results if r["status"] == "downloaded" and r.get("transcription")]
        if not downloaded:
            desc_slices = [r["desc"] for r in results if r.get("desc")]
            if desc_slices:
                yield _sse({"step": ProgressStep.ANALYZING, "message": "ASR 不可用，基于视频描述进行 AI 分析..."})
                try:
                    from app.services.persona_analyzer import persona_analyzer
                    _desc_task = asyncio.ensure_future(asyncio.gather(
                        persona_analyzer.analyze_slices(desc_slices, anchor_name=anchor_name),
                        persona_analyzer.analyze_narrative(desc_slices),
                    ))
                    _elapsed = 0
                    while not _desc_task.done():
                        done, _ = await asyncio.wait({_desc_task}, timeout=8.0)
                        if _desc_task in done:
                            break
                        _elapsed += 8
                        yield _sse({
                            "step": ProgressStep.ANALYZING,
                            "message": f"AI 深度分析进行中...（已用时 {_elapsed} 秒）",
                            "phase": "progress",
                            "elapsed": _elapsed,
                        })
                    analysis, narrative = _desc_task.result()
                except Exception as e:
                    logger.warning("AI analysis degraded (desc-only, SSE stream): %s", e)
                    from app.services.persona_analyzer import _build_minimal_persona
                    analysis = _build_minimal_persona("\n".join(desc_slices[:3]), anchor_name)
                    narrative = {"pacing_summary": "叙事分析暂不可用", "narrative_units": []}

                # 保存人设到数据库（基于视频描述，无转写切片）
                persona_id = None
                try:
                    from app.core.database import async_session_factory
                    from app.models.persona import Persona
                    from app.models.user import User
                    from sqlalchemy import select as sa_select

                    async with async_session_factory() as db:
                        user_result = await db.execute(
                            sa_select(User).where(User.is_active.is_(True)).limit(1)
                        )
                        user = user_result.scalar()
                        if user is None:
                            user = User(
                                id=uuid.uuid4(),
                                username="demo_user",
                                email="demo@scriptforge.local",
                                hashed_password="",
                                plan_type="free",
                                quota_total=5,
                                quota_used=0,
                            )
                            db.add(user)
                            await db.flush()

                        name = f"{anchor_name}的直播风格" if anchor_name else analysis.get("name", "未命名")
                        source_anchor_id = profile.get("sec_uid") or profile.get("anchor_id") or ""
                        source_homepage_url = profile.get("homepage_url") or url
                        existing_result = await db.execute(
                            sa_select(Persona).where(Persona.name == name)
                        )
                        persona = existing_result.scalar_one_or_none()

                        if persona:
                            persona.global_style = analysis.get("global_style", persona.global_style)
                            persona.catchphrases = analysis.get("catchphrases", persona.catchphrases)
                            persona.reaction_patterns = analysis.get("reaction_patterns", persona.reaction_patterns)
                            persona.sentence_templates = analysis.get("sentence_templates", persona.sentence_templates)
                            persona.core_values = analysis.get("core_values", persona.core_values)
                            persona.language_style = analysis.get("language_style", persona.language_style)
                            persona.language_style_v2 = analysis.get("language_style_v2", persona.language_style_v2)
                            persona.tone_adaptation = analysis.get("tone_adaptation", persona.tone_adaptation)
                            persona.lingo_map = analysis.get("lingo_map") or persona.lingo_map or {}
                            persona.narrative_style = narrative
                            persona.version += 1
                            await db.flush()
                        else:
                            persona = Persona(
                                name=name,
                                global_style=analysis.get("global_style", ""),
                                catchphrases=analysis.get("catchphrases", []),
                                reaction_patterns=analysis.get("reaction_patterns", {}),
                                sentence_templates=analysis.get("sentence_templates", []),
                                core_values=analysis.get("core_values", []),
                                language_style=analysis.get("language_style", {}),
                                language_style_v2=analysis.get("language_style_v2"),
                                tone_adaptation=analysis.get("tone_adaptation", {}),
                                narrative_style=narrative,
                                lingo_map=analysis.get("lingo_map") or {},
                                source_anchor_name=anchor_name or None,
                                source_anchor_id=source_anchor_id or None,
                                source_homepage_url=source_homepage_url or None,
                                source_follower_count=follower_count or None,
                            )
                            from app.core.security import set_owner
                            set_owner(persona, user)
                            db.add(persona)
                            await db.flush()

                        # Save desc-based slices
                        from app.models.persona_slice import PersonaSlice
                        for ds in desc_slices:
                            if ds and len(ds.strip()) > 10:
                                slice_obj = PersonaSlice(
                                    persona_id=persona.id,
                                    original_text=ds.strip(),
                                    source_url="",
                                    analyzed=True,
                                )
                                db.add(slice_obj)

                        # Build narrative model
                        from app.services.persona_analyzer import build_narrative_model
                        desc_total_len = sum(len(d.strip()) for d in desc_slices if d)
                        nm = build_narrative_model(persona, slice_count=len(desc_slices), total_text_length=desc_total_len)
                        if nm:
                            persona.narrative_model = nm

                        await db.commit()
                        persona_id = str(persona.id)
                        analysis["persona_id"] = persona_id
                        logger.info("Persona saved (desc-only): %s (%s) slices=%d", persona.name, persona_id, len(desc_slices))

                        # Rename voice profile from anchor_name to persona_id
                        if voice_profile_built and persona_id:
                            try:
                                vp_dir = Path(__file__).resolve().parent.parent.parent / "voice_profiles"
                                safe = anchor_name.replace("/", "_").replace("\\", "_")
                                old = vp_dir / f"{safe}.npy"
                                new = vp_dir / f"{persona_id}.npy"
                                if old.exists() and not new.exists():
                                    old.rename(new)
                                    logger.info("Renamed voice profile: %s -> %s", old.name, new.name)
                            except Exception as e:
                                logger.warning("Failed to rename voice profile (desc-only): %s", e)
                except Exception as e:
                    logger.error("Failed to save persona to DB (desc-only): %s", e)

                yield _sse({
                    "step": ProgressStep.DONE,
                    "message": "处理完成（基于视频描述，非语音转写）",
                    "result": {
                        "profile": profile,
                        "analysis": analysis,
                        "narrative": narrative,
                        "strategies": {"extracted": 0, "results": []},
                        "materials": results,
                        "follower_count": follower_count,
                        "asr_note": "语音转写不可用，分析基于视频标题和描述",
                        "persona_id": persona_id,
                    },
                })
                _update_task_record(
                    status="completed",
                    persona_id=persona_id,
                    persona_name=f"{anchor_name}的直播风格" if anchor_name else analysis.get("name", ""),
                    result_summary={"current_step": "done", "message": "处理完成", "progress_pct": 100},
                )
            else:
                yield _sse({"step": ProgressStep.ERROR, "message": "没有可分析的有效素材"})
                _update_task_record(status="failed", error_message="没有可分析的有效素材")
            return

        slices = [r["transcription"]["text"] for r in downloaded if r.get("transcription")]

        try:
            from app.services.persona_analyzer import persona_analyzer
            _analysis_task = asyncio.ensure_future(asyncio.gather(
                persona_analyzer.analyze_slices(slices, anchor_name=anchor_name),
                persona_analyzer.analyze_narrative(slices),
            ))
            _elapsed = 0
            while not _analysis_task.done():
                done, _ = await asyncio.wait({_analysis_task}, timeout=8.0)
                if _analysis_task in done:
                    break
                _elapsed += 8
                yield _sse({
                    "step": ProgressStep.ANALYZING,
                    "message": f"AI 深度分析进行中...（已用时 {_elapsed} 秒）",
                    "phase": "progress",
                    "elapsed": _elapsed,
                })
            analysis, narrative = _analysis_task.result()
        except Exception as e:
            logger.warning("AI analysis degraded (SSE stream): %s", e)
            from app.services.persona_analyzer import _build_minimal_persona
            analysis = _build_minimal_persona("\n".join(slices[:3]), anchor_name)
            narrative = {"pacing_summary": "叙事分析暂不可用", "narrative_units": []}        # === Step 9.5: 保存人设到数据库 ===
        persona_id = None
        try:
            from app.core.database import async_session_factory
            from app.models.persona import Persona
            from app.models.persona_slice import PersonaSlice
            from app.models.user import User
            from sqlalchemy import select as sa_select

            async with async_session_factory() as db:
                # 获取或创建用户
                user_result = await db.execute(
                    sa_select(User).where(User.is_active.is_(True)).limit(1)
                )
                user = user_result.scalar()
                if user is None:
                    user = User(
                        id=uuid.uuid4(),
                        username="demo_user",
                        email="demo@scriptforge.local",
                        hashed_password="",
                        plan_type="free",
                        quota_total=5,
                        quota_used=0,
                    )
                    db.add(user)
                    await db.flush()

                # 检查是否已存在同名 persona
                name = f"{anchor_name}的直播风格" if anchor_name else analysis.get("name", "未命名")
                source_anchor_id = profile.get("sec_uid") or profile.get("anchor_id") or ""
                source_homepage_url = profile.get("homepage_url") or url
                existing_result = await db.execute(
                    sa_select(Persona).where(Persona.name == name)
                )
                persona = existing_result.scalar_one_or_none()

                if persona:
                    persona.global_style = analysis.get("global_style", persona.global_style)
                    persona.catchphrases = analysis.get("catchphrases", persona.catchphrases)
                    persona.reaction_patterns = analysis.get("reaction_patterns", persona.reaction_patterns)
                    persona.sentence_templates = analysis.get("sentence_templates", persona.sentence_templates)
                    persona.core_values = analysis.get("core_values", persona.core_values)
                    persona.language_style = analysis.get("language_style", persona.language_style)
                    persona.language_style_v2 = analysis.get("language_style_v2", persona.language_style_v2)
                    persona.tone_adaptation = analysis.get("tone_adaptation", persona.tone_adaptation)
                    persona.lingo_map = analysis.get("lingo_map") or persona.lingo_map or {}
                    persona.narrative_style = narrative
                    persona.version += 1
                    await db.flush()
                    action = "updated"
                else:
                    persona = Persona(
                        name=name,
                        global_style=analysis.get("global_style", ""),
                        catchphrases=analysis.get("catchphrases", []),
                        reaction_patterns=analysis.get("reaction_patterns", {}),
                        sentence_templates=analysis.get("sentence_templates", []),
                        core_values=analysis.get("core_values", []),
                        language_style=analysis.get("language_style", {}),
                        language_style_v2=analysis.get("language_style_v2"),
                        tone_adaptation=analysis.get("tone_adaptation", {}),
                        narrative_style=narrative,
                        lingo_map=analysis.get("lingo_map") or {},
                        source_anchor_name=anchor_name or None,
                        source_anchor_id=source_anchor_id or None,
                        source_homepage_url=source_homepage_url or None,
                        source_follower_count=follower_count or None,
                    )
                    from app.core.security import set_owner
                    set_owner(persona, user)
                    db.add(persona)
                    await db.flush()
                    action = "created"

                persona_id = str(persona.id)

                # 保存每个转写切片
                slice_count_for_nm = 0
                total_text_len = 0
                for r in downloaded:
                    if r.get("transcription") and r["transcription"].get("text"):
                        txt = r["transcription"]["text"]
                        slice_obj = PersonaSlice(
                            persona_id=persona.id,
                            original_text=txt,
                            source_url=r.get("source_url", ""),
                            analyzed=True,
                        )
                        db.add(slice_obj)
                        slice_count_for_nm += 1
                        total_text_len += len(txt)

                # Build narrative model
                from app.services.persona_analyzer import build_narrative_model
                nm = build_narrative_model(persona, slice_count=slice_count_for_nm, total_text_length=total_text_len)
                if nm:
                    persona.narrative_model = nm

                await db.commit()
                analysis["persona_id"] = persona_id
                logger.info("Persona saved: %s (%s) action=%s slices=%d",
                            persona.name, persona_id, action, len(downloaded))

                # Rename voice profile from anchor_name to persona_id
                if voice_profile_built and persona_id:
                    try:
                        vp_dir = Path(__file__).resolve().parent.parent.parent / "voice_profiles"
                        safe = anchor_name.replace("/", "_").replace("\\", "_")
                        old = vp_dir / f"{safe}.npy"
                        new = vp_dir / f"{persona_id}.npy"
                        if old.exists() and not new.exists():
                            old.rename(new)
                            logger.info("Renamed voice profile: %s -> %s", old.name, new.name)
                    except Exception as e:
                        logger.warning("Failed to rename voice profile: %s", e)
        except Exception as e:
            logger.error("Failed to save persona to DB: %s", e)
            yield _sse({
                "step": "save_warning",
                "message": f"人设分析完成但保存失败: {e}",
            })

        # === Step 10: 生成报告 ===
        yield _sse({"step": ProgressStep.GENERATING_REPORT, "message": "正在生成人设报告和策略卡片..."})

        try:
            from app.services.strategy_extractor import strategy_extractor
            combined_text = "\n\n".join(slices)
            strategy_res = await strategy_extractor.batch_extract(
                [{"text": combined_text, "category": "monologue"}]
            )
        except Exception as e:
            logger.warning("Strategy extraction failed: %s", e)
            strategy_res = {"extracted": 0, "results": []}

        # === Done ===
        try:
            from sqlalchemy import select as _done_sel
            async with _async_sf() as _done_db:
                _done_row = (await _done_db.execute(
                    _done_sel(_TR).where(_TR.task_id == task_id)
                )).scalar_one_or_none()
                if _done_row:
                    _done_row.status = "completed"
                    _done_row.video_count = len(video_ids)
                    _done_row.downloaded_count = len([r for r in results if r["status"] == "downloaded"])
                    _done_row.transcribed_count = len([r for r in results if r.get("transcription")])
                    _done_row.persona_id = persona_id
                    _done_row.persona_name = f"{anchor_name}的直播风格" if anchor_name else analysis.get("name", "")
                    _done_row.result_summary = {
                        "current_step": "done",
                        "message": "全部处理完成",
                        "progress_pct": 100,
                        "profile": {"name": anchor_name, "followers": follower_count},
                        "materials_count": len(results),
                        "persona_id": persona_id,
                        "strategy_count": strategy_res.get("extracted", 0),
                    }
                    await _done_db.commit()
                    logger.info("Task %s marked completed", task_id)
        except Exception as e:
            logger.error("Failed to mark task completed: %s", e)
        yield _sse({
            "step": ProgressStep.DONE,
            "message": "全部处理完成",
            "result": {
                "profile": profile,
                "analysis": analysis,
                "narrative": narrative,
                "strategies": strategy_res,
                "materials": results,
                "follower_count": follower_count,
                "persona_id": persona_id,
            },
        })

        # Cleanup: Kill any still-running subprocesses on disconnect/error
        for p in _procs:
            try:
                if p.poll() is None:
                    p.terminate()
                    try:
                        p.wait(timeout=5)
                    except _sp.TimeoutExpired:
                        p.kill()
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
