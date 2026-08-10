"""Director slot 重试端点: 单 slot / 批量 / purge replaced.

原 `retry_slot`(87 行)拆分为 `_apply_retry_pipeline_degrade`(管线降级块)
与 `_reset_slot_for_retry`(状态重置), 端点主体 ≤40 行。
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DirectorJob, DirectorSlot
from app.schemas import RetrySlotResponse
from app.services.director_parser import _best_fallback_workflow
from app.services.slot_executor import execute_slot
from app.services.director_events import publish as _evt
from app.routers.director_routes.common import (
    _WORKFLOW_PIPELINE, _decode_pipelines, _job_or_404, _slot_or_404,
)
from app.routers.director_routes.execution import _executing_jobs

logger = logging.getLogger(__name__)

retry_router = APIRouter(tags=["director"])

__all__ = ["retry_router", "_original_workflow", "_apply_retry_pipeline_degrade",
           "_reset_slot_for_retry", "_restore_original_workflow", "_execute_slot_retry"]


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


def _apply_retry_pipeline_degrade(db: Session, job_id: str,
                                  slot: DirectorSlot, pipelines: str | None) -> None:
    """If slot's workflow pipeline is disabled, degrade to an allowed pipeline.

    pipelines 已在端点解析 (query param 缺省回退 job.pipelines)。
    注意: 用 `is not None` 判断空集合(全关) — 空集合也是有效约束, 需进入降级逻辑。
    """
    enabled_pipelines: set[str] | None = _decode_pipelines(pipelines)
    if enabled_pipelines is None:
        return
    wf_pipeline = _WORKFLOW_PIPELINE.get(slot.workflow)
    if wf_pipeline is None or wf_pipeline in enabled_pipelines:
        return
    original_wf = slot.workflow
    fallback = _best_fallback_workflow(enabled_pipelines, prefer=original_wf)
    if fallback == original_wf:
        raise HTTPException(
            status_code=400,
            detail=f"管线 {wf_pipeline.upper()} 已禁用, 且 {original_wf} 无可用替代管线",
        )
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


def _reset_slot_for_retry(slot: DirectorSlot) -> None:
    """Reset slot status on the original row (not creating a new slot)."""
    slot.status = "queued"
    slot.error_code = None
    slot.error_message = None
    slot.output_path = None


def _job_truly_executing(job: DirectorJob) -> bool:
    """僵尸检测: job 是否真正在后台执行中.

    running slot 可能是服务重启/执行中断留下的僵尸状态 (job 已不在
    _executing_jobs 且状态非 executing)。此时允许重试恢复, 而非 409 拒绝。
    """
    return job.status == "executing" and job.id in _executing_jobs


def _restore_original_workflow(job_id: str, slot: DirectorSlot) -> None:
    """ID-025: black_placeholder 重试必须恢复原始 workflow."""
    if slot.workflow != "black_placeholder":
        return
    original = _original_workflow(slot)
    slot.workflow = original
    slot.visual_type = original
    # visual_type was set to next_workflow in replace_failed_slot; restore it too.
    logger.info("[director %s] retry_slot restoring workflow %s for slot %s", job_id, original, slot.id)


def _execute_slot_retry(db: Session, slot: DirectorSlot) -> DirectorSlot:
    """Run execute_slot, holding a comfyui GPU session for host pipelines."""
    if slot.workflow in ("host", "mixed_host_broll"):
        from app.services.gpu_service_manager import get_gpu_service_manager
        with get_gpu_service_manager().session("comfyui"):
            return execute_slot(db, slot)
    return execute_slot(db, slot)


@retry_router.post("/jobs/{job_id}/slots/{slot_id}/retry", response_model=RetrySlotResponse)
def retry_slot(
    job_id: str,
    slot_id: str,
    pipelines: str | None = None,
    db: Session = Depends(get_db),
):
    """手动重试一个 slot: 重置为 queued 后重新执行, 必要时降级管线/恢复原始 workflow."""
    job = _job_or_404(db, job_id)
    slot = _slot_or_404(db, job_id, slot_id)

    if slot.status == "running":
        if _job_truly_executing(job):
            raise HTTPException(status_code=409,
                                detail="slot 正在执行中，请等待完成后再重新生成")
        # 僵尸 running: job 不在后台执行 (服务重启/中断遗留), 放行重试
        logger.warning("[director %s] slot %s status=running but job not executing, "
                       "treat as zombie and allow retry",
                       job_id, slot.id)
        slot.status = "queued"
        db.commit()

    # ── 管线降级: 若 slot workflow 管线被禁用则自动找替代 (query 缺省回退 job.pipelines; 三态 None/空/部分) ──
    if pipelines is not None and not pipelines.strip():
        pipelines = job.pipelines
    _apply_retry_pipeline_degrade(db, job_id, slot, pipelines)
    _restore_original_workflow(job_id, slot)

    # 在原 slot 上重置状态，不创建新 slot
    _reset_slot_for_retry(slot)
    db.commit()
    logger.info("[director %s] retry_slot %s (workflow=%s) reset to queued",
                job_id, slot.id, slot.workflow)
    _evt(job_id, {"type": "slot_start", "slot_index": slot.slot_index,
                  "workflow": slot.workflow, "msg": f"Slot #{slot.slot_index} 重试开始"})

    # force 标记无天然清理点: 每个新执行入口显式清除
    from app.services.slot_executor import clear_force_stopped
    clear_force_stopped(job_id)

    try:
        slot = _execute_slot_retry(db, slot)
    except Exception as exc:
        logger.exception("retry execute_slot failed")
        _evt(job_id, {"type": "slot_fail", "slot_index": slot.slot_index,
                      "workflow": slot.workflow, "error": str(exc)[:200],
                      "msg": f"Slot #{slot.slot_index} 重试失败"})
        raise HTTPException(status_code=500, detail=f"retry failed: {exc}")

    if slot.status == "completed":
        logger.info("[director %s] retry_slot %s done, output=%s",
                    job_id, slot.id, slot.output_path)
        _evt(job_id, {"type": "slot_done", "slot_index": slot.slot_index,
                      "workflow": slot.workflow, "msg": f"Slot #{slot.slot_index} 重试完成"})
    else:
        logger.warning("[director %s] retry_slot %s failed: %s",
                       job_id, slot.id, slot.error_message)
        _evt(job_id, {"type": "slot_fail", "slot_index": slot.slot_index,
                      "workflow": slot.workflow, "error": slot.error_message or "",
                      "msg": f"Slot #{slot.slot_index} 重试失败"})

    return RetrySlotResponse(
        slot_id=slot.id,
        status=slot.status,
        message=(
            f"slot retried (workflow={slot.workflow}), status={slot.status}"
            + (f", output={slot.output_path}" if slot.output_path else "")
            + (f", error={slot.error_message}" if slot.error_message else "")
        ),
    )


@retry_router.post("/jobs/{job_id}/purge-replaced")
def purge_replaced_slots(job_id: str, db: Session = Depends(get_db)):
    """删除所有 status='replaced' 的 slot，只保留每个 slot_index 的最新活跃条目。"""
    job = _job_or_404(db, job_id)
    if job.status == "executing":
        raise HTTPException(status_code=409, detail="任务执行中，不可清理")
    replaced = [s for s in job.slots if s.status == "replaced"]
    # 素材生命周期 (2026-08-07): 连带删除被替换 slot 的磁盘目录, 避免孤儿残留。
    # replaced slot 有独立目录 (composition_output_root/<job_id>/slots/<slot_id>),
    # 与活跃 slot 互不冲突; 保留策略下仅此路径负责回收被替换 slot 的旧素材。
    import shutil
    from app.config import get_config
    cfg = get_config()
    for slot in replaced:
        dir_to_remove = Path(cfg.defaults.composition_output_root) / job_id / "slots" / str(slot.id)
        if dir_to_remove.exists() and dir_to_remove.is_dir():
            try:
                shutil.rmtree(dir_to_remove, ignore_errors=True)
                logger.info("[director %s] purge removed replaced-slot dir %s", job_id, dir_to_remove)
            except Exception as exc:
                logger.warning("[director %s] purge failed to remove %s: %s", job_id, dir_to_remove, exc)
    for slot in replaced:
        db.delete(slot)
    if replaced:
        db.commit()
    logger.info("[director %s] purged %d replaced slots", job_id, len(replaced))
    return {"status": "ok", "purged_count": len(replaced)}


@retry_router.post("/jobs/{job_id}/retry-workflow")
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
            _reset_slot_for_retry(slot)
            reset_count += 1

    if reset_count == 0:
        raise HTTPException(status_code=404, detail=f"无 {workflow} 类型的 failed/completed/skipped slot 可重新生成")

    # 如果 job 之前是 reviewing/failed，改回 reviewing 以便再次执行
    if job.status in ("failed", "reviewing", "completed"):
        job.status = "reviewing"
    db.commit()

    # force 标记无天然清理点: 每个新执行入口显式清除
    from app.services.slot_executor import clear_force_stopped
    clear_force_stopped(job_id)

    logger.info("[director %s] retry-workflow %s: reset %d slots", job_id, workflow, reset_count)
    return {"status": "ok", "reset_count": reset_count, "workflow": workflow}
