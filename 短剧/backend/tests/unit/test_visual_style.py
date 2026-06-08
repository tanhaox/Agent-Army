"""
项目视觉风格服务单元测试。

测试 apply_style_to_prompt、has_style_config 等纯函数。
运行: cd backend && python -m pytest tests/unit/test_visual_style.py -v --confcutdir=tests/unit
"""

import pytest

from app.services.visual_style_service import apply_style_to_prompt, has_style_config


class _FakeStyle:
    """模拟 ProjectVisualStyle 对象。"""

    def __init__(
        self,
        art_style: str | None = None,
        lighting_rule: str | None = None,
        color_palette: list | None = None,
        camera_style: str | None = None,
        style_reference_image: str | None = None,
    ):
        self.art_style = art_style
        self.lighting_rule = lighting_rule
        self.color_palette = color_palette
        self.camera_style = camera_style
        self.style_reference_image = style_reference_image


# ── apply_style_to_prompt ─────────────────────────────────────


class TestApplyStyleToPrompt:
    def test_no_style(self):
        style = _FakeStyle()
        result = apply_style_to_prompt("a man walking", style)
        assert result == "a man walking"

    def test_art_style_only(self):
        style = _FakeStyle(art_style="赛博朋克")
        result = apply_style_to_prompt("a man walking", style)
        assert "赛博朋克" in result
        assert "style consistent" in result

    def test_lighting_rule(self):
        style = _FakeStyle(lighting_rule="霓虹")
        result = apply_style_to_prompt("a woman running", style)
        assert "霓虹" in result
        assert "style consistent" in result

    def test_color_palette(self):
        style = _FakeStyle(color_palette=["#ff0000", "#00ff00"])
        result = apply_style_to_prompt("a scene", style)
        assert "#ff0000" in result
        assert "color tones" in result

    def test_all_fields(self):
        style = _FakeStyle(
            art_style="赛博朋克",
            lighting_rule="霓虹",
            color_palette=["蓝", "紫"],
        )
        result = apply_style_to_prompt("city street", style)
        assert "赛博朋克" in result
        assert "霓虹" in result
        assert "蓝" in result
        assert "style consistent" in result

    def test_video_mode(self):
        style = _FakeStyle(art_style="电影感")
        result = apply_style_to_prompt("a man", style, is_video=True)
        assert "maintain visual consistency" in result

    def test_video_mode_no_style(self):
        style = _FakeStyle()
        result = apply_style_to_prompt("a man", style, is_video=True)
        assert result == "a man"

    def test_prompt_trailing_chars_cleaned(self):
        style = _FakeStyle(art_style="写实")
        result = apply_style_to_prompt("test prompt, ", style)
        assert not result.startswith("test prompt, ,")

    def test_color_palette_limit(self):
        style = _FakeStyle(color_palette=["a", "b", "c", "d", "e", "f", "g"])
        result = apply_style_to_prompt("test", style)
        # 只取前5个颜色
        assert "a, b, c, d, e" in result
        assert "f" not in result or "g" not in result


# ── has_style_config ──────────────────────────────────────────


class TestHasStyleConfig:
    def test_empty(self):
        style = _FakeStyle()
        assert has_style_config(style) is False

    def test_with_art_style(self):
        style = _FakeStyle(art_style="写实")
        assert has_style_config(style) is True

    def test_with_reference_image(self):
        style = _FakeStyle(style_reference_image="/static/styles/test.jpg")
        assert has_style_config(style) is True

    def test_with_lighting(self):
        style = _FakeStyle(lighting_rule="霓虹")
        assert has_style_config(style) is True

    def test_with_color_palette(self):
        style = _FakeStyle(color_palette=["#ff0000"])
        assert has_style_config(style) is True

    def test_with_camera_style(self):
        style = _FakeStyle(camera_style="手持")
        assert has_style_config(style) is True
