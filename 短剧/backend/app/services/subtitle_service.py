"""
字幕生成服务 - 根据分镜对话生成 SRT 字幕文件。

每句对话按字数估算时长（约 0.3 秒/字），按片段顺序排列时间轴。
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# 每字平均朗读时长（秒）
SECONDS_PER_CHAR = 0.3

# 每句之间的停顿（秒）
PAUSE_BETWEEN_SENTENCES = 0.5

# 单句最小时长（秒）
MIN_DURATION = 1.5

# 单句最大时长（秒）
MAX_DURATION = 10.0


def estimate_duration(text: str) -> float:
    """
    根据文本字数估算朗读时长。

    Args:
        text: 对话文本。

    Returns:
        估算的秒数。
    """
    char_count = len(text.strip())
    if char_count == 0:
        return 0.0
    duration = char_count * SECONDS_PER_CHAR + PAUSE_BETWEEN_SENTENCES
    return max(MIN_DURATION, min(duration, MAX_DURATION))


def format_timestamp(seconds: float) -> str:
    """
    将秒数格式化为 SRT 时间戳格式。

    Args:
        seconds: 秒数。

    Returns:
        格式如 "00:00:03,500"。
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(storyboards: list[dict]) -> str:
    """
    根据分镜列表生成 SRT 字幕内容。

    每个 storyboard 字典应包含：
      - dialogue: 对话文本（为空则跳过）
      - episode_no: 集数（用于排序）
      - shot_no: 镜头序号（用于排序）

    Args:
        storyboards: 分镜字典列表。

    Returns:
        SRT 格式的字幕字符串。
    """
    if not storyboards:
        return ""

    # 过滤有对话的分镜，按集数和镜头排序
    items = [
        s for s in storyboards
        if s.get("dialogue") and s["dialogue"].strip()
    ]
    items.sort(key=lambda s: (s.get("episode_no", 0), s.get("shot_no", 0)))

    if not items:
        return ""

    srt_lines: list[str] = []
    current_time = 0.0

    for idx, item in enumerate(items, start=1):
        dialogue = item["dialogue"].strip()
        duration = estimate_duration(dialogue)
        start_time = current_time
        end_time = current_time + duration

        srt_lines.append(str(idx))
        srt_lines.append(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}")
        srt_lines.append(dialogue)
        srt_lines.append("")  # SRT 条目之间空行

        current_time = end_time

    return "\n".join(srt_lines)


def save_srt(srt_content: str, output_path: str) -> str:
    """
    将 SRT 内容保存为文件。

    Args:
        srt_content: SRT 字幕文本。
        output_path: 输出文件路径。

    Returns:
        保存的文件路径。
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    logger.info("SRT 字幕已保存: %s", output_path)
    return output_path
