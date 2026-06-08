"""
端到端集成测试 — 验证智能导演 → PromptAssembler → 保存 完整链路。

不依赖数据库，纯 Python 测试后端服务层的集成逻辑。
运行方式: cd backend && python -m pytest tests/unit/test_e2e_integration.py -v --confcutdir=tests/unit
"""

import json
import pytest

from app.services.prompt_engineering_service import PromptAssembler
from app.services.intelligent_director_service import (
    migrate_director_analysis,
    _extract_creative_data_from_prompt,
)


@pytest.fixture
def assembler() -> PromptAssembler:
    return PromptAssembler()


# ── 场景1：完整链路 — creative_data → prompt → 验证 ─────────────

class TestFullPipeline:
    """模拟智能导演完整输出 → PromptAssembler 组装 → 结构验证。"""

    def test_no_dialogue_pipeline(self, assembler):
        """无对话场景：纯视觉镜头。"""
        creative_data = {
            "subject": "图片1中的泛黄旧照片被一双修长的男性手拿在手中",
            "action": "金属打火机的火焰缓缓舔舐照片边缘",
            "environment": "商场奢侈品店外走廊，冷色调夜景",
            "camera": {"shot": "特写", "movement": "固定", "stability": "三脚架"},
            "style": "电影感",
            "lighting": "霓虹",
            "duration_suggestion": 5,
            "aspect_ratio": "9:16",
        }

        result = assembler.assemble_from_creative_data(creative_data)

        # 验证 prompt 结构
        prompt = result["prompt"]
        assert "图片1" in prompt
        assert "camera tripod, static tripod, close-up" in prompt
        assert "style cinematic" in prompt
        assert "5s" in prompt
        assert "9:16" in prompt
        assert "lip movements" not in prompt  # 无对话，不应有音画同步

        # 验证负面提示
        neg = result["negative_prompt"]
        assert "no text overlays" in neg

    def test_dialogue_pipeline(self, assembler):
        """含对话场景：音画同步。"""
        creative_data = {
            "subject": "一个穿着黑色风衣的男人站在雨中",
            "action": "缓缓转身面对镜头",
            "environment": "城市街道，大雨倾盆",
            "camera": {"shot": "近景", "movement": "推", "stability": "稳定器"},
            "style": "电影感",
            "lighting": "蓝调时刻",
            "dialogue": "我已经等了你十年",
            "duration_suggestion": 7,
            "aspect_ratio": "9:16",
        }

        result = assembler.assemble_from_creative_data(creative_data)

        # 验证音画同步
        assert "lip movements sync naturally" in result["prompt"]
        assert "我已经等了你十年" in result["prompt"]
        assert "facial expression matches the emotion" in result["prompt"]

        # 验证负面提示选择对话模板
        assert "no lip sync errors" in result["negative_prompt"]

    def test_audio_reference_pipeline(self, assembler):
        """含参考音频：音频同步描述。"""
        creative_data = {
            "subject": "女性角色微笑",
            "action": "轻轻点头",
            "dialogue": "好吧，我答应你",
            "audio_url": "http://example.com/voice_ref.mp3",
            "camera": {"shot": "中景", "movement": "固定", "stability": "三脚架"},
            "style": "写实",
            "duration_suggestion": 5,
        }

        result = assembler.assemble_from_creative_data(creative_data)

        assert "lip movements sync naturally" in result["prompt"]
        assert "Audio reference provided" in result["prompt"]

    def test_action_scene_negative(self, assembler):
        """动作场景：自动选择动作负面提示模板。"""
        creative_data = {
            "subject": "主角快速跑过走廊",
            "action": "跳过障碍物，翻滚落地",
            "camera": {"shot": "全景", "movement": "跟拍", "stability": "稳定器"},
            "duration_suggestion": 10,
        }

        result = assembler.assemble_from_creative_data(creative_data)
        assert "no shaky camera" in result["negative_prompt"]


# ── 场景2：迁移函数 — 旧格式兼容 ────────────────────────────────

class TestMigration:
    """验证旧格式 director_analysis 的迁移逻辑。"""

    def test_migrate_old_format(self):
        old_analysis = {
            "material_requirements": [
                {"id": "bg_1", "type": "background", "name": "夜景街道", "prompt": "测试"},
                {"id": "prop_1", "type": "prop", "name": "手机", "prompt": "测试"},
                {"id": "expr_1", "type": "character_expression", "name": "惊讶表情", "prompt": "测试"},
            ],
            "video_instruction": {
                "prompt": "旧格式的prompt文本，描述一个男人在街上走路",
                "negative_prompt": "模糊",
                "duration": 5,
            },
        }

        result = migrate_director_analysis(old_analysis)

        # 验证 creative_data 已生成
        assert "creative_data" in result
        cd = result["creative_data"]
        assert cd["_migrated"] is True
        assert cd["camera"]["shot"] == "中景"

        # 验证 necessity 已补全
        reqs = result["material_requirements"]
        assert reqs[0]["necessity"] == "optional"  # background
        assert reqs[1]["necessity"] == "required"  # prop
        assert reqs[2]["necessity"] == "required"  # character_expression

        # 验证 images 已构建
        images = result["video_instruction"]["images"]
        assert len(images) == 2  # prop + character_expression

    def test_migrate_new_format_unchanged(self):
        """新格式数据迁移后不应丢失 creative_data。"""
        new_analysis = {
            "material_requirements": [
                {"id": "p1", "type": "prop", "name": "测试", "prompt": "t", "necessity": "required", "material_index": 1},
            ],
            "creative_data": {
                "subject": "测试主体",
                "action": "测试动作",
                "camera": {"shot": "特写", "movement": "推", "stability": "三脚架"},
            },
            "video_instruction": {
                "prompt": "测试prompt",
                "images": [{"material_id": "p1", "material_index": 1, "description": "测试"}],
            },
        }

        result = migrate_director_analysis(new_analysis)
        # creative_data 保持原样，不应被覆盖
        assert result["creative_data"]["subject"] == "测试主体"
        assert "_migrated" not in result["creative_data"]


# ── 场景3：模拟完整 LLM 输出 → 后处理 ───────────────────────────

class TestLLMOutputIntegration:
    """模拟 LLM 返回的 JSON → 后处理 → PromptAssembler 组装。"""

    def test_full_director_output(self, assembler):
        """模拟一个完整的导演分析输出。"""
        llm_output = {
            "material_requirements": [
                {
                    "id": "bg_rain_street",
                    "type": "background",
                    "name": "雨夜街道",
                    "description": "夜晚的城市街道，大雨倾盆，路灯昏黄",
                    "reason": "设定环境氛围",
                    "necessity": "optional",
                    "material_index": None,
                    "prompt": "夜晚城市街道，大雨倾盆，路灯昏黄光线，积水倒影，4K",
                    "status": "pending",
                    "generated_url": None,
                },
                {
                    "id": "prop_letter",
                    "type": "prop",
                    "name": "一封未寄出的信",
                    "description": "泛黄的信纸，字迹模糊",
                    "reason": "关键道具",
                    "necessity": "required",
                    "material_index": 1,
                    "prompt": "泛黄的信纸，手写中文字迹，折痕明显，边缘泛黄，4K特写",
                    "status": "pending",
                    "generated_url": None,
                },
            ],
            "creative_data": {
                "subject": "图片1中的信被风吹起，在空中飘舞",
                "action": "信纸被雨水打湿，墨迹逐渐晕开",
                "environment": "雨夜街道，路灯昏黄，积水倒影",
                "camera": {"shot": "特写", "movement": "推", "stability": "三脚架"},
                "style": "电影感",
                "lighting": "低调",
                "dialogue": "这封信，我终于可以寄出去了",
                "duration_suggestion": 5,
                "aspect_ratio": "9:16",
            },
            "video_instruction": {
                "mode": "image_to_video",
                "images": [
                    {"material_id": "prop_letter", "material_index": 1, "description": "一封未寄出的信"},
                ],
                "prompt": "placeholder",
                "negative_prompt": "placeholder",
                "audio": {
                    "voiceover": "这封信，我终于可以寄出去了",
                    "sound_effects": ["雨声", "纸张翻动声"],
                    "bgm": "忧伤钢琴曲",
                },
                "duration": 5,
                "aspect_ratio": "9:16",
            },
        }

        # 模拟 analyze_and_plan 中的 PromptAssembler 调用
        cd = llm_output["creative_data"]
        assembled = assembler.assemble_from_creative_data(cd)
        llm_output["video_instruction"]["prompt"] = assembled["prompt"]
        llm_output["video_instruction"]["negative_prompt"] = assembled["negative_prompt"]

        vi = llm_output["video_instruction"]

        # 验证最终 prompt
        assert "图片1" in vi["prompt"]
        assert "camera tripod, slow push-in, close-up" in vi["prompt"]
        assert "style cinematic" in vi["prompt"]
        assert "5s" in vi["prompt"]
        assert "9:16" in vi["prompt"]
        assert "lip movements sync naturally" in vi["prompt"]
        assert "这封信" in vi["prompt"]

        # 验证负面提示（特写优先于对话模板）
        assert "no distorted facial features" in vi["negative_prompt"] or "no lip sync errors" in vi["negative_prompt"]

        # 验证可 JSON 序列化（存入数据库）
        json_str = json.dumps(llm_output, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["video_instruction"]["prompt"] == vi["prompt"]

        print("\n=== 最终 Prompt ===")
        print(vi["prompt"])
        print("\n=== 最终 Negative ===")
        print(vi["negative_prompt"])
