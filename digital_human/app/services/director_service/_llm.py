"""Director Agent 2.0 — LLM 工序单阶段 (build prompt → rewrite → parse).

失败路径: job 标记 failed + 环节轨迹 "plan_llm"/"error" + 前端 llm_error 事件。
PlanCancelled 原样上抛 (取消语义不得吞掉)。
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import DirectorJob, Persona
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
    # 优先用爆品改造稿 (boosted_text), 让导演按观众实际听到的新稿配画面.
    # 若未改造或改造为空, 回退到原始洗稿稿.
    director_script = (script.boosted_text or script.script_text) if hasattr(script, "boosted_text") else script.script_text
    # 从改造稿提取结构意图 (钩子/预埋/回收/呼吸点/情绪), 解决导演盲盒.
    visual_intent = None
    if hasattr(script, "boosted_text") and script.boosted_text:
        try:
            from app.services.director_prompt._intent import extract_visual_intent, summarize_intent

            visual_intent = extract_visual_intent(
                script.boosted_text,
                alignment["segment_timings"],
                getattr(script, "emotion_annotations", None),
            )
            if visual_intent:
                logger.info("[director] visual_intent: %s", summarize_intent(visual_intent))
        except Exception as exc:
            logger.warning("[director] extract_visual_intent failed: %s", exc)
    # 人物级视觉主题 (2026-08-11): script.host → persona.visual_theme (科技/地缘场景词)
    visual_theme = None
    try:
        if script.host:
            persona = db.query(Persona).filter(Persona.host_id == script.host.id).first()
            if persona and getattr(persona, "visual_theme", None):
                visual_theme = persona.visual_theme
                logger.info("[director] visual_theme: %s", visual_theme)
    except Exception as exc:
        logger.warning("[director] visual_theme resolve failed: %s", exc)
    prompt = build_director_prompt(
        script_text=director_script,
        segment_timings=alignment["segment_timings"],
        material_catalog=material_catalog,
        video_format=job.video_format if job else script.video_format,
        script_title=script_title,
        enabled_pipelines=enabled_pipelines,
        visual_intent=visual_intent,
        visual_theme=visual_theme,
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
