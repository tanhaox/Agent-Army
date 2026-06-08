"""
字幕生成服务单元测试。

覆盖：estimate_duration、format_timestamp、generate_srt、save_srt。
"""

import os
import tempfile

import pytest

from app.services.subtitle_service import (
    estimate_duration,
    format_timestamp,
    generate_srt,
    save_srt,
)


class TestEstimateDuration:
    """时长估算测试。"""

    def test_short_text(self) -> None:
        """短文本不低于最小时长。"""
        duration = estimate_duration("你好")
        assert duration >= 1.5

    def test_medium_text(self) -> None:
        """中等长度文本按字数估算。"""
        text = "你凭什么这样对我？"  # 9 个字
        duration = estimate_duration(text)
        expected = 9 * 0.3 + 0.5  # 3.2 秒
        assert abs(duration - expected) < 0.01

    def test_empty_text(self) -> None:
        """空文本时长为 0。"""
        assert estimate_duration("") == 0.0

    def test_long_text_capped(self) -> None:
        """超长文本不超过最大时长。"""
        text = "测" * 100
        duration = estimate_duration(text)
        assert duration <= 10.0


class TestFormatTimestamp:
    """时间戳格式化测试。"""

    def test_zero(self) -> None:
        assert format_timestamp(0) == "00:00:00,000"

    def test_three_seconds(self) -> None:
        assert format_timestamp(3.5) == "00:00:03,500"

    def test_over_minute(self) -> None:
        assert format_timestamp(65.123) == "00:01:05,123"

    def test_over_hour(self) -> None:
        assert format_timestamp(3661.0) == "01:01:01,000"


class TestGenerateSrt:
    """SRT 生成测试。"""

    def test_empty_list(self) -> None:
        """空列表返回空字符串。"""
        assert generate_srt([]) == ""

    def test_no_dialogue(self) -> None:
        """所有分镜无对话时返回空字符串。"""
        storyboards = [
            {"episode_no": 1, "shot_no": 1, "dialogue": None},
            {"episode_no": 1, "shot_no": 2, "dialogue": ""},
        ]
        assert generate_srt(storyboards) == ""

    def test_single_dialogue(self) -> None:
        """单条对话生成正确 SRT。"""
        storyboards = [
            {"episode_no": 1, "shot_no": 1, "dialogue": "你凭什么这样对我？"},
        ]
        srt = generate_srt(storyboards)
        assert "1\n" in srt
        assert "-->" in srt
        assert "你凭什么这样对我？" in srt

    def test_multiple_dialogues(self) -> None:
        """多条对话按顺序排列。"""
        storyboards = [
            {"episode_no": 1, "shot_no": 2, "dialogue": "第二句"},
            {"episode_no": 1, "shot_no": 1, "dialogue": "第一句"},
        ]
        srt = generate_srt(storyboards)
        # SRT 中第一条是"第一句"（按 shot_no 排序）
        assert "第一句" in srt
        assert "第二句" in srt
        # 第一句在第二句之前
        assert srt.index("第一句") < srt.index("第二句")

    def test_srt_format_structure(self) -> None:
        """验证 SRT 的四行结构（序号、时间轴、文本、空行）。"""
        storyboards = [
            {"episode_no": 1, "shot_no": 1, "dialogue": "测试"},
        ]
        srt = generate_srt(storyboards)
        blocks = srt.strip().split("\n\n")
        assert len(blocks) == 1
        lines = blocks[0].split("\n")
        assert len(lines) == 3  # 序号、时间轴、文本
        assert lines[0] == "1"
        assert "-->" in lines[1]
        assert lines[2] == "测试"


class TestSaveSrt:
    """SRT 保存测试。"""

    def test_save_creates_file(self) -> None:
        """保存后文件存在。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.srt")
            save_srt("1\n00:00:00,000 --> 00:00:03,000\n测试\n", path)
            assert os.path.isfile(path)
            with open(path, encoding="utf-8") as f:
                content = f.read()
            assert "测试" in content
