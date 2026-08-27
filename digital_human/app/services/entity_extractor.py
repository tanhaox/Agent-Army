# -*- coding: utf-8 -*-
"""entity_extractor — 素材实体层 (2026-08-27, 素材层 2.0 第 1 期).

用户诊断: 素材层 40 分的根因 = 源类型错配 + 检索与口播稿脱节 —
特朗普演讲/日本首相 Pexels(图库) 根本没有, 航母有也是道具级;
9 维词表全是风格维度, 无实体维度。

本模块: 口播稿 → 实体清单 (人/事/装备/机构/概念), 按类型路由素材源 —
  person/military/event/org → 油管精准截取 / DVIDS (第 2 期接线)
  concept/place 通用意象    → Pexels (现有, 降兜底位)
实体回库带标签后本地碰撞按实体优先命中 (第 3 期), 素材复利。

用法:
  from app.services.entity_extractor import extract_material_entities
  ents = extract_material_entities(口播全文)   # [{"name","type","queries":{...},"why"}]
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# 实体类型 → 素材源路由 (第 2 期接下载管线, 第 1 期先出需求单)
SOURCE_ROUTES: dict[str, list[str]] = {
    "person": ["youtube", "dvids"],     # 真实人物: 演讲/新闻画面 (军事人物 DVIDS)
    "military": ["dvids", "youtube"],   # 装备: 美军公共领域真实影像
    "event": ["youtube"],               # 事件/新闻现场
    "org": ["youtube"],                 # 公司/机构: 发布会/工厂
    "place": ["youtube", "pexels"],     # 地点: 实拍优先, 通用兜底
    "concept": ["pexels"],              # 抽象概念: 图库主场
}

ENTITY_PROMPT = """你是短视频素材采购员。读下面这篇口播稿，提取所有需要**真实画面**的实体，并给出素材源搜索词。只输出 JSON。

# 实体类型 (route 决定素材源)
- person: 真实人物 (特朗普/马斯克/日本首相…) — 需要真人画面
- military: 军事装备 (航母/F-35/驱逐舰/导弹…) — 需要真实装备影像
- event: 具体事件/新闻 (关税战/芯片禁令/大选/发布会…) — 需要现场画面
- org: 公司/机构 (英伟达/台积克/五角大楼…) — 需要实景/发布会
- place: 具体地点 (台海/硅谷/底特律…) — 实拍优先
- concept: 抽象概念 (算力/供应链/通胀/资本…) — 图库意象即可

# 规则
- 只提口播稿**点名**的实体; 稿里没提的不猜 (宁缺毋滥)
- 每实体给 queries: {"youtube": "英文搜索词(新闻/官方频道口径)", "pexels": "英文图库词(仅concept/place需要)", "dvids": "英文军语(仅military)"}
- 出现多次的同一实体只提一次; 优先提画面权重高的 (主角人物/核心装备/关键事件)
- concept 不超过 3 个 (太多=没重点)

# 输出
{"entities": [{"name": "中文名", "type": "person", "queries": {...}, "why": "口播中的上下文短语(≤20字)"}]}"""


def extract_material_entities(script_text: str) -> list[dict[str, Any]]:
    """口播全文 → 素材实体清单 (flash 单跑, 失败返回 []).

    每项: {name, type, queries{source:搜索词}, why, routes[素材源]}
    """
    text = (script_text or "").strip()
    if not text:
        return []
    try:
        from .boost_service import _call, _extract_json
        raw = _call(ENTITY_PROMPT + "\n\n【口播稿】\n" + text[:8000],
                    json_mode=True, max_tokens=2000, temperature=0.2)
        data = _extract_json(raw)
        items = (data or {}).get("entities") or []
    except Exception as exc:
        logger.warning("[entity] 抽取失败(素材需求单缺省): %s", exc)
        return []

    out: list[dict[str, Any]] = []
    for it in items:
        etype = str(it.get("type") or "").strip()
        if etype not in SOURCE_ROUTES or not it.get("name"):
            continue
        out.append({
            "name": str(it["name"]).strip(),
            "type": etype,
            "queries": {k: v for k, v in (it.get("queries") or {}).items() if v},
            "why": str(it.get("why") or "")[:40],
            "routes": SOURCE_ROUTES[etype],
        })
    return out


def match_slot_entities(slot_text: str, entities: list[dict[str, Any]]) -> list[str]:
    """slot 口播上下文 ↔ 实体名匹配 → 该 slot 关联的实体名 (本地碰撞实体维度用)."""
    if not slot_text or not entities:
        return []
    hit = [e["name"] for e in entities if e["name"] and e["name"] in slot_text]
    # 别名兜底: 名字≥2 字且 slot 里出现
    if not hit:
        hit = [e["name"] for e in entities
               if len(e["name"]) >= 2 and e["name"] in slot_text[:300]]
    return hit


def requirement_sheet(entities: list[dict[str, Any]]) -> str:
    """需求单文本 (人读/落 trace): 哪些实体走哪个源、搜什么."""
    if not entities:
        return "无实体 (纯概念稿, Pexels 兜底即可)"
    lines = []
    for e in entities:
        q = " | ".join(f"{k}:{v}" for k, v in e["queries"].items())
        lines.append(f"  [{e['type']}] {e['name']} → {'/'.join(e['routes'])}  {q}")
    return "\n".join(lines)
