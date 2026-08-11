"""HF visual workflow: 执行入口 (H 线 hf_chart / hf_title).

文本提取见 hf_extract.py, 图表归一化见 hf_chart.py, 模板选择见 common.py。
签名 ``execute_hf_visual_slot(db, slot, workflow)`` 由 slot_executor 特判调用。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import DirectorSlot, Persona, VisualRenderJob
from app.schemas import get_video_format_spec
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
    """Render an HF visual (chart / title card / opening text card) for the slot duration."""
    from app.services.visual_render_service import execute_visual_render_job

    # 开场字幕卡 (hf_opening): 走专属模板 + 多行台词, 禁忌警告风
    if workflow == "hf_opening":
        return _execute_hf_opening(db, slot)

    # 引用卡 (hf_quote): 一句话观点 + 出处/人物, 黑金质感
    if workflow == "hf_quote":
        return _execute_hf_quote(db, slot)

    # 按 video_format 选模板: 横屏→news-magazine-v1-ls, 竖屏/方屏→news-magazine-v1
    template_id = _pick_hf_template(slot.director_job)

    # 财经质感模板 (2026-08-11): hf_title/hf_chart 优先用 v2 财经版 (深炭+暖金, 同 v3 片头体系)
    if workflow in ("hf_title", "hf_chart"):
        spec = get_video_format_spec(slot.director_job.video_format)
        if spec["width"] > spec["height"]:
            # 横屏 v2 模板当前未做 -ls, 用基础 v2 (1920x1080 已横屏)
            template_id = "hf-title-v2" if workflow == "hf_title" else "hf-chart-v2"
        else:
            template_id = "hf-title-v2" if workflow == "hf_title" else "hf-chart-v2"

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


def _execute_hf_opening(db: Session, slot: DirectorSlot) -> str:
    """开场字幕卡 (hf_opening): 前 5 秒多行台词贴字兜听觉.

    - style: v1 = 禁忌警告风 (黑底白字+警示红, 顿挫硬切), v2 = Apple 官网审美 (浅灰+深蓝强调, 细腻缓入),
             v3 = 财经片头 (深炭+暖金 chrome-text, 多层时间轴+scatter, 大厂 UI 标准)
    - 模板: hf-opening-v{1|2|3} (竖) / hf-opening-v{1|2}-ls (横, v3 当前仅横屏设计)
    - 时长: 5-8 秒 (前 5 秒核心, 最多 8 秒)
    - 内容: v1/v2=多行台词+强调词; v3=hero_text(主句)+hot_word(金词)+sub_text(副句)+scatter_words(散布词)
    """
    from app.services.visual_render_service import execute_visual_render_job

    spec = get_video_format_spec(slot.director_job.video_format)
    render_config = slot.params_json.get("render_config") or {}
    style = render_config.get("style", "v1") or "v1"
    if style not in ("v1", "v2", "v3"):
        style = "v1"
    is_landscape = spec["width"] > spec["height"]
    # style 已是 "v1/v2/v3" (含 v), 直接拼; 横屏 v1/v2 用 -ls 模板, v3 当前仅横屏设计用基础模板
    template_id = f"hf-opening-{style}-ls" if is_landscape and style != "v3" else f"hf-opening-{style}"
    duration = round(slot.end_sec - slot.start_sec, 3)

    # v3 财经片头: hero/hot/sub/scatter 参数
    if style == "v3":
        input_data = {
            "hero_text": str(render_config.get("hero") or render_config.get("hero_text") or ""),
            "hot_word": str(render_config.get("hot") or render_config.get("hot_word") or ""),
            "sub_text": str(render_config.get("sub") or render_config.get("sub_text") or ""),
            "scatter_words": json.dumps(render_config.get("scatter") or render_config.get("scatter_words") or [], ensure_ascii=False),
            "duration_sec": max(5, min(8, round(duration))),
        }
        # 无显式 hero 时从口播取首句
        if not input_data["hero_text"]:
            input_data["hero_text"] = (slot.text_context or "").split("||")[0][:20]
        # 无 hot 词时从口播检测冲击词
        if not input_data["hot_word"]:
            try:
                from app.services.slot_workflows.hf_extract import _pick_red_words
                words = _pick_red_words(input_data["hero_text"])
                if words:
                    input_data["hot_word"] = words[0]
            except Exception:
                pass
        # 无 scatter 时给默认财经词
        if not input_data["scatter_words"].strip() or input_data["scatter_words"] == "[]":
            input_data["scatter_words"] = json.dumps(["资本", "黑箱", "博弈", "杠杆", "泡沫", "算盘", "命门", "逻辑"], ensure_ascii=False)
        _merge_brand(input_data, slot, db)
        job = VisualRenderJob(template_id=template_id, input_json=input_data, status="queued")
        db.add(job); db.commit(); db.refresh(job)
        result = execute_visual_render_job(db, job.id, template_id, input_data)
        if result.get("status") != "completed":
            raise RuntimeError(result.get("error_message") or "HF render failed")
        out_path = result.get("output_path")
        if not out_path or not Path(out_path).exists():
            raise RuntimeError("HF render output missing")
        return out_path

    # v1/v2: 多行台词逻辑
    accent_key = "opening_red_words" if style == "v1" else "opening_accent_words"

    duration = round(slot.end_sec - slot.start_sec, 3)

    # 多行台词: 优先用 render_config 显式给的, 否则从口播提取
    lines = render_config.get("lines") or render_config.get("opening_lines") or []
    accent_words = render_config.get("red_words") or render_config.get("accent_words") or []
    if not lines:
        # fallback: 从开场口播 (slot.text_context) 语义分行提取
        try:
            from app.services.slot_workflows.hf_extract import build_opening_lines

            built = build_opening_lines(slot.text_context or "")
            lines = built.get("lines", [])
            if not accent_words:
                accent_words = built.get("red_words", [])
        except Exception:
            lines = []

    input_data = {
        "opening_lines_json": json.dumps(lines, ensure_ascii=False),
        accent_key: json.dumps(accent_words, ensure_ascii=False),
        "duration_sec": max(5, min(8, round(duration))),
    }
    # 品牌注入
    _merge_brand(input_data, slot, db)

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


def _execute_hf_quote(db: Session, slot: DirectorSlot) -> str:
    """引用卡 (hf_quote): 一句话观点 + 出处/人物 + 可选人像, 黑金质感.

    - 模板: hf-quote-v1 (横屏 1920x1080)
    - 内容: quote_text(引用语) + hot_word(金词) + attrib_name(人物) + attrib_role(身份) + portrait_b64(人像)
    """
    from app.services.visual_render_service import execute_visual_render_job

    template_id = "hf-quote-v1"
    duration = round(slot.end_sec - slot.start_sec, 3)
    render_config = slot.params_json.get("render_config") or {}

    input_data = {
        "quote_text": str(render_config.get("quote") or render_config.get("quote_text") or ""),
        "hot_word": str(render_config.get("hot") or render_config.get("hot_word") or ""),
        "attrib_name": str(render_config.get("name") or render_config.get("attrib_name") or ""),
        "attrib_role": str(render_config.get("role") or render_config.get("attrib_role") or ""),
        "portrait_b64": str(render_config.get("portrait") or render_config.get("portrait_b64") or ""),
        "duration_sec": max(4, min(10, round(duration))),
    }
    # 无 quote 时从口播取
    if not input_data["quote_text"]:
        input_data["quote_text"] = (slot.text_context or "").replace("||", "")[:80]
    # 无 hot 词时从引用语检测冲击词
    if not input_data["hot_word"]:
        try:
            from app.services.slot_workflows.hf_extract import _pick_red_words
            words = _pick_red_words(input_data["quote_text"])
            if words:
                input_data["hot_word"] = words[0]
        except Exception:
            pass
    _merge_brand(input_data, slot, db)

    job = VisualRenderJob(template_id=template_id, input_json=input_data, status="queued")
    db.add(job); db.commit(); db.refresh(job)
    result = execute_visual_render_job(db, job.id, template_id, input_data)
    if result.get("status") != "completed":
        raise RuntimeError(result.get("error_message") or "HF render failed")
    out_path = result.get("output_path")
    if not out_path or not Path(out_path).exists():
        raise RuntimeError("HF render output missing")
    return out_path
