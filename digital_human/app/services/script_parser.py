"""Parse broadcast script into sentence-level segments.

``||`` is a TTS pause hint, NOT a segment boundary. Segments are split by
sentence delimiters (。！？；) so that each segment is a complete utterance.
"""
from __future__ import annotations

import re
from typing import Any, Literal

SegmentType = Literal["opening", "hook", "body", "cta", "ending"]

_SENTENCE_DELIMS = "。！？；"


def _detect_segment_type(
    text: str,
    index: int,
    total: int,
    fixed_opening: str | None = None,
    fixed_ending: str | None = None,
) -> SegmentType:
    """Heuristic classification for segment type."""
    if fixed_opening and text.startswith(fixed_opening[:8]):
        return "opening"
    if fixed_ending and text.startswith(fixed_ending[:8]):
        return "ending"
    if index == 0:
        return "opening" if "大家好" in text or "我是" in text else "hook"
    if index == total - 1:
        return "ending" if any(w in text for w in ("关注", "点赞", "收藏", "再见", "下期")) else "cta"
    if any(w in text for w in ("关注我", "点赞", "收藏", "转发", "评论区", "下期见")):
        return "cta"
    return "body"


def _clean_text(text: str) -> str:
    """Normalize control characters.

    - Removes redundant comma + pause marker combinations such as ",||" or
      "，||" and leaves only the comma.
    - Collapses consecutive whitespace.
    """
    text = re.sub(r"[,，]\s*\|\|", "，", text)
    text = re.sub(r"\|\|\s*[,，]", "，", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    """Split text into complete sentences, preserving trailing delimiters.

    ``||`` is treated as a pause hint inside a sentence, never as a boundary.
    """
    text = _clean_text(text)
    if not text:
        return []

    sentences: list[str] = []
    current = ""
    for ch in text:
        current += ch
        if ch in _SENTENCE_DELIMS:
            stripped = current.strip()
            if stripped:
                sentences.append(stripped)
            current = ""
    if current.strip():
        # Fragment without terminal punctuation: append to previous sentence or
        # stand alone if it is the only content.
        fragment = current.strip()
        if sentences:
            sentences[-1] = (sentences[-1] + fragment).strip()
        else:
            sentences.append(fragment)
    return sentences


def _parse_control_chars(text: str) -> dict[str, Any]:
    """Extract TTS control characters from segment text."""
    return {
        "pauses": text.count("||"),
        "periods": text.count("。"),
        "exclamations": text.count("！"),
        "questions": text.count("？"),
    }


def parse_script(
    script_text: str,
    fixed_opening: str | None = None,
    fixed_ending: str | None = None,
) -> list[dict[str, Any]]:
    """Split script into segments, one per complete sentence.

    Sentence delimiters (。！？；) define segment boundaries. ``||`` is kept
    inside the segment as a pause hint for the TTS/post-processing stage.
    """
    lines = [line.strip() for line in script_text.splitlines() if line.strip()]

    sentences: list[str] = []
    for line in lines:
        sentences.extend(_split_sentences(line))

    # Remove exact duplicates that sometimes appear when the model repeats the
    # fixed opening/ending on their own line and also inline.
    seen: set[str] = set()
    unique_sentences: list[str] = []
    for s in sentences:
        if s in seen:
            continue
        seen.add(s)
        unique_sentences.append(s)

    segments = []
    total = len(unique_sentences)
    for idx, text in enumerate(unique_sentences):
        seg_type = _detect_segment_type(text, idx, total, fixed_opening, fixed_ending)
        segments.append(
            {
                "line_index": idx,
                "text": text,
                "control_chars": _parse_control_chars(text),
                "segment_type": seg_type,
                "selected_for_host": True,
                "host_order": idx,
            }
        )
    return segments
