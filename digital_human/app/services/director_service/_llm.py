"""Director Agent 2.0 — LLM 工序单阶段 (build prompt → rewrite → parse).

失败路径: job 标记 failed + 环节轨迹 "plan_llm"/"error" + 前端 llm_error 事件。
PlanCancelled 原样上抛 (取消语义不得吞掉)。
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import DirectorJob
from app.services.director_events import PlanCancelled, publish as _evt
from app.services.director_parser import parse_llm_plan
from app.services.director_prompt import build_director_prompt
from app.services.director_service._trace import append_trace
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

__all__ = ["_llm_plan_phase"]


def _llm_plan_phase(
    db: Session,
    job: DirectorJob,
    job_id: str | None,
    alignment: dict[str, Any],
    script: Any,
    script_title: str | None,
    material_catalog: dict[str, Any] | None,
    total_duration: float,
    enabled_pipelines: set[str] | None,
    is_cancelled: Callable[[], bool] | None,
) -> Any:
    """Run LLM plan phase, return parsed plan or None (failed path handled)."""
    cfg = get_config()
    llm = LLMService(cfg.deepseek)
    prompt = build_director_prompt(
        script_text=script.script_text,
        segment_timings=alignment["segment_timings"],
        material_catalog=material_catalog,
        video_format=job.video_format if job else script.video_format,
        script_title=script_title,
        enabled_pipelines=enabled_pipelines,
    )

    try:
        raw_output = llm.rewrite_article(
            raw_text=prompt,
            model="pro",
            stream=False,
        )
        if is_cancelled and is_cancelled():
            raise PlanCancelled
        plan = parse_llm_plan(
            raw_output,
            alignment["segment_timings"],
            total_duration,
            enabled_pipelines=enabled_pipelines,
        )
        append_trace(
            db, job, "plan_llm", "done",
            f"LLM 工序单完成: {len(plan.slots)} slots (prompt ~{len(prompt)//1024}KB)",
        )
        return plan
    except PlanCancelled:
        raise
    except Exception as exc:
        job.status = "failed"
        job.error_message = f"director agent failed: {type(exc).__name__}: {exc}"
        append_trace(db, job, "plan_llm", "error", f"LLM 规划失败: {str(exc)[:200]}")
        db.commit()
        if job_id:
            _evt(job_id, {"type": "llm_error", "msg": str(exc)[:200]})
        return None
