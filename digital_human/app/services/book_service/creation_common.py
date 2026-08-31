# -*- coding: utf-8 -*-
"""拆书创作公共层 — 人设常量 / 灵性金句锚定扫描 / 六段弹性标签 / LLM 工具.

拆包自 orchestrator.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import get_config
from app.models import BookProject
from app.services.book_service.reader import read_book
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

__all__ = ["elastic_labels", "validate_script", "source_context"]

# ── 人设后处理注入层 (P1 定稿措辞): 创作 LLM 保持中性, 身份段/结尾在此加 ──
# 2026-08-23: 自称"静"而非"静姐" — 拉大受众群 (静姐限定了已婚熟龄, 静覆盖更广)
_PERSONA_IDENTITY = "我是静，读透一本好书，陪你遇见更好的自己。"
_PERSONA_ENDING = "照顾好自己，让我们一起成长。我是静，下期见。"

# ── 灵性金句锚定扫描 (2026-08-21): 生成后确定性检查, 未锚定→触发重写 ──
# 本书/灵性主题流传广的金句, 出现必须带"书里/书中/作者"锚定, 防宿命论/向内归罪/伪科学.
_OCCULT_QUOTE_PATTERNS = [
    r"外面没有别人",
    r"凡是你抗拒的",
    r"都是[^。，]{0,14}的礼物",
    r"事件[^。，]{0,8}中性",
    r"内在[^。，]{0,8}(镜子|投射)",
    r"内在投射",
    r"爱[^。，]{0,4}喜悦[^。，]{0,4}和平",
    r"心想事成",
    r"境由心转",  # 唯心/心转断言, 须锚定书里比喻
    r"二十一天",  # 21天固定周期, 须锚定书里建议/弱化确定性
]
_ANCHOR_RE = re.compile(r"(书里|书中|作者|按照书|这本书|书里讲|书里说|书里提到|书中提出|书中记录|书中的看法)")


def _scan_occult_quotes(out: str) -> list[str]:
    """扫描未锚定书中观点的灵性金句, 返回问题清单 (每句一条).

    判定: 金句所在句(上一个句末标点到金句结束)内必须出现锚定词(书里/书中/作者/按照书等);
    跨句的'这本书'泛介绍不算锚定.
    """
    issues: list[str] = []
    for pat in _OCCULT_QUOTE_PATTERNS:
        for m in re.finditer(pat, out):
            parts = re.split(r"[。！？!?；;\n]", out[: m.end()])
            sentence = parts[-1] if parts else ""
            if not _ANCHOR_RE.search(sentence):
                issues.append(
                    f"「{m.group(0)}」需锚定书中观点——前句带'书里有一句比喻/书中提出/按照书里的看法'主语，禁作客观真理")
    return issues

# 兜底基底 (2026-08-20): config/jingshu-book.txt 缺失/过短时回退, 防管线静默崩坏.
# 精简版人设 + 六段结构说明; 附加指令/Gate B 仍由 generate_episode 动态追加.
_FALLBACK_BASE = (
    "你是\"静读书\"的拆书讲述者静，45岁+，已有上小学的儿子。满级情商、温柔、知性、"
    "通过分享达到精神成长。说话不端着、不卖弄、不居高临下，拒绝煽情和鸡汤腔。\n"
    "【核心任务】基于【本集输入】（书名/本集路线图/全书输入/读者反应/素材包/前序覆盖），"
    "按六段结构写一集口播稿：把这本书拆透、讲人话。\n"
    "【受众画像】抖音、小红书：25-50岁女性，希望通过阅读、听书获得成长。喜欢知识沉淀，"
    "又没有太多时间进行仔细阅读；爱听\"这本书说的，对我有什么用\"，打比方用职场/育儿/"
    "关系/深夜独处等生活场景。\n"
    "【口吻红线】普遍规律用\"咱们\"、个人建议才用\"你\"；转场极简；禁元叙述/计数预告句；"
    "比喻须与论证严格对应；温柔但不绵软——软声说硬话，观点清晰有立场。\n"
    "【拆书约束】同一引导词全篇最多1次；每句≤20字；强比喻≤3个；"
    "书中内容≤40%、场景/解读≥60%；观点须可追溯来源，书中观点一律\"书中提出/作者认为\"视角限定；"
    "金句转述不挂引号。\n"
    "【六段结构】钩子 → 回顾+引入 → 核心概念拆解（一）→（二）→（三）→ 总结+下期预告，"
    "每段以附加指令给的【A-B秒｜段名】标签行开头，逐字保留。\n"
    "【输出】纯口播文本，末尾另起一段附严格 JSON 块 {\"coverage\":[str]} 列本集知识点，"
    "该块之后禁止再输出任何文字。"
)

# 防幻觉核心四字段: 仅 L0 提取或人工输入可入总纲
_CORE_FIELDS = ("全书核心主张", "关键概念清单", "核心金句", "核心案例")

# 弹性标签六段基准 (270s), 按目标时长等比缩放
_LABEL_BASE = [
    (0, 10, "钩子"),
    (10, 40, "回顾+引入"),
    (40, 100, "核心概念拆解（一）"),
    (100, 170, "核心概念拆解（二）"),
    (170, 220, "核心概念拆解（三）"),
    (220, 270, "总结+下期预告"),
]
_LABEL_RE = re.compile(r"【(\d+)-(\d+)秒｜([^】]+)】")


def _llm() -> LLMService:
    return LLMService(get_config().deepseek)


def _parse_json(text: str) -> Any:
    """LLM 输出取 JSON: 去 markdown 围栏后解析."""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?", "", t)
    t = re.sub(r"```$", "", t).strip()
    m = re.search(r"[\[{]", t)
    if m and not t.startswith(("{", "[")):
        t = t[m.start():]
    return json.loads(t)


def _first_list(data: Any) -> list:
    """LLM 常把数组包进 dict — 取第一个非空 dict 列表值."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def elastic_labels(target: float) -> list[tuple[int, int, str]]:
    """六段结构按目标时长等比缩放 (默认 600s)."""
    k = target / 270.0
    return [(round(a * k), round(b * k), name) for a, b, name in _LABEL_BASE]


def validate_script(text: str, target: float) -> tuple[bool, list[str]]:
    """硬校验: 字数 2700-3000 + 六标签完整 + 末段终点≈目标±10%."""
    issues: list[str] = []
    body = _LABEL_RE.sub("", text or "")
    n = len(re.sub(r"\s", "", body))
    if not 2700 <= n <= 3000:
        issues.append(f"字数 {n} {'超出 3000' if n > 3000 else '不足 2700'}")
    labels = _LABEL_RE.findall(text or "")
    names = [x[2].strip() for x in labels]
    for _a, _b, name in _LABEL_BASE:
        if name not in names:
            issues.append(f"缺标签【{name}】")
    if labels:
        end = max(int(b) for _a, b, _n in labels)
        if abs(end - target) > target * 0.1:
            issues.append(f"末段终点 {end}s 偏离目标 {target:.0f}s ±10%")
    return (not issues, issues)


def source_context(book: BookProject, cap: int = 12000) -> str:
    """L0 来源上下文: 精华/原书章节摘要 (cap 内), 无来源返回空串."""
    if not book.source_path:
        return ""
    try:
        parsed = read_book(book.source_path)
    except Exception as exc:
        logger.warning("[book] L0 读取失败 %s: %s", book.source_path, exc)
        return ""
    parts, used = [], 0
    for ch in parsed["chapters"]:
        if used >= cap:
            break
        take = ch["text"][: max(500, cap - used)]
        parts.append(f"【{ch['name']}】{take}")
        used += len(take)
    return "\n".join(parts)
