"""Director 2.0 router — 视觉导演 Agent 工序单生命周期.

8 端点 (与 digital_human_video.py 对齐):
  GET  /api/director/jobs                  列任务
  POST /api/director/jobs                  创建任务 (direct: 触发 LLM 出工序单)
  GET  /api/director/jobs/{id}             详情(含 slots)
  GET  /api/director/jobs/{id}/slots       slot 列表(单独)
  POST /api/director/jobs/{id}/execute     同步执行所有 queued slot (含 audit 替换)
  POST /api/director/jobs/{id}/slots/{slot_id}/retry   手动重试 + 替换失败链路
  POST /api/director/jobs/{id}/compose     合成最终 9:16 mp4
  GET  /api/director/jobs/{id}/download    下载产物 mp4 (FileResponse)

设计要点:
  - 同步执行 (与 dhv / visual_render 一致):单 job 单次执行,前端 2s 轮询 /jobs/{id}
  - 状态机 planning → executing → reviewing → completed/failed
  - 失败替换由 slot_executor.execute_all_slots 内置调用 director_service.replace_failed_slot
  - 重试单个 slot 时若已 failed,先走 replace_failed_slot 进入下一级 fallback chain 再 execute
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db, get_session_maker
from ..models import AudioFile, DirectorJob, DirectorSlot, Script
from ..schemas import (
    DirectorDirectResponse,
    DirectorJobCreate,
    DirectorJobOut,
    DirectorSlotOut,
    RetrySlotResponse,
)
from ..services.composition_service import compose_director_job
from ..services.director_service import (
    create_director_plan,
    mark_job_reviewed,
    replace_failed_slot,
)
from ..services.gpu_service_manager import get_gpu_service_manager
from ..services.director_parser import _best_fallback_workflow
from ..services.slot_executor import (
    clear_cancel,
    execute_all_slots,
    execute_slot,
    is_cancelled,
    request_cancel,
)

# workflow → pipeline tag 映射 (与 slot_executor._EXECUTION_PHASES 保持一致)
_WORKFLOW_PIPELINE: dict[str, str | None] = {
    "host": "c",
    "mixed_host_broll": "c",
    "broll_pexels": "p",
    "hf_chart": "h",
    "hf_title": "h",
    "broll_local": None,
    "black_placeholder": None,
}


# ── 管线约束编解码 ──
# 三态语义 (2026-08-07 修复 "全开→None→无约束→host 回归" 根因):
#   None         = 全启用 (无约束, 允许 host) — 与 parser/executor 的 None 语义一致
#   set()        = 全关 (无任何管线可用, 只跑 broll_local/black_placeholder 兜底)
#   {"c","p"}    = 部分启用 (约束块 + _strip_host_mode 生效)
# 落库列 (job.pipelines): None = 全启用, "" = 全关, "c,p" = 部分启用。
# "" 必须与 None 区分: 若全关落库成 None, execute/retry 回退到 job.pipelines 时会
# 退化成全启用, fallback 链就可能引入 P/C 线 (replace_failed_slot 的 None 走 legacy 链)。
def _encode_pipelines(enabled: set[str] | None) -> str | None:
    if enabled is None:
        return None            # 全启用
    return ",".join(sorted(enabled)) if enabled else ""   # 部分启用 / 全关


def _decode_pipelines(raw: str | None) -> set[str] | None:
    """None → None(全启用); "" → set()(全关); 非空 → 管线集合 (非法值过滤)."""
    if raw is None:
        return None
    if not raw.strip():
        return set()
    return {p.strip().lower() for p in raw.split(",") if p.strip()} & {"c", "p", "h"}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/director", tags=["director"])


def _job_or_404(db: Session, job_id: str) -> DirectorJob:
    job = db.get(DirectorJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"DirectorJob {job_id} not found")
    return job


def _slot_or_404(db: Session, job_id: str, slot_id: str) -> DirectorSlot:
    slot = db.get(DirectorSlot, slot_id)
    if slot is None or slot.director_job_id != job_id:
        raise HTTPException(
            status_code=404, detail=f"DirectorSlot {slot_id} not in job {job_id}"
        )
    return slot


# ---------------------------------------------------------------------------
# 1. 列表
# ---------------------------------------------------------------------------
@router.get("/jobs", response_model=list[DirectorJobOut])
def list_jobs(limit: int = 50, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(DirectorJob).order_by(DirectorJob.created_at.desc())
    if status:
        q = q.filter(DirectorJob.status == status)
    return q.limit(limit).all()


# ---------------------------------------------------------------------------
# 2. 创建 + 触发 (后台线程, 立即返回)
# ---------------------------------------------------------------------------

_planning_jobs: set[str] = set()
_planning_lock = threading.Lock()


def _plan_in_background(job_id: str, script_id: str, audio_id: str,
                        enabled_pipelines: set[str] | None = None) -> None:
    """Run alignment + LLM planning in a dedicated thread."""
    from ..services.director_events import PlanCancelled, publish as _evt
    from ..services.director_prompt import build_real_material_catalog

    db = get_session_maker()()
    try:
        _evt(job_id, {"type": "plan_start", "msg": "开始规划: 音频对齐 + LLM 工序单"})
        _evt(job_id, {"type": "alignment_start", "msg": "音频对齐中… (段落时长完整时秒级完成)"})

        # ID-023: 规划阶段可取消 — 线程在创建后可能已被标记取消
        if is_cancelled(job_id):
            raise PlanCancelled()

        # 构建真实素材库目录（带 AI 多维标签），失败时内部 fallback 到 mock
        material_catalog = build_real_material_catalog(db)
        logger.info("[director %s] material_catalog: %d categories", job_id, len(material_catalog))

        job, alignment = create_director_plan(
            db, script_id, audio_id, job_id=job_id,
            material_catalog=material_catalog,
            is_cancelled=lambda: is_cancelled(job_id),
            enabled_pipelines=enabled_pipelines,
        )

        if job.status == "failed":
            _evt(job_id, {"type": "plan_error", "msg": job.error_message or "规划失败"})
        else:
            slot_count = len(job.slots)
            _evt(job_id, {"type": "plan_done", "msg": f"规划完成: {slot_count} slots", "slot_count": slot_count})

        logger.info("[director %s] background plan done, status=%s", job_id, job.status)
    except PlanCancelled:
        logger.info("[director %s] plan cancelled by user", job_id)
        _evt(job_id, {"type": "plan_cancelled", "msg": "用户取消，已停止规划"})
        try:
            j = db.get(DirectorJob, job_id)
            if j and j.status in ("planning", "reviewing"):
                j.status = "failed"
                j.error_message = "规划被用户取消"
                db.commit()
        except Exception:
            pass
    except Exception:
        logger.exception("[director %s] background plan crashed", job_id)
        _evt(job_id, {"type": "plan_error", "msg": "规划崩溃 (see server log)"})
        try:
            j = db.get(DirectorJob, job_id)
            if j and j.status == "planning":
                j.status = "failed"
                j.error_message = "create_director_plan crashed"
                db.commit()
        except Exception:
            pass
    finally:
        clear_cancel(job_id)
        db.close()
        with _planning_lock:
            _planning_jobs.discard(job_id)


@router.post("/jobs", response_model=DirectorDirectResponse, status_code=201)
def create_job(body: DirectorJobCreate, db: Session = Depends(get_db)):
    """创建导演任务: 立即返回 job_id, 后台线程跑 alignment + LLM 规划.

    前端拿到 job_id 后连 SSE /jobs/{id}/events 获取进度.
    """
    from ..services.director_events import publish as _evt

    script = db.get(Script, body.script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=f"Script {body.script_id} not found")

    audio_id = body.audio_file_id
    if not audio_id:
        # Auto-pick latest combined audio file for this script
        latest = None
        for job in script.audio_jobs:
            if job.status != "completed":
                continue
            for af in job.audio_files:
                if af.segment_id is None and af.duration and af.duration >= 1.0:
                    if latest is None or af.created_at > latest.created_at:
                        latest = af
        if latest is None:
            raise HTTPException(
                status_code=400,
                detail="audio_file_id 未提供,且找不到该脚本的可用整段音频 (先生成 TTS)",
            )
        audio_id = latest.id

    audio = db.get(AudioFile, audio_id)
    if audio is None:
        raise HTTPException(status_code=404, detail=f"AudioFile {audio_id} not found")
    if not Path(audio.file_path).exists():
        raise HTTPException(status_code=409, detail=f"音频文件丢失: {audio.file_path}")

    # Parse enabled pipelines from request body.
    # 三态语义 (2026-08-07): 缺失 body → None = 全启用 (向后兼容, 允许 host);
    #       "c,p,h" → {"c","p","h"} = 全开 (显式允许 host, 无约束裁剪);
    #       "c,p" → 部分启用 (约束块 + _strip_host_mode 生效);
    #       "" → set() = 全关 (只跑本地/黑场兜底)。
    enabled: set[str] | None = _decode_pipelines(body.pipelines)

    # Create placeholder job immediately
    job = DirectorJob(
        script_id=body.script_id,
        audio_file_id=audio_id,
        view_group_index=body.view_group_index,
        pipelines=_encode_pipelines(enabled),
        status="planning",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    job_id = job.id

    with _planning_lock:
        _planning_jobs.add(job_id)

    # Launch background thread
    t = threading.Thread(
        target=_plan_in_background,
        args=(job_id, body.script_id, audio_id, enabled),
        daemon=True,
        name=f"plan-{job_id[:8]}",
    )
    t.start()

    logger.info("[director %s] plan dispatched to background thread", job_id)
    return DirectorDirectResponse(
        job_id=job_id,
        status="planning",
        slot_count=0,
        message="规划已提交后台, 请通过 SSE 或轮询查看进度",
    )


# ---------------------------------------------------------------------------
# 3. 详情
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}", response_model=DirectorJobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    return _job_or_404(db, job_id)


# ---------------------------------------------------------------------------
# 4. slot 列表(单独)
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}/slots", response_model=list[DirectorSlotOut])
def list_slots(job_id: str, db: Session = Depends(get_db)):
    _job_or_404(db, job_id)
    return (
        db.query(DirectorSlot)
        .filter(DirectorSlot.director_job_id == job_id)
        .order_by(DirectorSlot.slot_index, DirectorSlot.created_at)
        .all()
    )


# ---------------------------------------------------------------------------
# 5. 执行所有 queued slot (后台线程, 不阻塞请求)
# ---------------------------------------------------------------------------

# Track which jobs are currently executing to prevent double-trigger
_executing_jobs: set[str] = set()
_executing_lock = threading.Lock()


def _execute_in_background(job_id: str, auto_replace: bool, enabled_pipelines: set[str] | None = None) -> None:
    """Run execute_all_slots in a dedicated thread with its own DB session."""
    db = get_session_maker()()
    try:
        job = execute_all_slots(db, job_id, auto_replace=auto_replace, enabled_pipelines=enabled_pipelines)
        # 进入 reviewing 阶段
        if job.status in ("completed", "failed"):
            any_completed = any(s.status == "completed" for s in job.slots)
            if any_completed:
                try:
                    mark_job_reviewed(db, job_id)
                except Exception:
                    logger.warning("mark_job_reviewed failed for %s", job_id)
        logger.info(
            "[director %s] background execute done, status=%s", job_id, job.status,
        )
    except Exception:
        logger.exception("[director %s] background execute_all_slots crashed", job_id)
        # Mark job as failed so frontend doesn't poll forever
        try:
            j = db.get(DirectorJob, job_id)
            if j and j.status == "executing":
                j.status = "failed"
                j.error_message = "execute_all_slots crashed (see server log)"
                from ..services.director_service import append_trace
                append_trace(db, j, "execute", "error", "execute_all_slots crashed")
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
        with _executing_lock:
            _executing_jobs.discard(job_id)


@router.post("/jobs/{job_id}/execute", response_model=DirectorJobOut)
def execute_job(
    job_id: str,
    auto_replace: bool = True,
    pipelines: str | None = None,
    db: Session = Depends(get_db),
):
    """触发后台执行所有 queued slot. 立即返回, 前端轮询状态.

    Query params:
        auto_replace: 是否自动运行 fallback 链 (default True)
        pipelines:   逗号分隔启用的管线, 可选 c/p/h. 默认全开.
                     例如 "c,h" 只跑 ComfyUI + HF, 跳过 Pexels.
    """
    # 解析 pipelines: query param 优先, 缺省回退到 job.pipelines 落库约束
    # (修复 C: 重启/重试不丢管线约束)。
    # 语义 (2026-08-07 统一三态): None = 全启用; set() = 全关 (只跑本地/黑场兜底);
    # 空 query ("" ) → 回退 job.pipelines; job.pipelines = "" → 全关。
    job = _job_or_404(db, job_id)
    if pipelines is not None and not pipelines.strip():
        pipelines = job.pipelines
    enabled: set[str] | None = _decode_pipelines(pipelines)
    logger.info(
        "[director %s] pipelines filter: %s",
        job_id,
        ",".join(sorted(enabled)) if enabled else ("all" if enabled is None else "none"),
    )
    if job.status == "completed":
        raise HTTPException(status_code=409, detail="job 已完成, 不可重复执行")
    if job.status == "failed" and all(s.status in ("failed", "replaced") for s in job.slots):
        raise HTTPException(status_code=409, detail="job 已失败, 请新建任务")

    # Prevent double-trigger
    with _executing_lock:
        if job_id in _executing_jobs:
            raise HTTPException(status_code=409, detail="job 正在执行中, 请勿重复触发")
        _executing_jobs.add(job_id)

    # Mark as executing immediately so frontend sees the state change
    job.status = "executing"
    db.commit()
    db.refresh(job)

    # Launch background thread (not FastAPI BackgroundTasks which waits for response)
    t = threading.Thread(
        target=_execute_in_background,
        args=(job_id, auto_replace, enabled),
        daemon=True,
        name=f"exec-{job_id[:8]}",
    )
    t.start()

    logger.info("[director %s] execute dispatched to background thread", job_id)
    return job


# ---------------------------------------------------------------------------
# 6. 重试单个 slot
# ---------------------------------------------------------------------------
def _original_workflow(slot: DirectorSlot) -> str:
    """Trace replaced_from chain back to the earliest non-fallback workflow."""
    fallback_only = {"black_placeholder"}
    params = slot.params_json or {}
    seen = {slot.workflow}
    current = params.get("replaced_from")
    while current and current not in fallback_only and current not in seen:
        seen.add(current)
        # replaced_from may itself point to a slot that was replaced earlier.
        # We do not have that slot object here, so we only go one level deep
        # via the params_json chain stored by replace_failed_slot.
        current = params.get("replaced_from")
    # If replaced_from is another fallback (should not happen) or missing,
    # prefer the first entry in the standard fallback chain.
    origin = params.get("replaced_from")
    if origin and origin not in fallback_only:
        return origin
    return "broll_pexels"


@router.post("/jobs/{job_id}/slots/{slot_id}/retry", response_model=RetrySlotResponse)
def retry_slot(
    job_id: str,
    slot_id: str,
    pipelines: str | None = None,
    db: Session = Depends(get_db),
):
    """手动重试一个 slot。

    普通 workflow: 在原 slot 上重置为 queued 并重新执行。
    black_placeholder: 恢复最初的标准 workflow（取 params_json["replaced_from"]）
    再执行，避免无意义地重试兜底。

    若提供了 pipelines 参数 (如 "c,p")，则在执行前检查 slot 的 workflow
    所属管线是否被禁用；若禁用则通过 _best_fallback_workflow 降级到替代管线。
    """
    job = _job_or_404(db, job_id)
    slot = _slot_or_404(db, job_id, slot_id)

    if slot.status in ("running",):
        raise HTTPException(
            status_code=409,
            detail=f"slot 正在执行中，请等待完成后再重新生成",
        )

    # ── 管线降级: 若 slot 的 workflow 所属管线被禁用, 自动找替代 ──
    # query param 缺省 → 回退 job.pipelines 落库约束 (修复 C)。
    # 语义 (2026-08-07 统一三态): None = 全启用; set() = 全关 (retry 时无替代管线 → 仅 broll_local)。
    if pipelines is not None and not pipelines.strip():
        pipelines = job.pipelines
    enabled_pipelines: set[str] | None = _decode_pipelines(pipelines)
    # 注意: 必须用 `is not None` 而非真值判断 — 空集合(全关)也是有效约束, 需进入降级逻辑
    if enabled_pipelines is not None:
        wf_pipeline = _WORKFLOW_PIPELINE.get(slot.workflow)
        if wf_pipeline is not None and wf_pipeline not in enabled_pipelines:
            original_wf = slot.workflow
            fallback = _best_fallback_workflow(enabled_pipelines, prefer=original_wf)
            if fallback != original_wf:
                logger.info(
                    "[director %s] retry_slot 管线降级: %s→%s (管线 %s 已禁用)",
                    job_id, original_wf, fallback, wf_pipeline.upper(),
                )
                slot.workflow = fallback
                slot.visual_type = fallback
                params = slot.params_json or {}
                params["fallback_reason"] = f"{wf_pipeline}_pipeline_disabled"
                slot.params_json = params
                db.commit()
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"管线 {wf_pipeline.upper()} 已禁用, 且 {original_wf} 无可用替代管线",
                )

    # ID-025: black_placeholder 重试必须恢复原始 workflow
    if slot.workflow == "black_placeholder":
        original = _original_workflow(slot)
        slot.workflow = original
        slot.visual_type = original
        # visual_type was set to next_workflow in replace_failed_slot; restore it too.
        logger.info("[director %s] retry_slot restoring workflow %s for slot %s", job_id, original, slot_id)

    # 在原 slot 上重置状态，不创建新 slot
    slot.status = "queued"
    slot.error_code = None
    slot.error_message = None
    slot.output_path = None
    db.commit()

    try:
        if slot.workflow in ("host", "mixed_host_broll"):
            with get_gpu_service_manager().session("comfyui"):
                slot = execute_slot(db, slot)
        else:
            slot = execute_slot(db, slot)
    except Exception as exc:
        logger.exception("retry execute_slot failed")
        raise HTTPException(status_code=500, detail=f"retry failed: {exc}")

    return RetrySlotResponse(
        slot_id=slot.id,
        status=slot.status,
        message=(
            f"slot retried (workflow={slot.workflow}), status={slot.status}"
            + (f", output={slot.output_path}" if slot.output_path else "")
            + (f", error={slot.error_message}" if slot.error_message else "")
        ),
    )


# ---------------------------------------------------------------------------
# 6a. 清理 replaced slots（fallback 链产生的旧条目）
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_id}/purge-replaced")
def purge_replaced_slots(job_id: str, db: Session = Depends(get_db)):
    """删除所有 status='replaced' 的 slot，只保留每个 slot_index 的最新活跃条目。"""
    job = _job_or_404(db, job_id)
    if job.status == "executing":
        raise HTTPException(status_code=409, detail="任务执行中，不可清理")
    replaced = [s for s in job.slots if s.status == "replaced"]
    for slot in replaced:
        db.delete(slot)
    if replaced:
        db.commit()
    logger.info("[director %s] purged %d replaced slots", job_id, len(replaced))
    return {"status": "ok", "purged_count": len(replaced)}


# ---------------------------------------------------------------------------
# 6b. 取消执行
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """发送取消信号，后台线程在下一个 phase/检查点停止。

    planning → 规划线程在下一个检查点中止; executing → 执行循环在 phase 边界停止.
    """
    job = _job_or_404(db, job_id)
    if job.status not in ("executing", "planning"):
        raise HTTPException(status_code=409, detail=f"job 状态为 {job.status}，无法取消")
    request_cancel(job_id)
    logger.info("[director %s] cancel signal sent", job_id)
    if job.status == "planning":
        return {"status": "cancelling", "message": "已发送停止信号，规划将在当前步骤完成后中止"}
    return {"status": "cancelling", "message": "已发送停止信号，将在当前阶段完成后停止"}


# ---------------------------------------------------------------------------
# 6c. 按 workflow 类型批量重试
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_id}/retry-workflow")
def retry_by_workflow(
    job_id: str,
    workflow: str,
    db: Session = Depends(get_db),
):
    """将指定 workflow 类型的所有 failed/completed/skipped slot 重置为 queued（重新生成）。"""
    job = _job_or_404(db, job_id)
    # 僵尸检测: job 状态 executing 但后台线程已死 (服务重启等)
    if job.status == "executing" and job_id not in _executing_jobs:
        job.status = "reviewing"
        db.commit()
    if job.status == "executing":
        raise HTTPException(status_code=409, detail="任务执行中，请等待完成后再重试")

    reset_count = 0
    for slot in job.slots:
        if slot.workflow == workflow and slot.status in ("failed", "completed", "skipped"):
            slot.status = "queued"
            slot.error_code = None
            slot.error_message = None
            slot.output_path = None
            reset_count += 1

    if reset_count == 0:
        raise HTTPException(status_code=404, detail=f"无 {workflow} 类型的 failed/completed/skipped slot 可重新生成")

    # 如果 job 之前是 reviewing/failed，改回 reviewing 以便再次执行
    if job.status in ("failed", "reviewing", "completed"):
        job.status = "reviewing"
    db.commit()
    logger.info("[director %s] retry-workflow %s: reset %d slots", job_id, workflow, reset_count)
    return {"status": "ok", "reset_count": reset_count, "workflow": workflow}


# ---------------------------------------------------------------------------
# 7. 合成最终 9:16 mp4  (异步 + SSE 进度透传)
# ---------------------------------------------------------------------------
_composing_lock = threading.Lock()
_composing_jobs: set[str] = set()


def _compose_in_background(
    job_id: str,
    crossfade_sec: float,
    target_lufs: float,
) -> None:
    """Run compose_director_job in a background thread with SSE progress."""
    from ..services.director_events import publish as _evt
    from ..services.composition_service import compose_director_job

    db = get_session_maker()()
    try:
        from ..models import DirectorJob as DJ
        _dj = db.get(DJ, job_id)
        if _dj:
            from ..services.director_service import append_trace
            append_trace(db, _dj, "compose", "start", f"合成开始 (crossfade={crossfade_sec}s, lufs={target_lufs})")
        result = compose_director_job(
            db, job_id,
            crossfade_sec=crossfade_sec,
            target_lufs=target_lufs,
            evt=lambda data: _evt(job_id, data),
        )
        if result.get("ok"):
            _dj = db.get(DJ, job_id)
            if _dj:
                from ..services.director_service import append_trace
                append_trace(db, _dj, "compose", "done",
                             f"合成完成: {result.get('duration_sec', 0):.1f}s → {result.get('output_path', '')}")
            # 自动登记成品库
            try:
                from ..models import VideoOutput, DirectorJob as DJ2
                job = db.get(DJ2, job_id)
                output_path = result.get("output_path", "")
                title = ""
                if job:
                    title = job.title or ""
                    if not title and job.script and job.script.script_text:
                        title = job.script.script_text[:30].replace("\n", " ").strip()
                if not title:
                    title = f"director_{job_id[:8]}"
                vo = VideoOutput(
                    job_id=job_id,
                    title=title,
                    file_path=output_path,
                    orientation=job.video_format or "portrait" if job else "portrait",
                    duration_sec=result.get("duration_sec"),
                    video_format=job.video_format if job else None,
                )
                db.add(vo)
                db.commit()
            except Exception as reg_exc:
                logger.warning("[compose] VideoOutput registration failed: %s", reg_exc)
        logger.info("[director %s] compose done, ok=%s", job_id, result.get("ok"))
    except Exception:
        logger.exception("[director %s] compose background thread crashed", job_id)
        try:
            _evt(job_id, {"type": "compose_error", "msg": "合成线程崩溃 (见服务端日志)"})
            try:
                from ..models import DirectorJob as DJ
                from ..services.director_service import append_trace
                _dj2 = db.get(DJ, job_id)
                if _dj2:
                    append_trace(db, _dj2, "compose", "error", "合成线程崩溃")
            except Exception:
                pass
        except Exception:
            pass
    finally:
        db.close()
        with _composing_lock:
            _composing_jobs.discard(job_id)


@router.post("/jobs/{job_id}/compose")
def compose_job(
    job_id: str,
    crossfade_sec: float = 0.2,
    target_lufs: float = -14.0,
    db: Session = Depends(get_db),
):
    """触发后台合成, 立即返回; 前端通过 SSE 获取进度."""
    job = _job_or_404(db, job_id)
    if not job.slots:
        raise HTTPException(status_code=409, detail="job 无 slot, 无法 compose")
    if not any(s.status == "completed" for s in job.slots):
        raise HTTPException(
            status_code=409,
            detail="至少需要 1 个 completed slot 才能 compose",
        )

    with _composing_lock:
        if job_id in _composing_jobs:
            raise HTTPException(status_code=409, detail="合成正在进行中, 请勿重复触发")
        _composing_jobs.add(job_id)

    t = threading.Thread(
        target=_compose_in_background,
        args=(job_id, crossfade_sec, target_lufs),
        daemon=True,
        name=f"compose-{job_id[:8]}",
    )
    t.start()

    return {"job_id": job_id, "status": "composing", "message": "合成已提交后台, 通过 SSE 获取进度"}


# ---------------------------------------------------------------------------
# 8. 下载产物 mp4
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}/download")
def download_job(job_id: str, db: Session = Depends(get_db)):
    job = _job_or_404(db, job_id)
    if job.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"job 状态 {job.status}, 暂未产出 (需 status=completed)",
        )
    # 优先从 composition manifest 文件读取, 其次 plan_json, 最后 fallback 搜索
    out = _find_composition_mp4(job_id)
    if not out:
        raise HTTPException(status_code=404, detail="未找到合成产物路径")
    p = Path(out)
    if not p.exists():
        raise HTTPException(status_code=410, detail=f"产物文件丢失: {p}")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)


# ---------------------------------------------------------------------------
# 8.1 打开产物所在文件夹
# ---------------------------------------------------------------------------
@router.post("/jobs/{job_id}/open-folder")
def open_output_folder(job_id: str, db: Session = Depends(get_db)):
    """打开合成产物所在的文件夹（仅 Windows 本地环境）."""
    job = _job_or_404(db, job_id)
    out = _find_composition_mp4(job_id)
    if not out:
        raise HTTPException(status_code=404, detail="未找到合成产物路径")
    folder = str(Path(out).parent)
    if not Path(folder).exists():
        raise HTTPException(status_code=410, detail=f"产物目录不存在: {folder}")
    try:
        os.startfile(folder)
        return {"status": "ok", "folder": folder}
    except Exception as exc:
        logger.exception("open folder failed")
        raise HTTPException(status_code=500, detail=f"打开文件夹失败: {exc}")


# ---------------------------------------------------------------------------
# 9. SSE 执行进度流
# ---------------------------------------------------------------------------
@router.get("/jobs/{job_id}/events")
async def job_events(request: Request, job_id: str):
    """Server-Sent Events: 实时推送 Phase/Slot 执行进度."""
    from ..services.director_events import subscribe, unsubscribe

    queue = subscribe(job_id)

    async def event_stream():
        last_evt_time = time.monotonic()
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=20.0)
                    last_evt_time = time.monotonic()
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                    if data.get("type") in ("exec_done", "exec_cancelled", "plan_done", "plan_cancelled", "plan_error", "compose_done", "compose_error"):
                        break
                except asyncio.TimeoutError:
                    # 服务端无事件超过 20s 时，向前端发送可感知的心跳，避免日志面板长时间静默
                    elapsed = int(time.monotonic() - last_evt_time)
                    hb = {"type": "heartbeat", "elapsed_sec": elapsed, "msg": "服务端仍在运行…"}
                    yield f"data: {json.dumps(hb, ensure_ascii=False)}\n\n"
        finally:
            unsubscribe(job_id, queue)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _find_composition_mp4(job_id: str) -> str | None:
    """回退:在 composition_output_root 下找 director_<job_id>.mp4."""
    from ..config import get_config

    cfg = get_config()
    root = Path(cfg.defaults.composition_output_root) / job_id
    if not root.exists():
        return None
    cand = root / f"director_{job_id}.mp4"
    return str(cand) if cand.exists() else None


# ---------------------------------------------------------------------------
# 9. 任务清理
# ---------------------------------------------------------------------------
@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """删除单个导演任务及其所有 slots + 磁盘文件。执行中的任务不可删除。"""
    job = _job_or_404(db, job_id)
    if job.status == "executing":
        raise HTTPException(status_code=409, detail="任务执行中，不可删除")
    # 删除关联 slots（cascade 已配置，但显式删除更安全）
    for slot in list(job.slots):
        db.delete(slot)
    db.delete(job)
    db.commit()
    _cleanup_job_files(job_id)
    logger.info("[director] deleted job %s (with files)", job_id)
    return {"status": "ok", "deleted": job_id}


@router.post("/jobs/cleanup")
def cleanup_jobs(
    only_empty: bool = True,
    db: Session = Depends(get_db),
):
    """批量清理导演任务 + 磁盘文件。

    only_empty=True: 只清理无任何 completed slot 的任务（从未产出视频）
    only_empty=False: 清理所有 failed/planning 状态的任务
    执行中的任务始终跳过。
    """
    candidates = (
        db.query(DirectorJob)
        .filter(DirectorJob.status.in_(["failed", "planning", "reviewing"]))
        .all()
    )
    deleted_ids: list[str] = []
    for job in candidates:
        if only_empty:
            has_completed = any(s.status == "completed" for s in job.slots)
            if has_completed:
                continue
        for slot in list(job.slots):
            db.delete(slot)
        db.delete(job)
        deleted_ids.append(job.id)

    if deleted_ids:
        db.commit()
    for jid in deleted_ids:
        _cleanup_job_files(jid)
    logger.info("[director] cleanup deleted %d job(s) (with files)", len(deleted_ids))
    return {"status": "ok", "deleted_count": len(deleted_ids), "deleted_ids": deleted_ids}


def _cleanup_job_files(job_id: str) -> None:
    """Remove director output + composition directories for a job."""
    import shutil
    from ..config import get_config
    cfg = get_config()
    dirs_to_remove = [
        Path(cfg.defaults.director_output_root) / job_id,
        Path(cfg.defaults.composition_output_root) / job_id,
    ]
    for d in dirs_to_remove:
        if d.exists() and d.is_dir():
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception as exc:
                logger.warning("[cleanup] failed to remove %s: %s", d, exc)