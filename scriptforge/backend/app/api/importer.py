import asyncio
import json
import logging
import os
import sys
import time
import uuid

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.progress import ProgressStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["Import"])


class ImportRequest(BaseModel):
    url: str


class DouyinUserRequest(BaseModel):
    url: str = Field(..., description="抖音用户主页链接")
    count: int = Field(default=5, ge=1, le=20, description="下载视频数量")


class DouyinUserProfileRequest(BaseModel):
    url: str = Field(..., description="抖音用户主页链接")


def _is_celery_available() -> bool:
    try:
        from app.core.celery import celery_app
        celery_app.connection().ensure_connection(max_retries=1)
        return True
    except Exception:
        return False


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

    if _is_celery_available():
        try:
            from app.tasks.importer_tasks import import_video_task
            task = import_video_task.delay(url)
            return {"task_id": task.id, "status": "PENDING", "message": "视频下载和转写已开始"}
        except Exception as e:
            logger.warning("Celery dispatch failed, falling back to sync: %s", e)

    try:
        from app.services.importer import VideoImporter, VideoImportError
        importer = VideoImporter()
        result = importer.import_and_transcribe(url)
        return {
            "task_id": str(uuid.uuid4()),
            "status": "SUCCESS",
            "result": result,
        }
    except VideoImportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Sync import failed for %s", url)
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")


@router.get("/task/{task_id}")
async def get_import_task_status(task_id: str):
    try:
        uuid.UUID(task_id)
    except ValueError:
        pass

    task_result = AsyncResult(task_id)
    state = task_result.state

    if state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    elif state == "PROCESSING":
        return {"task_id": task_id, "status": "processing", "meta": task_result.info}
    elif state == "SUCCESS":
        return {"task_id": task_id, "status": "success", "result": task_result.result}
    elif state == "FAILURE":
        try:
            error_msg = str(task_result.info)
        except Exception:
            error_msg = "任务执行失败"
        return {"task_id": task_id, "status": "failed", "error": error_msg}
    else:
        return {"task_id": task_id, "status": state.lower()}


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

        _procs: list[_sp.Popen] = []  # Track subprocesses for cleanup on disconnect
        url = req.url.strip()
        count = req.count

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
        except Exception as e:
            yield _sse({"step": ProgressStep.ERROR, "message": f"获取博主信息失败: {e}"})
            return

        # === Step 2-4: 获取视频列表 + 筛选排序 + Top N（流式 Popen） ===
        yield _sse({"step": ProgressStep.FETCHING_VIDEO_LIST, "message": "正在搜索视频列表..."})

        _worker = _P(__file__).resolve().parent.parent / "services" / "douyin_video_list_worker.py"
        _log_dir = _P(__file__).resolve().parent.parent.parent / "logs"
        _log_dir.mkdir(parents=True, exist_ok=True)

        video_ids = []

        # Use Popen for real-time stdout streaming (same pattern as ASR)
        _proc = await asyncio.to_thread(
            _sp.Popen,
            [sys.executable, str(_worker),
             profile.get("sec_uid") or profile.get("anchor_id") or "", str(count)],
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
            elif step == "done":
                video_ids = data.get("video_ids", [])
            elif step == "error":
                yield _sse({"step": ProgressStep.ERROR, "message": data["error"]})
                return

        _proc.wait(timeout=10)

        if _proc.returncode != 0 and not video_ids:
            stderr = _proc.stderr.read() if _proc.stderr else ""
            logger.error("Video list worker failed (exit %d): %s", _proc.returncode, stderr[:200])
            yield _sse({"step": ProgressStep.ERROR, "message": "获取视频列表失败，详情请查看 logs/playwright.log"})
            return

        if not video_ids:
            yield _sse({"step": ProgressStep.ERROR, "message": "该用户暂无公开视频或 cookies 已过期"})
            return

        yield _sse({
            "step": "video_list_done",
            "message": f"视频列表搜索完成，共选定 {len(video_ids)} 个视频",
            "total": len(video_ids),
        })

        # === Steps 5-7: 下载 → 提取音频 → 转写（逐个视频） ===
        results = []
        total = len(video_ids)

        for i, vid in enumerate(video_ids):
            title = vid.get("desc", "") or vid.get("aweme_id", "")
            video_duration = vid.get("duration", 0)

            # --- Step 5: 下载视频 ---
            yield _sse({
                "step": ProgressStep.DOWNLOADING_VIDEOS,
                "message": f"正在下载视频 {i + 1}/{total}：《{title[:30]}》...",
                "current": i + 1,
                "total": total,
                "title": title,
                "phase": "start",
            })

            start_time = time.time()
            audio_path = None
            try:
                audio_path = await asyncio.to_thread(downloader.download_video, vid["url"])
                download_time = time.time() - start_time

                # Check mp4 file size for display
                mp4_path = audio_path.replace(".wav", ".mp4") if audio_path.endswith(".wav") else audio_path
                file_size = os.path.getsize(mp4_path) if os.path.exists(mp4_path) else 0

                yield _sse({
                    "step": ProgressStep.DOWNLOADING_VIDEOS,
                    "message": f"视频 {i + 1}/{total} 下载完成（{_format_size(file_size)}，耗时 {download_time:.1f} 秒）",
                    "current": i + 1,
                    "total": total,
                    "phase": "done",
                    "file_size": file_size,
                    "download_seconds": round(download_time, 1),
                })
            except Exception as e:
                logger.error("Failed to download video %s: %s", vid.get("aweme_id"), e)
                results.append({
                    "index": i + 1,
                    "aweme_id": vid.get("aweme_id", ""),
                    "desc": vid.get("desc", ""),
                    "source_url": vid["url"],
                    "status": "failed",
                    "error": str(e),
                })
                yield _sse({
                    "step": ProgressStep.DOWNLOADING_VIDEOS,
                    "message": f"视频 {i + 1}/{total} 下载失败: {str(e)[:60]}",
                    "current": i + 1,
                    "total": total,
                    "phase": "failed",
                })
                continue

            # --- Step 6: 提取音频（已在 download_video 内完成） ---
            yield _sse({
                "step": ProgressStep.EXTRACTING_AUDIO,
                "message": f"正在提取音频 {i + 1}/{total}...",
                "current": i + 1,
                "total": total,
                "phase": "start",
            })
            yield _sse({
                "step": ProgressStep.EXTRACTING_AUDIO,
                "message": f"音频 {i + 1}/{total} 提取完成",
                "current": i + 1,
                "total": total,
                "phase": "done",
            })

            # --- Step 7: 转写（在子进程中运行，流式读取进度） ---
            duration_str = _format_duration(video_duration) if video_duration > 0 else ""
            yield _sse({
                "step": ProgressStep.TRANSCRIBING,
                "message": f"正在转写 {i + 1}/{total}{f'（视频时长 {duration_str}）' if duration_str else ''}...",
                "current": i + 1,
                "total": total,
                "video_duration": video_duration,
                "phase": "start",
            })

            transcription = None
            try:
                _asr_worker = _P(__file__).resolve().parent.parent / "services" / "asr_worker.py"
                asr_start = time.time()

                # Use Popen to read stdout line by line for progress
                proc = _sp.Popen(
                    [sys.executable, str(_asr_worker), audio_path],
                    stdout=_sp.PIPE,
                    stderr=_sp.PIPE,
                    encoding="utf-8",
                    errors="replace",
                )
                _procs.append(proc)

                asr_result_data = None
                asr_failed = False

                def _read_asr_lines():
                    lines = []
                    for line in proc.stdout:
                        line = line.strip()
                        if not line:
                            continue
                        lines.append(line)
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        yield data

                    proc.wait(timeout=60)
                    # Return all lines for final parsing
                    return lines

                async def _stream_asr():
                    nonlocal asr_result_data, asr_failed
                    loop = asyncio.get_event_loop()

                    def _read_next():
                        lines = []
                        try:
                            for line in proc.stdout:
                                s = line.strip()
                                if s:
                                    lines.append(s)
                        except Exception:
                            pass
                        return lines

                    while proc.poll() is None:
                        batch = await asyncio.to_thread(_read_next, )
                        if not batch:
                            await asyncio.sleep(0.5)
                            continue

                        for raw_line in batch:
                            try:
                                data = json.loads(raw_line)
                            except json.JSONDecodeError:
                                continue

                            if data.get("phase") == "loading_model":
                                yield _sse({
                                    "step": ProgressStep.TRANSCRIBING,
                                    "message": f"转写 {i + 1}/{total}：正在加载语音识别模型...",
                                    "current": i + 1,
                                    "total": total,
                                    "asr_sub_phase": "loading",
                                })
                            elif data.get("phase") == "model_loaded":
                                yield _sse({
                                    "step": ProgressStep.TRANSCRIBING,
                                    "message": f"转写 {i + 1}/{total}：模型已加载，开始识别...",
                                    "current": i + 1,
                                    "total": total,
                                    "asr_sub_phase": "transcribing",
                                })
                            elif data.get("phase") == "transcribing":
                                yield _sse({
                                    "step": ProgressStep.TRANSCRIBING,
                                    "message": f"转写 {i + 1}/{total}：{data.get('message', '')}",
                                    "current": i + 1,
                                    "total": total,
                                    "asr_sub_phase": "transcribing",
                                    "asr_progress_pct": data.get("progress_pct", 0),
                                    "asr_char_count": data.get("char_count", 0),
                                    "asr_elapsed": data.get("elapsed_seconds", 0),
                                    "asr_current_time": data.get("current_time", 0),
                                    "asr_total_duration": data.get("total_duration", 0),
                                })
                            elif data.get("phase") == "done":
                                asr_result_data = data
                            elif data.get("error"):
                                asr_failed = True
                                yield _sse({
                                    "step": ProgressStep.TRANSCRIBING,
                                    "message": f"转写 {i + 1}/{total} 失败: {data['error'][:60]}",
                                    "current": i + 1,
                                    "total": total,
                                    "phase": "failed",
                                })

                    # Drain remaining lines after process exits
                    remaining = proc.stdout.read()
                    for raw_line in remaining.strip().split("\n"):
                        raw_line = raw_line.strip()
                        if not raw_line:
                            continue
                        try:
                            data = json.loads(raw_line)
                        except json.JSONDecodeError:
                            continue
                        if data.get("phase") == "done":
                            asr_result_data = data
                        elif data.get("error"):
                            asr_failed = True

                # Stream ASR progress events
                async for sse_event in _stream_asr():
                    yield sse_event

                asr_time = time.time() - asr_start

                if asr_result_data and not asr_failed:
                    transcription = {
                        "text": asr_result_data["text"],
                        "segments": asr_result_data["segments"],
                        "duration": asr_result_data["duration"],
                    }
                    word_count = len(asr_result_data["text"])
                    yield _sse({
                        "step": ProgressStep.TRANSCRIBING,
                        "message": f"转写 {i + 1}/{total} 完成（识别 {word_count} 字，耗时 {asr_time:.1f} 秒）",
                        "current": i + 1,
                        "total": total,
                        "phase": "done",
                        "word_count": word_count,
                        "asr_seconds": round(asr_time, 1),
                    })
                elif not asr_failed:
                    logger.warning("ASR worker produced no result for %s", vid["aweme_id"])
                    yield _sse({
                        "step": ProgressStep.TRANSCRIBING,
                        "message": f"转写 {i + 1}/{total} 失败（ASR 无输出）",
                        "current": i + 1,
                        "total": total,
                        "phase": "failed",
                    })
            except Exception as e:
                logger.warning("Transcription failed for %s: %s", vid["aweme_id"], e)
                yield _sse({
                    "step": ProgressStep.TRANSCRIBING,
                    "message": f"转写 {i + 1}/{total} 失败: {str(e)[:50]}",
                    "current": i + 1,
                    "total": total,
                    "phase": "failed",
                })

            results.append({
                "index": i + 1,
                "aweme_id": vid["aweme_id"],
                "desc": vid["desc"],
                "source_url": vid["url"],
                "author": vid.get("author", ""),
                "duration": vid.get("duration", 0),
                "play_count": vid.get("play_count", 0),
                "audio_path": audio_path,
                "transcription": transcription,
                "status": "downloaded",
            })

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

        downloaded = [r for r in results if r["status"] == "downloaded" and r.get("transcription")]
        if not downloaded:
            desc_slices = [r["desc"] for r in results if r.get("desc")]
            if desc_slices:
                yield _sse({"step": ProgressStep.ANALYZING, "message": "ASR 不可用，基于视频描述进行 AI 分析..."})
                try:
                    from app.services.persona_analyzer import persona_analyzer
                    analysis = await persona_analyzer.analyze_slices(desc_slices)
                    narrative = await persona_analyzer.analyze_narrative(desc_slices)
                except Exception as e:
                    yield _sse({"step": ProgressStep.ERROR, "message": f"AI 分析失败: {e}"})
                    return

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
                    },
                })
            else:
                yield _sse({"step": ProgressStep.ERROR, "message": "没有可分析的有效素材"})
            return

        slices = [r["transcription"]["text"] for r in downloaded if r.get("transcription")]

        try:
            from app.services.persona_analyzer import persona_analyzer
            analysis, narrative = await asyncio.gather(
                persona_analyzer.analyze_slices(slices),
                persona_analyzer.analyze_narrative(slices),
            )
        except Exception as e:
            yield _sse({"step": ProgressStep.ERROR, "message": f"AI 分析失败: {e}"})
            return

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
