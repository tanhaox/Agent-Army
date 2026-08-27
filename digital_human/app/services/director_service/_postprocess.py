"""Director Agent 2.0 — 规划后处理 (clamp / references 卡 / 落库).

slot 时长钳制、references 来源卡追加、plan 落库 + slots 持久化。
"""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.models import DirectorJob, DirectorSlot
from app.services.director_service._trace import append_trace

logger = logging.getLogger(__name__)

__all__ = ["_clamp_slot_durations", "_append_source_slot", "_persist_plan"]

# 片尾来源声明卡时长 (2026-08-17 用户口径: 5 秒无语音免责声明)
_SOURCE_CARD_DURATION = 5.0


# 质量钳制参数 (2026-08-15): 实测 53 slots/5min、broll 0.9s 闪切、21 张 hf_title → 硬兜底
_MIN_DUR = {
    "broll_pexels": 2.5,
    "broll_local": 2.5,
    "hf_title": 3.0,
    "hf_chart": 3.0,
    "hf_quote": 3.0,
}
_HF_TITLE_CAP = 5  # 含尾部参考卡(clamp 后追加, 不占此额度)
_PROTECTED = {"host", "mixed_host_broll", "hf_opening"}


def _clamp_slot_durations(plan: Any, total_duration: float) -> None:
    """质量钳制: 重叠去重 + 最小时长 + hf_title 数量上限 + 时序重排.

    LLM 规划实测三种劣化 (2026-08-15): broll 碎片闪切 (0.9~1.8s)、
    hf_title 滥用 (单片 21 张)、同秒重叠 slot。此处为不可协商的硬底线。
    """
    slots = sorted(plan.slots, key=lambda s: (s.start_sec, s.slot_index))
    kept: list[Any] = []
    hf_title_seen = 0
    cursor = 0.0
    dropped = 0
    for slot in slots:
        dur = slot.end_sec - slot.start_sec
        if dur <= 0.05:
            dropped += 1
            continue  # 空 slot
        # hf_title 数量上限: 超限丢弃 (尾部参考卡在 clamp 之后追加, 不受影响)
        if slot.workflow == "hf_title":
            hf_title_seen += 1
            if hf_title_seen > _HF_TITLE_CAP:
                logger.info("[director] drop excess hf_title (cap %d)", _HF_TITLE_CAP)
                dropped += 1
                continue
        min_dur = _MIN_DUR.get(slot.workflow, 0.0)
        if dur < min_dur:
            if slot.workflow in _PROTECTED or slot.workflow.startswith("hf"):
                dur = min_dur  # hf 卡/出镜拉长到下限
            elif kept and kept[-1].workflow == slot.workflow:
                # broll 碎片并入前一相邻同类型 slot (顺延其 end)
                kept[-1].end_sec = round(kept[-1].end_sec + dur, 3)
                kept[-1].duration_sec = round(kept[-1].end_sec - kept[-1].start_sec, 3)
                cursor = kept[-1].end_sec
                continue
            else:
                dur = min_dur
        # 重叠去重: 起点 = max(原起点, 上一 slot 结束)
        start = max(slot.start_sec, cursor)
        end = start + dur
        if total_duration:
            end = min(end, total_duration)
        slot.start_sec = round(start, 3)
        slot.end_sec = round(end, 3)
        slot.duration_sec = round(slot.end_sec - slot.start_sec, 3)
        if slot.duration_sec <= 0.05 and slot.workflow not in _PROTECTED:
            dropped += 1
            continue
        cursor = slot.end_sec
        kept.append(slot)
    for i, slot in enumerate(kept):
        slot.slot_index = i
    # 时间轴满铺 (2026-08-15): LLM 规划偶发漏铺中段 (实测 323s 音频在 223s 处
    # 有 8.7s 空洞 → 成片音轨错位+截断, 观众听感"整段消失/念一半没了")。
    # 任何 >0.5s 的 slot 间隙, 一律用前一个 slot 延伸填满; 片尾同理。
    filled = 0
    for cur, nxt in zip(kept, kept[1:]):
        gap = nxt.start_sec - cur.end_sec
        if gap > 0.5:
            cur.end_sec = round(nxt.start_sec, 3)
            cur.duration_sec = round(cur.end_sec - cur.start_sec, 3)
            filled += 1
    if kept and total_duration and kept[-1].end_sec < total_duration - 0.5:
        gap = total_duration - kept[-1].end_sec
        kept[-1].end_sec = round(total_duration, 3)
        kept[-1].duration_sec = round(kept[-1].end_sec - kept[-1].start_sec, 3)
        filled += 1
        logger.info("[director] tail coverage: extended last slot by %.1fs to audio end (%.1fs)",
                    gap, total_duration)
    if filled:
        logger.info("[director] timeline tiling: filled %d gap(s), slots now tile audio fully", filled)
    plan.slots = kept
    if dropped:
        logger.info("[director] quality clamp: kept %d slots, dropped %d (碎片/超限/重叠)",
                    len(kept), dropped)


def _domain_of(url: str) -> str:
    """URL → 可读媒体名 (netloc 去 www./m./wap. 前缀). 失败返回空串."""
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:
        return ""
    for prefix in ("www.", "m.", "wap."):
        if host.startswith(prefix):
            return host[len(prefix):]
    return host


def _clean_source_title(title: str) -> str:
    """清洗来源标题: 截掉智谱搜索的"（发布时间：…"尾巴, 去空白, 限 40 字."""
    t = (title or "").strip()
    for marker in ("（发布时间", "(发布时间", "发布时间"):
        i = t.find(marker)
        if i > 0:
            t = t[:i]
            break
    return t.strip()[:40]


def _collect_news_sources(db: Session, script: Any) -> list[dict[str, str]]:
    """聚合真实来源: 素材包(真 http URL → 域名作媒体名 + 清洗后标题) + 主稿 article.

    来源数据在 material_items (洗稿时喂 LLM 参考), 产出稿不保留来源列表 →
    尾卡从这里取 (2026-08-17 修复: 原机制依赖脚本 references 段, 全库从未出现).
    URL 去重, 上限 5 条.
    """
    from app.models import MaterialPackage

    srcs: list[dict[str, str]] = []
    seen: set[str] = set()

    if script.material_package_id:
        pkg = db.get(MaterialPackage, script.material_package_id)
        if pkg:
            for it in pkg.items:
                url = (it.source_url or "").strip()
                if not url.lower().startswith("http") or url in seen:
                    continue
                seen.add(url)
                media = _domain_of(url)  # media 字段历史上有日期脏值, 域名更可靠
                srcs.append({"media": media or "网络", "title": _clean_source_title(it.title)})
                if len(srcs) >= 5:
                    break

    if len(srcs) < 5 and script.article and script.article.source_url:
        url = (script.article.source_url or "").strip()
        if url.lower().startswith("http") and url not in seen:
            seen.add(url)
            srcs.append({"media": _domain_of(url) or "新闻源",
                         "title": _clean_source_title(script.article.title)})
    return srcs


def _append_source_slot(db: Session, plan: Any, script: Any, total_duration: float) -> None:
    """片尾来源声明卡 (来源驱动, 无语音) — 修复 2026-08-17.

    原 _append_references_slot 依赖洗稿文本含"参考来源"段 (script_parser 据此建
    references 段), 但 7 层洗稿 prompt 输出纯口播稿从不含该段 → 全库 references
    段=0, 尾卡从未触发. 改为从 material_package + article 聚合真实来源, 有来源
    即恒定追加 5s hf_title 卡 (媒体名·短标题, no_voiceover).
    """
    from app.schemas import DirectorSlotPlan

    sources = _collect_news_sources(db, script)
    if not sources:
        # 回退: 洗稿文本的 references 段 (历史数据兜底)
        ref_segments = [seg for seg in script.segments if seg.segment_type == "references"]
        ref_text = "\n".join(seg.text for seg in ref_segments[:6])[:200].strip()
        if ref_text:
            sources = [{"media": "参考来源", "title": ref_text}]
    if not sources:
        sources = [{"media": "公开报道", "title": "内容综合自公开报道，仅供参考"}]

    subtitle = "  ·  ".join(
        f"{s['media']}·{s['title']}" if s["title"] else s["media"] for s in sources
    )[:200]

    ref_slot = DirectorSlotPlan(
        slot_index=len(plan.slots),
        start_sec=round(total_duration, 3),
        end_sec=round(total_duration + _SOURCE_CARD_DURATION, 3),
        duration_sec=_SOURCE_CARD_DURATION,
        text_context=subtitle,
        segment_id=None,
        visual_type="hf_title",
        workflow="hf_title",
        params={
            "render_config": {
                "title": "内容来源声明",
                "subtitle": subtitle,
                "style": "references",
                # 结构化来源列表 (hf-source-v1 专用; 长 subtitle 走 hf-title-v2
                # 的 kicker 会炸 32 字校验 → 2026-08-18 产线降级黑屏事故)
                "sources": sources,
            },
            "intensity": "low",
            "emotion": "closing",
            "no_voiceover": True,
        },
    )
    plan.slots.append(ref_slot)
    logger.info("[director] appended source-declaration hf_title slot (%.0fs): %s",
                _SOURCE_CARD_DURATION, subtitle[:60])


def _persist_plan(
    db: Session,
    job: DirectorJob,
    plan: Any,
    script_title: str | None,
) -> None:
    """plan 落库 (保留既有 trace) + slots 持久化."""
    # 保留既有 trace (alignment/plan_llm 已写入), 再覆盖 plan 主体, 避免 trace 被 model_dump 清空
    prev_trace = list((job.plan_json or {}).get("trace", []) or [])
    job.plan_json = plan.model_dump()
    if prev_trace:
        job.plan_json["trace"] = prev_trace
    job.title = plan.title or script_title
    job.status = "reviewing"
    append_trace(db, job, "plan", "done", f"规划完成, {len(plan.slots)} slots 进入 reviewing")
    db.commit()

    # Persist slots
    for slot_plan in plan.slots:
        slot = DirectorSlot(
            director_job_id=job.id,
            slot_index=slot_plan.slot_index,
            start_sec=slot_plan.start_sec,
            end_sec=slot_plan.end_sec,
            duration_sec=slot_plan.duration_sec,
            text_context=slot_plan.text_context,
            segment_id=slot_plan.segment_id,
            visual_type=slot_plan.visual_type,
            workflow=slot_plan.workflow,
            params_json=slot_plan.params,
            camera_angle=slot_plan.camera_angle,
            view_group_index=job.view_group_index or 0,
            status="queued",
        )
        db.add(slot)
    db.commit()
    db.refresh(job)

    # ── 镜头契约层 (2026-08-27, J3 前置): 独立 flash 二段跑, 不碰规划提示词 ──
    # 契约+J2 effect_recipe 存 params_json; 增强层失败静默, 不阻塞 reviewing。
    try:
        from ..shot_contract import generate_shot_contracts
        stats = generate_shot_contracts(db, job.id)
        append_trace(db, job, "shot_contract", "done",
                     f"镜头契约 {stats.get('contracts', 0)} 条 / 配方 {stats.get('recipes', 0)} 个"
                     + (f" (失败: {stats['failed']})" if stats.get("failed") else ""))
    except Exception as exc:  # noqa: BLE001 — 增强层任何失败不挡主流程
        append_trace(db, job, "shot_contract", "failed", str(exc)[:120])

    # ── 素材实体层 (2026-08-27, 素材层 2.0 第 1 期): 口播稿 → 实体需求单 ──
    # 特朗普演讲/航母这类真实画面 Pexels 图库根本没有 — 实体按类型路由
    # (person/military/event→油管/DVIDS 第2期接线, concept→Pexels 兜底)。
    # 实体入 plan_json + slot params.entities (本地碰撞实体维度, 第3期)。
    try:
        from ..entity_extractor import (ENTITY_LAYER_ENABLED, extract_material_entities,
                                        match_slot_entities, requirement_sheet)
        if not ENTITY_LAYER_ENABLED:
            raise RuntimeError("实体层实验中(ENTITY_LAYER_ENABLED=False), 跳过")
        script = getattr(job, "script", None)
        full_text = ((getattr(script, "boosted_text", None) or "")
                     or (getattr(script, "script_text", None) or "")) if script else ""
        entities = extract_material_entities(full_text)
        if entities:
            pj = dict(job.plan_json or {})
            pj["material_entities"] = entities
            job.plan_json = pj
            for s in job.slots:
                hits = match_slot_entities(s.text_context or "", entities)
                if hits:
                    params = dict(s.params_json or {})
                    params["entities"] = hits
                    s.params_json = params
            db.commit()
        append_trace(db, job, "material_entities", "done",
                     f"素材实体 {len(entities)} 个\n{requirement_sheet(entities)}")
    except Exception as exc:  # noqa: BLE001 — 增强层失败不挡主流程
        append_trace(db, job, "material_entities", "failed", str(exc)[:120])
