# -*- coding: utf-8 -*-
"""全系统统一禁用词/限流词服务 (2026-08-22) — 拆书/新闻线/未来衍生系统共用.

唯一事实源: config/compliance_common.json (categories: 绝对化/医疗/迷信/金融/引流/承诺).
入口:
- load_common_rules()       读词库
- build_redline_prompt()    组装成生成提示词注入块 (源头规避, LLM 生成时就避开)
- check_text(text)          检测文本命中违禁词 (生成后检查兜底)

用法示例:
- 拆书: orchestrator.GateB / facing-units prompt 注入 build_redline_prompt()
- 新闻线: articles.rewrite 加载模板后注入
- 未来系统: 直接 import compliance 服务, 禁止词功能自动赋能
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_COMMON_PATH = Path(__file__).resolve().parents[2] / "config" / "compliance_common.json"
_VISUAL_PATH = Path(__file__).resolve().parents[2] / "config" / "compliance_visual.json"

_cache: dict | None = None
_visual_cache: list[str] | None = None
_subs_cache: dict[str, str] | None = None


def load_common_rules() -> dict:
    """读 config/compliance_common.json (带缓存)."""
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_COMMON_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("[compliance] 公共限流词库加载失败: %s", exc)
            _cache = {"categories": {}}
    return _cache


def _all_banned(categories: list[str] | None = None) -> list[str]:
    """聚合指定类别(默认全部)的禁用词."""
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    out: list[str] = []
    for k in keys:
        ban = (rules.get(k) or {}).get("ban") or []
        out.extend(str(w) for w in ban)
    return list(dict.fromkeys(out))  # 去重保序


def _all_replaces(categories: list[str] | None = None) -> dict[str, str]:
    """类别 → 替换建议."""
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    return {k: (rules.get(k) or {}).get("replace", "") for k in keys}


def build_redline_prompt(categories: list[str] | None = None) -> str:
    """组装成生成提示词注入块 — LLM 生成时就规避 (源头).

    返回多行文本, 可直接拼到任何生成 prompt (拆书 facing/逐集、新闻线洗稿).
    """
    rules = load_common_rules().get("categories") or {}
    keys = categories or list(rules.keys())
    lines = ["【平台禁用词 · 全系统红线 · 生成时必规避, 出现即违规】"]
    for k in keys:
        cat = rules.get(k) or {}
        ban = "、".join(str(w) for w in (cat.get("ban") or [])[:12])
        repl = cat.get("replace", "")
        lines.append(f"- 禁{cat.get('label', k)}: {ban}（→ {repl}）")
    lines.append("- 全篇用'个人感受+参考建议'的温和表达, 禁绝对化/医疗承诺/迷信/金融收益/站外引流。")
    return "\n".join(lines)


def check_text(text: str, categories: list[str] | None = None) -> list[str]:
    """检测文本命中违禁词 (生成后检查兜底). 返回命中词列表."""
    if not text:
        return []
    banned = _all_banned(categories)
    hits = [w for w in banned if w and w in text]
    return hits


def build_check_prompt(categories: list[str] | None = None) -> str:
    """组装成审计/检测 prompt — 供 LLM 或代码检查生成内容."""
    return build_redline_prompt(categories)


def visual_banned() -> list[str]:
    """画面禁区词库 (config/compliance_visual.json, 带缓存).

    0917 动画线用户令: 任何画面禁出现中国地图/国旗/国徽/国家领导人画像 —
    卡通/剪影/变形也不行。宪法提示/软警告/生成闸门/K2 防尾共用此单一事实源。
    """
    global _visual_cache
    if _visual_cache is None:
        try:
            data = json.loads(_VISUAL_PATH.read_text(encoding="utf-8"))
            _visual_cache = [str(w) for cat in (data.get("categories") or {}).values()
                             for w in (cat.get("ban") or []) if w]
        except Exception as exc:  # noqa: BLE001 — 词库坏不炸管线, 空表=只靠提示层
            logger.warning("[compliance] 画面禁区词库加载失败: %s", exc)
            _visual_cache = []
    return _visual_cache


def visual_substitutes() -> dict[str, str]:
    """国家指代表 (config/compliance_visual.json substitutes, 带缓存).

    0917 用户令: 表现国家概念禁旗徽地图, 用央视同款指代物 (美国=白头鹰/中东=骆驼)。
    表是宪法提示的拼装源 — 改表即 DIRECTOR_SYS 同步 (director2 模块加载时拼入)。
    """
    global _subs_cache
    if _subs_cache is None:
        try:
            data = json.loads(_VISUAL_PATH.read_text(encoding="utf-8"))
            raw = data.get("substitutes") or {}
            _subs_cache = {str(k): str(v) for k, v in raw.items() if not str(k).startswith("_")}
        except Exception as exc:  # noqa: BLE001
            logger.warning("[compliance] 国家指代表加载失败: %s", exc)
            _subs_cache = {}
    return _subs_cache


def check_visual(text: str) -> list[str]:
    """画面禁区检测: keyframe/motion/文字层等画面描述文本的命中词列表."""
    if not text:
        return []
    return [w for w in visual_banned() if w in text]


def visual_constitution_prompt() -> str:
    """画面宪法拼装块 (0923 用户令"宪法进每个角落"): 所有视觉生成 LLM 入口统一注入.

    源头规避 — 圣经角色卡/试镜镜/风格提案/重调/分镜规划产 prompt 时就带着禁区与指代物,
    下游 VLM/OCR 守门只是兜底。改 compliance_visual.json 即此处同步。"""
    bans = visual_banned()
    subs = visual_substitutes()
    if not bans:
        return ""
    lines = ["【画面宪法 · 硬性禁区 (生成任何画面描述/角色look/道具时必须规避, 违者抖音不给流量)】"]
    for cat_name, cat in ((_VISUAL_PATH and json.loads(_VISUAL_PATH.read_text(encoding="utf-8")).get("categories") or {}).items() if _VISUAL_PATH.exists() else []):
        note = (cat.get("note") or "")[:60]
        ban = "、".join((cat.get("ban") or [])[:12])
        if ban:
            lines.append(f"- {cat_name}: 禁 {ban}" + (f" ({note})" if note else ""))
    if subs:
        rows = "；".join(f"{k}＝{v}" for k, v in subs.items() if not str(k).startswith("_"))
        lines.append(f"- 国家/民族概念指代物 (禁旗徽地图, 用指代物): {rows}")
    return "\n".join(lines) + "\n"
