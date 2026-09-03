"""Audio router: TTS generation and downloads."""
from __future__ import annotations

import datetime
import json
import logging
import threading
import time
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import db_session, get_db, get_session_maker
from ..models import AudioFile, AudioJob, Host, Persona, Script, Segment, Voice
from ..schemas import AudioFileOut, AudioJobOut
from ..services.gpu_service_manager import get_gpu_service_manager
from ..services.tts_service import TTSService
from .jobs import _publish

router = APIRouter(prefix="/api/audio", tags=["audio"])

logger = logging.getLogger(__name__)

# ── TTS 任务停止 (2026-09-02): 段间软取消 ──
# cancel 端点把 job_id 放入集合; _do_tts 在段间检查点 (情绪标注后 / 每段 progress 回调)
# 抛 _TTSCancelled 中断合成。已生成段 wav 保留, 重新生成走 _skip_batch 断点续传。
# 不强杀 GPU 服务: 进行中的批次 (一次 HTTP 合成调用) 做完后才中断, 前端提示"当前批次完成后中断"。
_cancel_requested: set[str] = set()
_cancel_lock = threading.Lock()


class _TTSCancelled(Exception):
    """用户点了停止按钮 (audio.html), TTS 任务在段间检查点主动中断。"""


def _check_cancel(job_id: str) -> None:
    with _cancel_lock:
        if job_id in _cancel_requested:
            raise _TTSCancelled()


def _cancel_done(job_id: str) -> None:
    with _cancel_lock:
        _cancel_requested.discard(job_id)


def get_tts() -> TTSService:
    from ..config import get_config

    cfg = get_config()
    return TTSService(cfg.defaults)


@router.post("/scripts/{script_id}/generate-audio", response_model=AudioJobOut)
def generate_audio(
    script_id: str,
    voice_id: str | None = None,
    selected_only: bool = True,
    background_tasks: BackgroundTasks = ...,
    db: Session = Depends(get_db),
    tts: TTSService = Depends(get_tts),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    voice = None
    if voice_id:
        voice = db.query(Voice).filter(Voice.id == voice_id).first()
    # 未显式选音色 → 人物即账号 (2026-08-08): 优先 persona.voice_id (人物页编辑的音色),
    # 其次 host.default_voice_id (老陈默认=大学教授 indextts), 最后 host 下第一条 voice。
    if not voice and script.host_id:
        persona = (
            db.query(Persona).filter(Persona.host_id == script.host_id).first()
        )
        if persona and persona.voice_id:
            voice = db.query(Voice).filter(Voice.id == persona.voice_id).first()
    if not voice and script.host_id:
        host = db.query(Host).filter(Host.id == script.host_id).first()
        if host and host.default_voice_id:
            voice = db.query(Voice).filter(Voice.id == host.default_voice_id).first()
    if not voice and script.host_id:
        voice = db.query(Voice).filter(Voice.host_id == script.host_id).first()

    query = db.query(Segment).filter(Segment.script_id == script_id)
    if selected_only:
        query = query.filter(Segment.selected_for_host == True)
    segments = query.order_by(Segment.host_order).all()

    if not segments:
        raise HTTPException(status_code=400, detail="No segments to synthesize")

    project_root = Path(__file__).resolve().parents[2]
    if script.project_dir:
        output_dir = Path(script.project_dir) / "audio"
    else:
        today = datetime.date.today().isoformat()
        voice_label = voice.name if voice else "default"
        voice_id_short = voice.id[:8] if voice else "default"
        output_dir = Path(r"E:\数字人计划\outputs\audio") / today / voice_label / f"{voice_id_short}_{int(time.time())}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── 过期音频清理 (方案A, 2026-08-12) ──
    # 文稿改动 (update_script) 已把旧 completed AudioJob 标记为 stale。
    # 点"生成音频"时: 清空 stale job 的磁盘 wav + 删除 DB 记录 → 强制重新合成,
    # 杜绝 `_skip_batch` 断点续传误复用旧音频。
    stale_jobs = (
        db.query(AudioJob)
        .filter(AudioJob.script_id == script_id, AudioJob.status == "stale")
        .all()
    )
    for stale_job in stale_jobs:
        stale_dir = Path(stale_job.output_dir)
        if stale_dir.exists():
            # 只清 wav/manifest, 不误删目录 (目录可能被其他 job 共享)
            for pat in ("*.wav", "manifest.json", "full_paragraph.wav"):
                try:
                    for p in stale_dir.glob(pat):
                        p.unlink(missing_ok=True)
                except OSError:
                    logger.warning(
                        "generate_audio: 清理 stale job %s 的 %s 失败", stale_job.id[:8], pat,
                        exc_info=True,
                    )
        db.delete(stale_job)  # 连带 audio_files (cascade delete-orphan)
    if stale_jobs:
        logger.info(
            "generate_audio: script %s 清理 %d 个 stale AudioJob, 强制重新生成音频",
            script_id[:8], len(stale_jobs),
        )
        db.commit()

    job = AudioJob(
        script_id=script_id,
        voice_id=voice.id if voice else None,
        output_dir=str(output_dir),
        status="pending",
        total_segments=len(segments),
        completed_segments=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_do_tts, job.id)
    return job


def _do_tts(job_id: str):
    if get_session_maker() is None:
        _publish(job_id, {"type": "tts_error", "error": "Database not initialized"})
        return
    with db_session() as db:
        try:
            job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
            if not job:
                _publish(job_id, {"type": "tts_error", "error": "Audio job not found"})
                return

            script = db.query(Script).filter(Script.id == job.script_id).first()
            voice = None
            if job.voice_id:
                voice = db.query(Voice).filter(Voice.id == job.voice_id).first()

            query = db.query(Segment).filter(Segment.script_id == job.script_id)
            query = query.filter(Segment.selected_for_host == True)
            segments = query.order_by(Segment.host_order).all()

            # 段数据快照 (2026-08-25): 必须在下方 status=running 的 db.commit() 之前提取。
            # commit 令 ORM expire; TTS 长任务 (GPU 冷启动+逐段合成) 期间若文稿被保存,
            # _reparse_segments 删旧建新行, 旧对象 refresh 不到行 → "Segment has been
            # deleted" → job 卡 failed 且 0 段完成 (audio 线实测)。之后全程只用纯数据。
            seg_pairs: list[tuple[str, str]] = [(s.id, s.text) for s in segments]

            if not segments:
                job.status = "failed"
                job.error_message = "No segments to synthesize"
                db.commit()
                _publish(job_id, {"type": "tts_error", "error": "No segments to synthesize"})
                return

            job.status = "running"
            job.total_segments = len(segments)
            db.commit()

            tts = get_tts()

            # ── 情绪标注 (2026-08-25 从爆品改造拆出, 移至生成音频时刻) ──
            # 单一事实源: 用与 TTS 完全同源的文本现场标注 → 不存在"改稿后旧标注
            # 错配"窗口 (此前靠改稿清空+异步重跑兜)。失败落整篇兜底: 新闻线
            # surprised/3 (2026-08-27 惊讶打底定稿), 读书线 calm/2 (2026-09-03)。
            # 耗时 ~10-30s, 藏在 TTS 引擎冷启动 (~2min) 里零感知。
            emotion_segments: list | None = None
            from ..services.pinyin_fix import apply_pinyin_marks, scan_pinyin_hits
            from ..services.boost_service import annotate_emotions, _parse_emotion_annotations
            clean_text = "\n".join(t for _, t in seg_pairs)
            # 词表命中提示 (2026-09-03): 扫干净文本, 命中即推 SSE。
            hits = scan_pinyin_hits(clean_text)
            if hits:
                _publish(job_id, {"type": "tts_service",
                                  "message": f"纠音词表命中 {len(hits)} 处: {'、'.join(hits)}"})
            tts_text = apply_pinyin_marks(clean_text)
            _publish(job_id, {"type": "tts_service", "message": "情绪标注中…"})
            # 读书线分流 (2026-09-03): 拆书稿 prompt_template="jingshu-book" (persona.py
            # 定死, 逐集继承) → 读书版情绪规则 (calm+confident 混合打底 + melancholic
            # 共情), 惊讶打底铁律只属新闻线。
            style = ("book" if script and script.prompt_template
                     and "book" in script.prompt_template else "news")
            fallback = ({"emotion": "calm", "strength": 2, "text": tts_text} if style == "book"
                        else {"emotion": "surprised", "strength": 3, "text": tts_text})
            try:
                persona_name = "老谭"
                if script and script.host:
                    persona_name = (
                        getattr(script.host, "stamp_name", None) or script.host.name
                    ) or ("静姐" if style == "book" else "老谭")
                raw_anno = annotate_emotions(tts_text, persona_name, style=style)
                parsed = _parse_emotion_annotations(raw_anno) if raw_anno else None
                if parsed:
                    emotion_segments = parsed
                    script.emotion_annotations = raw_anno  # 写回供前端/诊断显示
                    db.commit()
                    _publish(job_id, {"type": "tts_service",
                                      "message": f"情绪标注完成: {len(parsed)} 段"})
                else:
                    emotion_segments = [dict(fallback)]
                    _publish(job_id, {"type": "tts_service",
                                      "message": "情绪标注解析失败, 整篇打底兜底"})
            except Exception as exc:
                logger.warning("[tts %s] emotion annotate failed, fallback: %s",
                               job_id[:8], exc)
                emotion_segments = [dict(fallback)]
                _publish(job_id, {"type": "tts_service",
                                  "message": "情绪标注失败, 整篇打底兜底"})

            # 停止检查点 1/2 (2026-09-02): 情绪标注 (~10-30s) 期间收到的停止请求在此生效
            _check_cancel(job_id)

            def _progress(completed: int, total: int, text: str | None, audio_file: AudioFile | None = None) -> None:
                # 停止检查点 2/2: 每段 progress 回调 (合成循环的段间边界)
                _check_cancel(job_id)
                job.completed_segments = completed
                db.commit()
                event: dict = {
                    "type": "tts_progress",
                    "completed": completed,
                    "total": total,
                    "text": text,
                }
                if audio_file:
                    db.add(audio_file)
                    db.commit()
                    db.refresh(audio_file)
                    event["audio_file"] = {
                        "id": audio_file.id,
                        "filename": audio_file.filename,
                        "duration": audio_file.duration,
                        "segment_id": audio_file.segment_id,
                    }
                _publish(job_id, event)

            # ── GPU 服务托管: 排队 + 按需拉起 TTS 后端 + 空闲自动关停腾显存 ──
            from ..config import get_config

            backend = (voice.backend if voice and voice.backend else get_config().defaults.backend)

            def _svc_notify(message: str) -> None:
                _publish(job_id, {"type": "tts_service", "message": message})

            manager = get_gpu_service_manager()
            with manager.session(backend, status_callback=_svc_notify):
                result = tts.generate(
                    job, seg_pairs, voice, progress_callback=_progress,
                    emotion_annotations=emotion_segments,  # 现场标注 (同源文本), 不读库
                    status_callback=lambda m, lv: _publish(
                        job_id, {"type": "tts_service", "message": m}),
                )
            # audio_files rows are already committed one-by-one inside _progress,
            # so no add_all here — a second add would double-insert (P0-1 related).

            for af in result["audio_files"]:
                if af.segment_id and af.duration:
                    seg = db.query(Segment).filter(Segment.id == af.segment_id).first()
                    if seg:
                        seg.estimated_duration = af.duration

            # ── Save combined paragraph audio as AudioFile ──
            combined_info = result.get("combined_file")
            combined_audio_file = None
            if combined_info and combined_info.get("file_path"):
                combined_audio_file = AudioFile(
                    audio_job_id=job.id,
                    segment_id=None,
                    filename=combined_info["file"],
                    file_path=combined_info["file_path"],
                    duration=combined_info.get("duration"),
                    sample_rate=combined_info.get("sample_rate"),
                )
                db.add(combined_audio_file)

            job.status = "completed"
            job.completed_segments = len(segments)
            db.commit()

            output_dir = Path(job.output_dir)
            done_event: dict = {"type": "tts_done", "job_id": job.id, "output_dir": str(output_dir)}
            if combined_audio_file:
                done_event["combined_audio"] = {
                    "id": combined_audio_file.id,
                    "filename": combined_audio_file.filename,
                    "duration": combined_audio_file.duration,
                }
            _publish(job_id, done_event)
        except _TTSCancelled:
            try:
                job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
                if job:
                    job.status = "cancelled"
                    job.error_message = "用户停止 — 已生成音频保留，重新生成将从断点继续"
                    db.commit()
            except Exception:
                pass
            _publish(job_id, {"type": "tts_cancelled", "job_id": job_id})
        except Exception as exc:
            try:
                job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    # P0-1 方案 1: 失败不删盘 → 已生成 wav 保留, 可重试续传
                    job.error_message = f"{exc}（已生成的音频已保留，重新生成将从断点继续）"
                    db.commit()
            except Exception:
                pass
            _publish(job_id, {"type": "tts_error", "error": str(exc)})
        finally:
            _cancel_done(job_id)


@router.get("/jobs", response_model=list[AudioJobOut])
def list_audio_jobs(
    script_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """查询音频任务，支持按 script_id / status 过滤."""
    query = db.query(AudioJob)
    if script_id:
        query = query.filter(AudioJob.script_id == script_id)
    if status:
        query = query.filter(AudioJob.status == status)
    return query.order_by(AudioJob.created_at.desc()).limit(limit).all()


@router.get("/jobs/{job_id}", response_model=AudioJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=AudioJobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """请求停止 TTS 任务 (段间软取消, 已生成段保留断点续传).

    首次点击: pending/running → cancelling, 合成线程在下个检查点中断。
    二次点击 (仍 cancelling): 强制落 cancelled — 兜底线程已死 (服务重启/HTTP 卡死)
    的僵尸 cancelling, 让前端立即复位。
    """
    job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    if job.status in ("completed", "failed", "cancelled"):
        return job  # 已终态, 幂等返回
    with _cancel_lock:
        _cancel_requested.add(job_id)
    if job.status == "cancelling":
        job.status = "cancelled"
        job.error_message = "用户停止（强制）— 已生成音频保留，重新生成将从断点继续"
        db.commit()
        db.refresh(job)
        _publish(job_id, {"type": "tts_cancelled", "job_id": job_id})
    else:
        job.status = "cancelling"
        db.commit()
        db.refresh(job)
        _publish(job_id, {"type": "tts_cancelling", "message": "已请求停止 — 当前批次完成后中断"})
    return job


@router.get("/jobs/{job_id}/files", response_model=list[AudioFileOut])
def list_job_files(job_id: str, db: Session = Depends(get_db)):
    return db.query(AudioFile).filter(AudioFile.audio_job_id == job_id).order_by(AudioFile.filename).all()


@router.get("/files/{file_id}/download")
def download_file(file_id: str, db: Session = Depends(get_db)):
    af = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not af:
        raise HTTPException(status_code=404, detail="Audio file not found")
    path = Path(af.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="audio/wav", filename=af.filename)


@router.get("/jobs/{job_id}/manifest")
def download_manifest(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AudioJob).filter(AudioJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audio job not found")
    manifest_path = Path(job.output_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    return FileResponse(manifest_path, media_type="application/json", filename="manifest.json")


@router.post("/scripts/{script_id}/replace-char")
def replace_char(
    script_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """错别字音频替换 (2026-08-11): 把含生僻字的段改字后重做 TTS.

    背景: indextts 不认识生僻字(如"昇"), 遇到就读错/乱读, 污染整段音频.
    方案: 找到含原字的 segments → text 替换 → 单段重做 TTS → 替换 wav → 重合成.

    payload: {"from_char": "昇", "to_char": "升"}
    """
    from scripts import tts_client  # noqa: F401
    from ..services.tts_service import TTSService

    from_char = (payload.get("from_char") or "").strip()
    to_char = (payload.get("to_char") or "").strip()
    if not from_char or not to_char:
        raise HTTPException(status_code=400, detail="from_char/to_char 必填")

    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # 1. 找含原字的 segments
    segments = db.query(Segment).filter(
        Segment.script_id == script_id,
        Segment.text.contains(from_char),
    ).all()
    if not segments:
        return {"ok": True, "replaced": 0, "msg": f"未找到含'{from_char}'的段"}

    # 2. 找到该 script 的 audio_job (最新 completed)
    job = (
        db.query(AudioJob)
        .filter(AudioJob.script_id == script_id, AudioJob.status == "completed")
        .order_by(AudioJob.created_at.desc())
        .first()
    )
    if not job:
        return {"ok": False, "msg": "未找到已完成音频任务"}

    voice = db.query(Voice).filter(Voice.id == job.voice_id).first()
    output_dir = Path(job.output_dir)

    # 3. 确保 TTS 引擎 (indextts) 在线, 逐段重做 + 替换 wav
    from ..services.gpu_service_manager import get_gpu_service_manager

    manager = get_gpu_service_manager()
    replaced = 0
    # 词表校正 (2026-09-03): 此路径直调 synthesize_lines 绕过了 tts_service 的
    # apply_pinyin_marks 注入 — 改错字重合成时词表词 (铟/昇) 会退回错读, 补上。
    # 标注只进 TTS 输入, DB 稿件存干净文本。
    from ..services.pinyin_fix import apply_pinyin_marks

    with manager.session(voice.backend if voice else "auto"):
        for seg in segments:
            seg.text = seg.text.replace(from_char, to_char)
            db.commit()
            new_text = apply_pinyin_marks(seg.text)

            temp_dir = output_dir / f"replace_{seg.id[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            try:
                tts_client.synthesize_lines(
                    text=new_text,
                    output_dir=temp_dir,
                    backend=voice.backend if voice else "auto",
                    voice_id=voice.name if voice else "default",
                    reference_audio=Path(voice.reference_audio_path) if voice and voice.reference_audio_path else None,
                    reference_text=voice.reference_text or "" if voice else "",
                    base_url_fish=voice.base_url_fish if voice else None,
                    base_url_f5=voice.base_url_f5 if voice else None,
                    base_url_indextts=voice.base_url_indextts if voice else None,
                    master_audio=Path(voice.master_audio_path) if voice and voice.master_audio_path else None,
                    master_text=voice.master_text or "" if voice else "",
                    params=(
                        json.loads(voice.config_json) if isinstance(voice.config_json, str)
                        else (voice.config_json or {}).get("params")
                    ) if voice and voice.config_json else None,
                )
                new_wavs = sorted(temp_dir.glob("*.wav"))
                if not new_wavs:
                    continue
                new_wav = new_wavs[0]

                af = (
                    db.query(AudioFile)
                    .filter(AudioFile.audio_job_id == job.id, AudioFile.segment_id == seg.id)
                    .first()
                )
                if af:
                    old_path = Path(af.file_path)
                    if old_path.exists():
                        old_path.unlink()
                    new_dest = old_path if old_path.parent.exists() else temp_dir / new_wav.name
                    import shutil
                    shutil.copy2(new_wav, new_dest)
                    af.file_path = str(new_dest)
                    af.duration = None
                    db.commit()
                replaced += 1
            except Exception as exc:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"段 {seg.id[:8]} 重做失败: {exc}")

    # 4. 重合成 full_paragraph.wav (concat 所有段)
    try:
        from scripts.tts_client import _concat_wavs_with_ffmpeg

        all_afs = (
            db.query(AudioFile)
            .filter(AudioFile.audio_job_id == job.id, AudioFile.segment_id.isnot(None))
            .order_by(AudioFile.filename)
            .all()
        )
        wavs = [Path(af.file_path) for af in all_afs if Path(af.file_path).exists()]
        if wavs:
            combined = output_dir / "full_paragraph.wav"
            _concat_wavs_with_ffmpeg(wavs, combined)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"重合成失败: {exc}")

    return {"ok": True, "replaced": replaced, "msg": f"替换完成, 重做 {replaced} 段"}