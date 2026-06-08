"""
PromptAssembler 和 prompt_vocab 的单元测试。

验证六步公式输出顺序、中英文映射、负面提示选择、默认值等。
"""

import pytest

from app.services.prompt_engineering_service import PromptAssembler
from app.services import prompt_vocab


# ── fixtures ──────────────────────────────────────────────────

@pytest.fixture
def assembler() -> PromptAssembler:
    return PromptAssembler()


@pytest.fixture
def sample_data() -> dict:
    return {
        "subject": "一只戴着银色机械腕表的男性手部",
        "action": "用金属打火机点燃一张泛黄的旧照片",
        "environment": "商场奢侈品店外，冷色调夜景，背景虚化",
        "camera": {
            "shot": "特写",
            "movement": "固定",
            "stability": "三脚架",
        },
        "style": "电影感",
        "lighting": "霓虹",
        "duration": 5,
        "aspect_ratio": "9:16",
    }


# ── prompt_vocab 测试 ─────────────────────────────────────────

class TestVocab:
    def test_shot_types_mapping(self):
        assert prompt_vocab.resolve_shot("特写") == "close-up"
        assert prompt_vocab.resolve_shot("远景") == "wide shot"
        assert prompt_vocab.resolve_shot("大远景") == "extreme wide shot"

    def test_camera_movements_mapping(self):
        assert prompt_vocab.resolve_movement("推") == "slow push-in"
        assert prompt_vocab.resolve_movement("环绕") == "orbit"
        assert prompt_vocab.resolve_movement("跟拍") == "tracking shot"

    def test_stability_mapping(self):
        assert prompt_vocab.resolve_stability("三脚架") == "tripod"
        assert prompt_vocab.resolve_stability("稳定器") == "gimbal"

    def test_style_mapping(self):
        assert prompt_vocab.resolve_style("电影感") == "cinematic"
        assert prompt_vocab.resolve_style("写实") == "photorealistic"

    def test_lighting_mapping(self):
        assert prompt_vocab.resolve_lighting("黄金时刻") == "golden hour"
        assert prompt_vocab.resolve_lighting("霓虹") == "neon lighting"

    def test_unknown_key_passthrough(self):
        assert prompt_vocab.resolve_shot("自定义景别") == "自定义景别"
        assert prompt_vocab.resolve_movement("custom") == "custom"

    def test_negative_prompt_default(self):
        neg = prompt_vocab.get_negative_prompt("通用")
        assert "no text overlays" in neg
        assert "no watermarks" in neg

    def test_negative_prompt_action(self):
        neg = prompt_vocab.get_negative_prompt("动作")
        assert "no shaky camera" in neg

    def test_negative_prompt_unknown_falls_to_default(self):
        neg = prompt_vocab.get_negative_prompt("不存在的类型")
        assert "no text overlays" in neg

    def test_clamp_duration(self):
        assert prompt_vocab.clamp_duration(5) == 5
        assert prompt_vocab.clamp_duration(1) == 3
        assert prompt_vocab.clamp_duration(20) == 15

    def test_aspect_ratios_list(self):
        assert "9:16" in prompt_vocab.ASPECT_RATIOS
        assert "16:9" in prompt_vocab.ASPECT_RATIOS


# ── PromptAssembler 六步公式测试 ────────────────────────────────

class TestSixStep:
    def test_full_assembly(self, assembler, sample_data):
        prompt = assembler.assemble_six_step(sample_data)

        # 六步顺序验证
        assert prompt.index("一只戴着银色机械腕表的男性手部") < prompt.index("用金属打火机")
        assert prompt.index("in 商场奢侈品店外") < prompt.index("camera")
        assert "camera tripod, static tripod, close-up" in prompt
        assert "style cinematic" in prompt
        assert "neon lighting" in prompt
        assert prompt.endswith("9:16")
        assert "5s" in prompt

    def test_output_contains_no_empty_segments(self, assembler, sample_data):
        prompt = assembler.assemble_six_step(sample_data)
        assert ",," not in prompt

    def test_minimal_data(self, assembler):
        data = {"subject": "一只猫", "action": "打盹"}
        prompt = assembler.assemble_six_step(data)
        assert "一只猫" in prompt
        assert "打盹" in prompt
        assert "5s" in prompt  # 默认时长
        assert "9:16" in prompt  # 默认比例

    def test_with_image_placeholder(self, assembler):
        data = {
            "subject": "图片1中的旧照片被点燃",
            "action": "火焰吞噬照片",
            "environment": "暗室",
            "camera": {"shot": "特写", "movement": "推", "stability": "三脚架"},
            "duration": 7,
            "aspect_ratio": "9:16",
        }
        prompt = assembler.assemble_six_step(data)
        assert "图片1" in prompt
        assert "7s" in prompt

    def test_invalid_ratio_falls_back(self, assembler, sample_data):
        sample_data["aspect_ratio"] = "99:99"
        prompt = assembler.assemble_six_step(sample_data)
        assert "9:16" in prompt

    def test_duration_clamped(self, assembler, sample_data):
        sample_data["duration"] = 100
        prompt = assembler.assemble_six_step(sample_data)
        assert "15s" in prompt  # max

    def test_no_environment_no_in_prefix(self, assembler):
        data = {"subject": "主体", "action": "动作"}
        prompt = assembler.assemble_six_step(data)
        assert "in " not in prompt


# ── 负面提示测试 ───────────────────────────────────────────────

class TestNegativePrompt:
    def test_default_negative(self, assembler):
        neg = assembler.build_negative_prompt({})
        assert "no text overlays" in neg
        assert "no watermarks" in neg

    def test_custom_negative_merged(self, assembler):
        neg = assembler.build_negative_prompt(
            {"negative_prompt": "no cats, no dogs"},
            scene_type="通用",
        )
        assert "no cats" in neg
        assert "no text overlays" in neg

    def test_action_scene_negative(self, assembler):
        neg = assembler.build_negative_prompt({}, scene_type="动作")
        assert "no shaky camera" in neg

    def test_deduplication(self, assembler):
        neg = assembler.build_negative_prompt(
            {"negative_prompt": "no text overlays, no watermarks, custom"},
        )
        count = neg.lower().count("no text overlays")
        assert count == 1


# ── 音画同步测试 ───────────────────────────────────────────────

class TestAudioSync:
    def test_add_dialogue(self, assembler):
        result = assembler.add_audio_sync("base prompt", "你好世界")
        assert "你好世界" in result
        assert "lip movements sync naturally" in result

    def test_empty_dialogue_no_change(self, assembler):
        result = assembler.add_audio_sync("base prompt", "")
        assert result == "base prompt"

    def test_no_dialogue_no_audio(self, assembler):
        result = assembler.add_audio_sync("base prompt", "", None)
        assert result == "base prompt"

    def test_audio_url_only(self, assembler):
        result = assembler.add_audio_sync("base prompt", "", "http://example.com/audio.mp3")
        assert "Audio reference provided" in result

    def test_dialogue_and_audio(self, assembler):
        result = assembler.add_audio_sync("base prompt", "你好", "http://example.com/a.mp3")
        assert "lip movements sync naturally" in result
        assert "Audio reference provided" in result

    def test_long_dialogue_truncated(self, assembler):
        long_text = "这是一段非常长的对话" * 20
        result = assembler.add_audio_sync("base", long_text)
        assert len(result) < len("base") + len(long_text) + 100


# ── assemble_from_creative_data 完整测试 ────────────────────────

class TestFullAssembly:
    def test_complete_output(self, assembler, sample_data):
        result = assembler.assemble_from_creative_data(sample_data)
        assert "prompt" in result
        assert "negative_prompt" in result
        assert "一只戴着银色机械腕表的男性手部" in result["prompt"]
        assert "no text overlays" in result["negative_prompt"]

    def test_inferred_scene_type_closeup(self, assembler):
        data = {
            "subject": "面部",
            "camera": {"shot": "特写"},
        }
        result = assembler.assemble_from_creative_data(data)
        assert "no distorted facial features" in result["negative_prompt"]

    def test_inferred_scene_type_action(self, assembler):
        data = {
            "subject": "主角",
            "action": "快速跑过走廊",
        }
        result = assembler.assemble_from_creative_data(data)
        assert "no shaky camera" in result["negative_prompt"]

    def test_inferred_scene_type_dialogue(self, assembler):
        data = {
            "subject": "角色",
            "dialogue": "我再也不想见到你",
        }
        result = assembler.assemble_from_creative_data(data)
        assert "lip movements sync naturally" in result["prompt"]
        assert "no lip sync errors" in result["negative_prompt"]

    def test_audio_url_in_prompt(self, assembler):
        data = {
            "subject": "角色",
            "dialogue": "你好",
            "audio_url": "http://example.com/voice.mp3",
        }
        result = assembler.assemble_from_creative_data(data)
        assert "Audio reference provided" in result["prompt"]
        assert "lip movements sync naturally" in result["prompt"]
