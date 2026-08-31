# -*- coding: utf-8 -*-
"""P5 情绪标注 — span 协议句编号区间标注 + 解析归一.

拆包自 boost_service.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

import logging
from typing import Any

from app.services.boost_service.llm import _call, _extract_json
from app.services.boost_service.prompts import P5_SPAN_PROMPT

logger = logging.getLogger(__name__)

__all__ = ["_parse_emotion_annotations", "annotate_emotions"]


def _parse_emotion_annotations(text: str) -> list[dict[str, Any]] | None:
    """Parse P5 output: [emotion/strength] text -> [{"emotion":..., "strength":..., "text":...}]

    emotion 归一为 EMOTIONS 英文 key (2026-08-25): P5 常输出中文情绪名 (惊讶/严肃),
    下游 resolve_emotion 只认英文 key — 此前中文全部 KeyError 被静默丢弃, 整篇恒 calm。
    """
    import re

    from app.services.emotion_dict import normalize_emotion_key
    segs = []
    pattern = re.compile(r"^\[(\w+)/(\d+)\]\s*(.*)")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            segs.append({
                "emotion": normalize_emotion_key(m.group(1)),
                "strength": int(m.group(2)),
                "text": m.group(3).strip(),
            })
    return segs if segs else None


def annotate_emotions(text: str, persona_name: str = "老谭", track: str | None = None) -> str | None:
    """生成音频时刻的 P5 情绪标注 (2026-08-25 拆离 boost, 移入 _do_tts).

    v2 协议 (2026-08-25): **句编号+区间标签** — 代码用与 TTS 完全相同的分行逻辑编号,
    LLM 只输出 {"spans": [[起,止,情绪,强度],...]} (几百 token, 零复写原文), 代码拼装
    "[情绪/强度] 段落文字" 兼容下游 (_parse / _map_lines_to_segments / 存储)。
    旧协议 (LLM 复写全文 3000+ 字) 触发大输出空响应, 需 thinking 压制约 48s;
    新协议 flash 直跑 ~10-15s, 且段文本与 TTS 行天然逐行对齐 (零漂移)。
    track: 2026-08-27 起不再分赛道 — 全程惊讶打底 (实测 serious 打底在 IndexTTS2
    上听着平/困, 且 LLM 把带数据的科技稿也误判成"严肃分析")。失败返回 None
    (调用方落整篇 surprised 兜底)。
    """
    try:
        from scripts.tts_lib.lines import _split_line_indices
        lines = _split_line_indices(text)
        if not lines:
            return None
        numbered = "\n".join(f"[{i}] {ln}" for i, ln in enumerate(lines, start=1))

        prompt = P5_SPAN_PROMPT.replace('{persona}', persona_name)
        # (2026-08-27 撤 geo serious 赛道提示: 全赛道统一惊讶打底, 起伏靠强度档。)
        prompt += f"\n\n【编号句子表（共 {len(lines)} 句）】\n" + numbered
        raw = _call(prompt, json_mode=True, max_tokens=1200)
        data = _extract_json(raw)
        if not isinstance(data, dict):
            logger.warning("[p5] span parse failed: %s", str(raw)[:80])
            return None

        # 逐句情绪填充: span 区间覆盖, 漏句继承前句情绪 (初始兜底 surprised/2)
        emo_of: list[tuple[str, int]] = [("surprised", 2)] * len(lines)
        spans = data.get("spans") or []
        for sp in spans:
            try:
                a, b, emo, strength = int(sp[0]) - 1, int(sp[1]), str(sp[2]), int(sp[3])
            except (TypeError, ValueError, IndexError):
                continue
            a, b = max(0, min(a, len(lines) - 1)), max(1, min(b, len(lines)))
            for i in range(a, b):
                emo_of[i] = (emo, strength)
        # 连续同情绪合并 → "[情绪/强度] 段文本" (TTS 行原样拼接, 与合成行天然对齐)
        blocks: list[str] = []
        cur_emo, cur_strength, cur_lines = None, 0, []
        for ln, (emo, strength) in zip(lines, emo_of):
            if emo != cur_emo:
                if cur_lines:
                    blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
                cur_emo, cur_strength, cur_lines = emo, strength, [ln]
            else:
                # 同情绪但强度档变化 → 仍分段 (强度是情绪坡度的一部分)
                if strength != cur_strength:
                    blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
                    cur_strength, cur_lines = strength, [ln]
                else:
                    cur_lines.append(ln)
        if cur_lines:
            blocks.append(f"[{cur_emo}/{cur_strength}] " + "\n".join(cur_lines))
        return "\n".join(blocks) if blocks else None
    except Exception as exc:
        logger.warning("[boost] annotate_emotions failed: %s", exc)
        return None
