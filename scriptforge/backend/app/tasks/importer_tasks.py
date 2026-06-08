"""Background tasks for importing videos and processing Douyin user content.

Previously Celery-based, now runs as plain sync functions invoked via asyncio.to_thread().
"""

import asyncio
import gc
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.services.deepseek_client import reset_client_sync

logger = logging.getLogger(__name__)


# ── Progress step constants (mirrors app.core.progress.ProgressStep) ──

class _Step:
    FETCHING_PROFILE = "fetching_profile"
    FETCHING_VIDEO_LIST = "fetching_video_list"
    FILTERING_AND_SORTING = "filtering_and_sorting"
    TOP_SELECTED = "top_selected"
    DOWNLOADING_VIDEOS = "downloading_videos"
    EXTRACTING_AUDIO = "extracting_audio"
    BUILDING_VOICE_PROFILE = "building_voice_profile"
    TRANSCRIBING = "transcribing"
    SEARCH_ENHANCING = "search_enhancing"
    ANALYZING = "analyzing"
    GENERATING_REPORT = "generating_report"
    DONE = "done"
    ERROR = "error"


def import_video_task(url: str):
    from app.services.importer import VideoImporter, VideoImportError

    try:
        importer = VideoImporter()
        result = importer.import_and_transcribe(url)
        return result
    except VideoImportError as e:
        logger.error("Video import error: %s", e)
        raise
    except Exception as e:
        logger.exception("Video import failed: %s", url)
        raise


# ── Asset recording helper ──

def _update_task_record_sync(task_id: str, **kwargs):
    """Update a TaskRecord row using a short-lived async session."""
    async def _do():
        from app.core.database import async_session_factory
        from app.models.task_record import TaskRecord
        from sqlalchemy import select
        async with async_session_factory() as session:
            row = (await session.execute(
                select(TaskRecord).where(TaskRecord.task_id == task_id)
            )).scalar_one_or_none()
            if row:
                for k, v in kwargs.items():
                    setattr(row, k, v)
                await session.commit()
    try:
        asyncio.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        asyncio.run(_do())


def _progress(task_id: str, step: str, message: str, **extra):
    """Update TaskRecord result_summary with step progress (replaces Celery self.update_state)."""
    summary = {"step": step, "message": message, **extra}
    _update_task_record_sync(task_id, result_summary=summary)


def _create_task_record_sync(task_id: str, trigger: str, url: str):
    """Create a TaskRecord row using a short-lived async session."""
    async def _do():
        from app.core.database import async_session_factory
        from app.models.task_record import TaskRecord
        async with async_session_factory() as session:
            record = TaskRecord(task_id=task_id, trigger=trigger, url=url, status="running")
            session.add(record)
            await session.commit()
    try:
        asyncio.get_event_loop().run_until_complete(_do())
    except RuntimeError:
        asyncio.run(_do())


def _save_asset_sync(
    task_id: str,
    anchor_name: str,
    video_title: str,
    asset_type: str,
    file_path: str,
    file_size: int = 0,
    duration: float = 0.0,
    transcription_text: str | None = None,
):
    """Insert an asset record using a short-lived asyncio session."""
    async def _insert():
        from app.core.database import async_session_factory
        from app.models.asset import Asset, AssetType

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

    try:
        asyncio.run(_insert())
    except Exception as e:
        logger.warning("Failed to save asset record: %s", e)


# ── Transcription worker (runs in thread pool) ──

def _transcribe_sync(audio_path: str, vid: dict, idx: int, total: int, anchor_name: str = "") -> dict:
    """Run ASR subprocess in a thread-safe manner. Returns result dict."""
    import gc as _gc
    _WORKER_DIR = Path(__file__).resolve().parent.parent / "services"

    result = {
        "aweme_id": vid.get("aweme_id", ""),
        "desc": vid.get("desc", ""),
        "source_url": vid["url"],
        "author": vid.get("author", ""),
        "duration": vid.get("duration", 0),
        "play_count": vid.get("play_count", 0),
        "index": idx + 1,
        "audio_path": audio_path,
    }

    # Demucs vocal separation before ASR
    try:
        from app.services.audio_processor import separate_vocals
        vocals_path = separate_vocals(audio_path)
        if vocals_path != audio_path:
            logger.info("[ASR] Using vocals-separated audio: %s", vocals_path)
            audio_path = vocals_path
    except Exception as _e:
        logger.warning("[ASR] Vocal separation skipped: %s", _e)

    try:
        asr_worker = _WORKER_DIR / "asr_worker.py"
        _venv_py = Path(__file__).resolve().parent.parent.parent / ".venv-py312" / "Scripts" / "python.exe"
        _python = str(_venv_py) if _venv_py.exists() else sys.executable
        asr_proc = subprocess.Popen(
            [_python, str(asr_worker), audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace",
        )

        asr_result_data = None
        asr_failed = False

        for raw_line in asr_proc.stdout:
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

        asr_proc.wait(timeout=120)

        if asr_result_data and not asr_failed:
            segments = asr_result_data.get("segments", [])

            # Speaker diarization — assign "主播" / "连线观众" labels
            try:
                from app.services.audio_processor import SpeakerDiarizer
                sd = SpeakerDiarizer()
                diarization_segs = sd.diarize(audio_path, anchor_name=anchor_name)
                if diarization_segs:
                    ref_used = sd.last_mode == "reference"
                    speaker_map = sd.map_speakers(diarization_segs, reference_used=ref_used)
                    segments = sd.assign_speakers(diarization_segs, segments, speaker_map)
                    logger.info("[ASR] Speaker diarization (%s) applied: %s", sd.last_mode, speaker_map)
            except Exception as _e:
                logger.warning("[ASR] Speaker diarization skipped: %s", _e)

            # Build labeled text from segments if speaker info is present
            labeled_segments = [s for s in segments if s.get("speaker")]
            if labeled_segments:
                from app.api.assets import _merge_speaker_lines
                text = _merge_speaker_lines(labeled_segments)
            else:
                text = asr_result_data["text"]

            result["transcription"] = {
                "text": text,
                "segments": segments,
                "duration": asr_result_data.get("duration", 0),
            }
            result["status"] = "success"
            result["error"] = None
        else:
            result["status"] = "failed"
            result["transcription"] = None
            result["error"] = "转写失败或结果为空"
    except Exception as e:
        logger.warning("Transcription failed for %s: %s", vid.get("aweme_id"), e)
        result["status"] = "failed"
        result["transcription"] = None
        result["error"] = f"转写异常: {e}"

    _gc.collect()
    return result


def process_douyin_user_task(url: str, count: int = 5, task_id: str | None = None):
    """Full pipeline for processing a Douyin user's videos.

    Steps: profile → video list → download → transcribe → analyze → save → strategies

    Progress is reported via TaskRecord updates so the frontend can poll
    GET /api/import/task/{task_id} and see real-time step progress.
    """
    from app.services.douyin_service import DouyinDownloader

    if not task_id:
        task_id = uuid.uuid4().hex

    _WORKER_DIR = Path(__file__).resolve().parent.parent / "services"
    _LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    profile = None
    follower_count = 0
    results: list[dict] = []
    persona_id = None
    task_id = task_id

    # Create TaskRecord
    _create_task_record_sync(task_id, trigger="douyin_user_import", url=url)

    # ── Step 1: Fetch profile ──
    _progress(task_id, _Step.FETCHING_PROFILE, "正在获取博主信息...")
    try:
        downloader = DouyinDownloader()
        profile = downloader.get_user_profile(url)
        follower_count = profile.get("follower_count", 0)
    except Exception as e:
        logger.error("Profile fetch failed: %s", e)
        _update_task_record_sync(task_id, status="failed", result_summary={"step": "error", "message": ""})
        raise

    fc_str = f"{follower_count / 10000:.1f}万" if follower_count >= 10000 else str(follower_count)
    _update_task_record_sync(task_id,
        anchor_name=profile.get("anchor_name", ""),
        anchor_avatar=profile.get("avatar_url"),
        follower_count=follower_count,
    )
    _progress(task_id, _Step.FETCHING_PROFILE, f"已获取博主: {profile.get('anchor_name')} ({fc_str} 粉丝)", profile=profile, follower_count=follower_count)

    # ── Step 2: Fetch video list (subprocess) ──
    _progress(task_id, _Step.FETCHING_VIDEO_LIST, "正在搜索视频列表...")

    video_ids = []
    sec_uid = profile.get("sec_uid") or profile.get("anchor_id") or ""
    worker_script = _WORKER_DIR / "douyin_video_list_worker.py"

    proc = subprocess.Popen(
        [sys.executable, str(worker_script), sec_uid, str(count)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )

    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        # Mirror to playwright log
        with open(_LOG_DIR / "playwright.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        step = data.get("step")
        if step == "fetching_video_list":
            _progress(task_id, _Step.FETCHING_VIDEO_LIST, f"正在搜索视频列表（第 {data['page']} 页，已发现 {data['total_collected']} 个作品）...", page=data["page"], total_collected=data["total_collected"])
        elif step == "filtering":
            _progress(task_id, _Step.FILTERING_AND_SORTING, f"正在筛选（时长 15-180 秒），{data['total_before_filter']} 个作品中 {data['filtered_count']} 个符合条件...", total_before_filter=data["total_before_filter"], filtered_count=data["filtered_count"])
        elif step == "top_selected":
            play_str = " / ".join(data.get("play_strs", []))
            _progress(task_id, _Step.TOP_SELECTED, f"已选定 Top {data['selected_count']} 视频（播放量：{play_str}）", selected_count=data["selected_count"], top_videos=data.get("top_videos"))
        elif step == "done":
            video_ids = data.get("video_ids", [])
        elif step == "error":
            _update_task_record_sync(task_id, status="failed", result_summary={"step": "error", "message": ""})
            return

    proc.wait(timeout=10)

    if proc.returncode != 0 and not video_ids:
        stderr = proc.stderr.read() if proc.stderr else ""
        logger.error("Video list worker failed (exit %d): %s", proc.returncode, stderr[:200])
        _update_task_record_sync(task_id, status="failed", result_summary={"step": "error", "message": ""})
        return

    if not video_ids:
        _update_task_record_sync(task_id, status="failed", result_summary={"step": "error", "message": ""})
        return

    total = len(video_ids)
    _progress(task_id, _Step.FETCHING_VIDEO_LIST, f"视频列表搜索完成，共选定 {total} 个视频", total=total)

    anchor_name = profile.get("anchor_name", "") if profile else ""

    # ── Steps 3-5: Download → Extract Audio → Build Voice Profile → Batch Transcribe ──
    # Phase 1: Download ALL videos first (no transcription yet).
    # Phase 2: Build voice profile from accumulated audio (if enough files).
    # Phase 3: Batch transcribe all audio using voice profile for speaker diarization.

    BATCH_SIZE = 3
    BATCH_PAUSE = 30  # seconds between batches to avoid Douyin anti-scraping
    VOICE_PROFILE_THRESHOLD = 8  # minimum audio files to build voice profile

    def _download_single(vid: dict, idx: int, _total: int, t_id: str, a_name: str):
        """Download one video (runs in thread pool). Returns result dict for main-thread processing."""
        _title = vid.get("desc", "") or vid.get("aweme_id", "")
        try:
            _start = time.time()
            _audio = downloader.download_video(vid["url"])
            _elapsed = time.time() - _start

            _mp4 = _audio.replace(".wav", ".mp4") if _audio and _audio.endswith(".wav") else _audio
            _fsize = os.path.getsize(_mp4) if _mp4 and os.path.exists(_mp4) else 0
            _dur = vid.get("duration", 0)

            # Save video asset immediately
            _save_asset_sync(task_id=t_id, anchor_name=a_name, video_title=_title,
                             asset_type="video", file_path=_mp4, file_size=_fsize, duration=_dur)

            # Save audio asset immediately
            if _audio and os.path.exists(_audio):
                _save_asset_sync(task_id=t_id, anchor_name=a_name, video_title=_title,
                                 asset_type="audio", file_path=_audio,
                                 file_size=os.path.getsize(_audio), duration=_dur)

            return {"index": idx + 1, "vid": vid, "title": _title, "audio_path": _audio,
                    "file_size": _fsize, "download_seconds": round(_elapsed, 1), "error": None}
        except Exception as e:
            logger.error("Failed to download video %s: %s", vid.get("aweme_id"), e)
            return {"index": idx + 1, "vid": vid, "title": _title, "audio_path": None,
                    "file_size": 0, "download_seconds": 0, "error": str(e)}

    # ── Phase 1: Download ALL videos (no transcription yet) ──
    downloaded_audios: list[dict] = []  # Collect successful downloads for batch transcription
    completed_dls = 0
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(num_batches):
        batch_start = batch_idx * BATCH_SIZE
        batch = video_ids[batch_start:batch_start + BATCH_SIZE]

        if batch_idx > 0:
            logger.info("Batch %d/%d: pausing %ds before downloading next batch",
                        batch_idx + 1, num_batches, BATCH_PAUSE)
            _progress(task_id, _Step.DOWNLOADING_VIDEOS, f"等待 {BATCH_PAUSE} 秒后继续下载第 {batch_idx + 1}/{num_batches} 批（防反爬）", current=completed_dls, total=total)
            time.sleep(BATCH_PAUSE)

        logger.info("Batch %d/%d: downloading %d videos (video %d-%d of %d)",
                    batch_idx + 1, num_batches, len(batch),
                    batch_start + 1, batch_start + len(batch), total)

        dl_executor = ThreadPoolExecutor(max_workers=3)
        dl_futures = [dl_executor.submit(_download_single, vid, batch_start + i, total,
                      task_id, anchor_name) for i, vid in enumerate(batch)]

        for dl_future in as_completed(dl_futures):
            dl = dl_future.result()
            completed_dls += 1
            idx = dl["index"]
            vid = dl["vid"]
            title = dl["title"]

            if dl["error"]:
                results.append({
                    "index": idx, "aweme_id": vid.get("aweme_id", ""),
                    "desc": vid.get("desc", ""), "source_url": vid["url"],
                    "author": vid.get("author", ""), "duration": vid.get("duration", 0),
                    "play_count": vid.get("play_count", 0),
                    "status": "failed", "error": f"下载失败: {dl['error']}",
                })
                _progress(task_id, _Step.DOWNLOADING_VIDEOS, f"视频 {idx}/{total} 下载失败，已跳过", current=completed_dls, total=total)
                continue

            _progress(task_id, _Step.DOWNLOADING_VIDEOS, f"视频 {idx}/{total} 下载完成（{dl['file_size'] / 1048576:.1f} MB，耗时 {dl['download_seconds']:.1f} 秒）", current=completed_dls, total=total, file_size=dl["file_size"], download_seconds=dl["download_seconds"])

            # Collect for batch transcription (do NOT transcribe yet)
            downloaded_audios.append(dl)

        dl_executor.shutdown(wait=False)

    # ── Phase 2: Build voice profile (if enough audio) ──
    voice_profile_built = False
    audio_paths = [a["audio_path"] for a in downloaded_audios if a.get("audio_path")]

    if len(audio_paths) >= VOICE_PROFILE_THRESHOLD:
        _progress(task_id, _Step.BUILDING_VOICE_PROFILE, f"正在构建声纹档案（基于 {len(audio_paths)} 个音频）...", audio_count=len(audio_paths))
        try:
            from app.services.voice_profile_builder import build_voice_profile
            build_voice_profile(anchor_name, audio_paths)
            voice_profile_built = True
            logger.info("Voice profile built for '%s' from %d audio files", anchor_name, len(audio_paths))
            _progress(task_id, _Step.BUILDING_VOICE_PROFILE, f"声纹档案构建完成，将用于精确说话人识别（{len(audio_paths)} 个音频）", voice_profile_built=True)
        except Exception as e:
            logger.warning("Voice profile build failed, falling back to clustering: %s", e)
    else:
        logger.info("Audio count (%d) below threshold (%d), skipping voice profile build",
                     len(audio_paths), VOICE_PROFILE_THRESHOLD)

    # ── Phase 3: Batch transcribe ALL audio ──
    tr_executor = ThreadPoolExecutor(max_workers=2)
    tr_futures: list = []
    future_meta: dict = {}

    for idx, dl in enumerate(downloaded_audios):
        vid = dl["vid"]
        tf = tr_executor.submit(_transcribe_sync, dl["audio_path"], vid, idx, len(downloaded_audios), anchor_name)
        tr_futures.append(tf)
        future_meta[tf] = {"index": dl["index"], "vid": vid, "audio_path": dl["audio_path"], "title": dl["title"]}

    completed_tr = 0
    for future in as_completed(tr_futures):
        trans_result = future.result()
        meta = future_meta[future]
        completed_tr += 1

        results.append(trans_result)

        # Save transcript asset immediately
        if trans_result.get("status") == "success" and trans_result.get("transcription"):
            text = trans_result["transcription"]["text"]
            _save_asset_sync(
                task_id=task_id, anchor_name=anchor_name,
                video_title=meta["title"], asset_type="transcript",
                file_path=meta.get("audio_path", ""),
                duration=trans_result.get("duration", 0),
                transcription_text=text,
            )

        _progress(task_id, _Step.TRANSCRIBING, f"转写完成 {completed_tr}/{total}", current=completed_tr, total=total)

    tr_executor.shutdown(wait=False)
    gc.collect()

    # ── Post-download summary ──
    successful_videos = [r for r in results if r["status"] == "success" and r.get("transcription")]
    failed_videos = [r for r in results if r["status"] == "failed"]
    _progress(task_id, _Step.TRANSCRIBING, f"全部视频处理完成（成功 {len(successful_videos)}/总数 {len(results)}）", successful_count=len(successful_videos), total_count=len(results), failed_count=len(failed_videos))

    # ── Minimum material threshold ──
    MIN_SUCCESS_COUNT = 1
    if len(successful_videos) < MIN_SUCCESS_COUNT:
        failed_details = [
            {"desc": v["desc"][:40], "error": v.get("error", "未知错误")}
            for v in failed_videos
        ]
        error_msg = (
            f"素材下载失败，成功数不足（成功 {len(successful_videos)}/总数 {len(results)}），"
            f"无法生成人设"
        )
        logger.error("Task failed: %s, failures: %s", error_msg, failed_details)
        _update_task_record_sync(task_id, status="failed", result_summary={"step": "error", "message": ""})
        return

    # Warn on partial failure
    if failed_videos:
        logger.warning("部分视频失败，仅用成功素材分析。成功: %d, 失败: %d",
                      len(successful_videos), len(failed_videos))
        _progress(task_id, _Step.TRANSCRIBING, f"部分视频处理失败，仅使用成功素材（成功 {len(successful_videos)}/总数 {len(results)}）", successful_count=len(successful_videos), total_count=len(results), failed_count=len(failed_videos), partial_success=True)

    has_transcription = any(r.get("transcription") for r in results if r["status"] == "success")
    downloaded = successful_videos  # Only use successful videos for analysis

    # ── Update intermediate stats (Bug 2 fix) ──
    _update_task_record_sync(task_id,
        video_count=len(video_ids),
        downloaded_count=len(successful_videos),
        transcribed_count=len([r for r in results if r.get("transcription")]),
    )

    # ── Step 6: Search enhancement (if >= 1M followers) ──
    enhanced_data = None
    if follower_count >= 1_000_000:
        _progress(task_id, _Step.SEARCH_ENHANCING, "检测到头部大V，正在搜索网络公开资料构建增强档案...")
        try:
            from app.services.search_enhancer import search_enhancer
            reset_client_sync()
            enhanced_data = asyncio.run(search_enhancer.enhance(
                profile["anchor_name"], follower_count
            ))
        except Exception as e:
            logger.warning("Search enhancement failed: %s", e)

    # ── Step 7: AI Analysis (only from successfully transcribed material) ──
    _progress(task_id, _Step.ANALYZING, f"正在进行 AI 深度分析（基于 {len(downloaded)} 个成功素材）...")

    slices = [r["transcription"]["text"] for r in downloaded if r.get("transcription")]
    analysis = None
    narrative = None
    strategy_res = {"extracted": 0, "results": []}
    analysis_warning = None

    try:
        from app.services.persona_analyzer import persona_analyzer

        async def _analyze():
            return await asyncio.gather(
                persona_analyzer.analyze_slices(slices, anchor_name=anchor_name),
                persona_analyzer.analyze_narrative(slices),
            )

        reset_client_sync()
        analysis, narrative = asyncio.run(_analyze())
    except Exception as e:
        analysis_warning = f"AI 分析部分降级: {e}"
        logger.warning("AI analysis degraded for task %s: %s", task_id, e)
        # Build minimal analysis so persona can still be saved
        if not analysis:
            from app.services.persona_analyzer import _build_minimal_persona
            combined_text = "\n\n".join(slices[:3])
            analysis = _build_minimal_persona(combined_text, anchor_name)
        if not narrative:
            narrative = {"pacing_summary": "叙事分析暂不可用", "narrative_units": []}

    # ── Step 8: Save persona to DB ──
    _progress(task_id, _Step.ANALYZING, "正在保存人设数据...")

    try:
        from app.core.database import async_session_factory
        from app.models.persona import Persona
        from app.models.persona_slice import PersonaSlice
        from app.models.user import User
        from app.core.security import set_owner
        from sqlalchemy import select as sa_select

        async def _save_persona():
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
                        tone_adaptation=analysis.get("tone_adaptation", {}),
                        narrative_style=narrative,
                        lingo_map=analysis.get("lingo_map") or {},
                        source_anchor_name=anchor_name or None,
                        source_anchor_id=source_anchor_id or None,
                        source_homepage_url=source_homepage_url or None,
                        source_follower_count=follower_count or None,
                    )
                    set_owner(persona, user)
                    db.add(persona)
                    await db.flush()
                    action = "created"

                pid = str(persona.id)

                nm_slice_count = 0
                nm_text_len = 0
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
                        nm_slice_count += 1
                        nm_text_len += len(txt)

                # Build narrative model
                from app.services.persona_analyzer import build_narrative_model
                nm = build_narrative_model(persona, slice_count=nm_slice_count, total_text_length=nm_text_len)
                if nm:
                    persona.narrative_model = nm

                await db.commit()
                return pid

        reset_client_sync()
        persona_id = asyncio.run(_save_persona())
        analysis["persona_id"] = persona_id
        logger.info("Persona saved: %s (%s)", analysis.get("name"), persona_id)

        # Rename voice profile from anchor_name to persona_id
        if voice_profile_built and persona_id:
            try:
                vp_dir = Path(__file__).resolve().parent.parent.parent / "voice_profiles"
                old = vp_dir / f"{anchor_name.replace('/', '_').replace(chr(92), '_')}.npy"
                new = vp_dir / f"{persona_id}.npy"
                if old.exists() and not new.exists():
                    old.rename(new)
                    logger.info("Renamed voice profile: %s → %s", old.name, new.name)
            except Exception as e:
                logger.warning("Failed to rename voice profile: %s", e)
    except Exception as e:
        logger.error("Failed to save persona to DB: %s", e)
        # Non-fatal: continue with result but no persona_id

    # ── Step 9: Strategy extraction ──
    _progress(task_id, _Step.GENERATING_REPORT, "正在生成人设报告和策略卡片...")

    if downloaded:
        try:
            from app.services.strategy_extractor import strategy_extractor
            combined_text = "\n\n".join(
                r["transcription"]["text"] for r in downloaded if r.get("transcription")
            )
            reset_client_sync()
            strategy_res = asyncio.run(strategy_extractor.batch_extract(
                [{"text": combined_text, "category": "monologue"}]
            ))
        except Exception as e:
            logger.warning("Strategy extraction failed: %s", e)

    # ── Build final result ──
    has_failures = len(failed_videos) > 0
    result = {
        "status": "completed",
        "partial_success": has_failures,
        "persona_id": persona_id,
        "profile": profile,
        "analysis": analysis,
        "narrative": narrative,
        "strategies": strategy_res,
        "materials": results,
        "follower_count": follower_count,
        "enhanced_data": enhanced_data is not None,
        "successful_count": len(successful_videos),
        "total_count": len(results),
        "failed_count": len(failed_videos),
        "failed_videos": [
            {"desc": v["desc"][:40], "error": v.get("error", "未知错误")}
            for v in failed_videos
        ] if has_failures else [],
    }

    result_msg = "全部处理完成"
    if has_failures:
        result_msg = f"部分成功完成（成功 {len(successful_videos)}/总数 {len(results)}）"

    # Update TaskRecord to completed
    _update_task_record_sync(task_id,
        status="completed",
        video_count=len(results),
        downloaded_count=len(successful_videos),
        transcribed_count=len([r for r in results if r.get("transcription")]),
        persona_id=persona_id,
        persona_name=f"{anchor_name}的直播风格" if anchor_name else (analysis.get("name", "") if analysis else ""),
        result_summary={
            "profile": {"name": profile.get("anchor_name", ""), "followers": follower_count},
            "materials_count": len(results),
            "persona_id": persona_id,
            **({"warning": analysis_warning} if analysis_warning else {}),
        },
    )

    logger.info("Douyin user task completed: persona_id=%s, videos=%d/%d success",
                persona_id, len(successful_videos), len(results))
    return result
