"""TTS 文本处理工具: 分段 / 净化 / 批量分组.

不依赖任何引擎后端, 是纯字符串逻辑 — 与 requests / sqlalchemy 等
域外依赖零耦合, 方便单测与复用。
"""
from __future__ import annotations

import re

__all__ = [
    "_sanitize_for_fish",
    "_tts_text",
    "_split_text",
    "_merge_lines_for_batch",
]


def _sanitize_for_fish(text: str) -> str:
    """Work around Fish Speech s2-pro bug: ASCII + space + Chinese triggers 500.

    Fish Speech fails on strings like "GPT-5 真的要来了" (ASCII, space, CJK).
    Removing the space between ASCII alphanumerics and CJK characters avoids the
    crash without changing pronunciation materially.
    """
    # Remove spaces between ASCII alphanumerics/punctuation and CJK.
    # Run repeatedly until no more changes because patterns can overlap.
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"([a-zA-Z0-9\-._%/+])(\s+)([一-鿿])", r"\1\3", text)
        text = re.sub(r"([一-鿿])(\s+)([a-zA-Z0-9\-._%/+])", r"\1\3", text)
    # Collapse multiple spaces to one.
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _tts_text(text: str) -> str:
    """Prepare text for TTS inference.

    ``||`` is a pipeline pause hint, not a real phoneme. Fish Speech will not
    interpret it as silence; replace it with a comma. Emotion tags such as
    ``[calm]`` and paralinguistic markers such as ``(break)`` are stripped
    because many Fish Speech builds crash when CJK immediately follows an
    ASCII tag. The original line (with tags) is preserved in the manifest.
    """
    # Strip emotion / paralinguistic control tags.
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\([^)]+\)", "", text)
    # Pipeline pause hint -> comma.
    text = text.replace("||", "，")
    text = re.sub(r"[,，]{2,}", "，", text)
    text = re.sub(r"[,，]\s*([。！？])", r"\1", text)
    # Batch-join artifact: "句。||下一句" -> "句。，下一句" — drop the comma after
    # terminal punctuation, otherwise TTS renders an audible artifact (残音).
    text = re.sub(r"([。！？；])\s*[,，]+", r"\1", text)
    # Leading comma (line started with '||') has nothing to pause after.
    text = re.sub(r"^[,，]+", "", text)
    return text.strip()


def _split_text(
    text: str,
    segment_delimiter: str = "||",
    max_chars: int = 120,
    sentence_delimiters: str = "。；？！\n",
) -> list[str]:
    """Split text into synthesis segments.

    Priority:
      1. Explicit segment_delimiter (e.g. '||' from scripts) produces exact segments.
      2. Falls back to sentence-level splitting by sentence_delimiters.
      3. Hard-truncates any segment exceeding max_chars.
    """
    text = text.strip()
    if not text:
        return []

    if segment_delimiter in text:
        raw_segments = _split_by_delimiter(text, segment_delimiter)
    else:
        raw_segments = _split_by_sentence(text, sentence_delimiters)

    segments: list[str] = []
    for s in raw_segments:
        s = _sanitize_for_fish(s)
        if len(s) <= max_chars:
            if s:
                segments.append(s)
        else:
            segments.extend(_truncate_overlong(s, max_chars))
    return segments


def _split_by_delimiter(text: str, segment_delimiter: str) -> list[str]:
    """Split on an explicit delimiter (e.g. '||'), dropping empty pieces."""
    return [s.strip() for s in text.split(segment_delimiter) if s.strip()]


def _split_by_sentence(text: str, sentence_delimiters: str) -> list[str]:
    """Split on sentence-ending punctuation, keeping non-empty sentences."""
    raw: list[str] = []
    current = ""
    for ch in text:
        current += ch
        if ch in sentence_delimiters and current.strip():
            raw.append(current.strip())
            current = ""
    if current.strip():
        raw.append(current.strip())
    return raw


def _truncate_overlong(segment: str, max_chars: int) -> list[str]:
    """Hard-truncate an over-long segment into max_chars-sized chunks."""
    chunks: list[str] = []
    for i in range(0, len(segment), max_chars):
        chunk = segment[i : i + max_chars].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _merge_lines_for_batch(lines: list[str], max_chars: int = 300) -> list[list[int]]:
    """Group line indices into batches where each batch total ≤ max_chars.

    Lines are grouped purely by character count. Each group is synthesized as
    a single TTS call, then split back into individual segments by silence detection.

    Args:
        lines: List of text lines (one per segment).
        max_chars: Soft cap — a batch that ends exactly at max_chars is fine;
            a single line longer than max_chars gets its own batch.

    Returns:
        List of index groups, e.g. [[0, 1], [2, 3, 4], [5]]
    """
    batches: list[list[int]] = []
    current: list[int] = []
    current_chars = 0
    for idx, line in enumerate(lines):
        # Keep batches small enough that intra-sentence pauses don't accumulate
        # to a detectable silence split, but big enough for smooth prosody.
        effective_len = len(line)
        if effective_len > max_chars:
            if current:
                batches.append(current)
                current = []
                current_chars = 0
            batches.append([idx])
            continue
        if current_chars + effective_len > max_chars and current:
            batches.append(current)
            current = []
            current_chars = 0
        current.append(idx)
        current_chars += effective_len
    if current:
        batches.append(current)
    return batches
