"""HF visual workflow: 执行入口 (H 线 hf_chart / hf_title).

文本提取见 hf_extract.py, 图表归一化见 hf_chart.py, 模板选择见 common.py。
签名 ``execute_hf_visual_slot(db, slot, workflow)`` 由 slot_executor 特判调用。
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import DirectorSlot, Persona, VisualRenderJob
from app.services.slot_workflows.common import _pick_hf_template
from app.services.slot_workflows.hf_chart import _normalize_chart_input
from app.services.slot_workflows.hf_extract import _extract_hf_content

logger = logging.getLogger(__name__)

__all__ = [
    "execute_hf_visual_slot",
    "_extract_hf_content",
    "_normalize_chart_input",
    "_merge_brand",
]


def _merge_render_config(input_data: dict, render_config: dict) -> None:
    """Override title / metrics from render_config (LLM 真实数据优先)."""
    for k, v in render_config.items():
        if k == "metrics" and isinstance(v, list):
            cleaned = [{"label": str(i["label"])[:20], "value": str(i["value"])}
                       for i in v if isinstance(i, dict) and "label" in i and "value" in i]
            if cleaned:
                input_data["metrics"] = cleaned
        elif k == "title" and isinstance(v, str) and v.strip():
            input_data["title"] = v.strip()[:16]
        elif k not in ("title", "chart", "data"):
            input_data[k] = v


def _merge_brand(input_data: dict, slot: DirectorSlot, db: Session) -> None:
    """注入品牌字段 (brand_name / stamp_name / brand_tag), 供共享模板逐人设上屏.

    模板由多数数字人共享, 品牌栏/印章不再硬编码某个账号名, 而是从
    ``script → persona → host`` 闭环动态注入 (2026-08-08 整合: 人物即账号).

    取数优先级:
      1. persona.brand_name / stamp_name / brand_tag (人物页编辑, 唯一入口)
      2. host 同名字段 (旧数据回退)
      3. 中性兜底: 财经频道 / 前 2 字 / 数据解读 (保证老库零迁移也能跑)
    """
    host = slot.director_job.script.host if slot.director_job.script else None
    persona: Persona | None = None
    if db is not None:
        persona = db.query(Persona).filter(Persona.host_id == host.id).first() if host else None

    def _pick(a: str | None, b: str | None) -> str:
        return (a or b or "").strip()

    name = _pick(persona.brand_name if persona else None, host.brand_name if host else None)
    if not name and host:
        name = str(host.name or "").strip()
    input_data["brand_name"] = name or "财经频道"
    # 印章: 显式 stamp_name 优先, 否则取品牌名前 2 字竖排 (适配 120px 印章框); 短名取首个字符
    stamp = _pick(persona.stamp_name if persona else None, host.stamp_name if host else None)
    if not stamp:
        stamp = name[:2] if name else ""
    input_data["stamp_name"] = stamp or "财经"
    # 标语: 显式 brand_tag 优先, 其次 render_config 覆盖, 缺省用中性 tag
    tag = _pick(persona.brand_tag if persona else None, host.brand_tag if host else None)
    if not tag:
        tag = input_data.get("brand_tag")
    input_data["brand_tag"] = str(tag).strip() if tag else "数据解读"


def _ensure_metrics(input_data: dict) -> None:
    """Fill metrics from chart items, or give an empty placeholder row.

    input schema 强制 metrics 非空(minItems=1);口播无数字时给空占位行,
    模板 layout() 会删除空 .m-row → 视觉上标题卡只有标题+副题,不出现垃圾数字。
    """
    if not input_data.get("metrics") and input_data["chart"].get("items"):
        input_data["metrics"] = [
            {"label": it["label"], "value": str(it["value"]), "emphasis": i == 0}
            for i, it in enumerate(input_data["chart"]["items"][:4])
        ]
    if not input_data.get("metrics"):
        input_data["metrics"] = [{"label": "", "value": ""}]


def execute_hf_visual_slot(db: Session, slot: DirectorSlot, workflow: str) -> str:
    """Render an HF visual (chart or title card) for the slot duration."""
    from app.services.visual_render_service import execute_visual_render_job

    # 按 video_format 选模板: 横屏→news-magazine-v1-ls, 竖屏/方屏→news-magazine-v1
    template_id = _pick_hf_template(slot.director_job)

    duration = round(slot.end_sec - slot.start_sec, 3)
    render_config = slot.params_json.get("render_config") or {}
    input_data = _extract_hf_content(slot.text_context or "")
    input_data["duration_sec"] = max(5, min(30, round(duration)))
    # render_config 里的真实数据(如 title/metrics/chart)优先,覆盖从口播提取的结果
    _merge_render_config(input_data, render_config)

    # 品牌字段 (brand_name/stamp_name/brand_tag): 从 script → persona → host 闭环注入,
    # 模板共享, 不再硬编码"老陈聊财经"等账号名 (2026-08-08)
    _merge_brand(input_data, slot, db)

    # chart 数据贯通 (问题2): 归一化器统一 render_config.chart_type/data/label/unit/growth
    # 与口播提取结构为 {type, unit, growth, label, color_scheme, items}, 经 {{chart_json}} 进模板
    input_data["chart"] = _normalize_chart_input(render_config, input_data)
    _ensure_metrics(input_data)

    job = VisualRenderJob(template_id=template_id, input_json=input_data, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    result = execute_visual_render_job(db, job.id, template_id, input_data)
    if result.get("status") != "completed":
        raise RuntimeError(result.get("error_message") or "HF render failed")
    out_path = result.get("output_path")
    if not out_path or not Path(out_path).exists():
        raise RuntimeError("HF render output missing")
    return out_path
