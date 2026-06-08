"""
Seedance 2.0 视频提示词工程服务。

将结构化的创意数据 (creative_data) 转换为符合 Seedance 2.0 最佳实践的 prompt：
- 六步公式：[主体], [动作], in [环境], camera [镜头指令], style [风格], avoid [负面提示], [时长]s, [比例]
- 自动中英文映射
- 多模态引用（图片n 占位符保留）
"""

import logging
from typing import Any

from app.services import prompt_vocab

logger = logging.getLogger(__name__)


class PromptAssembler:
    """
    视频提示词组装器。

    接收结构化 creative_data，输出符合 Seedance 2.0 规范的 prompt 和 negative_prompt。
    """

    def __init__(self, vocab: type = prompt_vocab) -> None:
        self.vocab = vocab

    def assemble_six_step(self, data: dict[str, Any]) -> str:
        """
        六步公式组装 prompt。

        输入 data 结构：
        {
            "subject": "主体描述（可含 图片n 占位符）",
            "action": "动作描述",
            "environment": "环境描述",
            "camera": {"shot": "特写", "movement": "推", "stability": "三脚架"},
            "style": "电影感"（可选）,
            "lighting": "黄金时刻"（可选）,
            "duration": 5,
            "aspect_ratio": "9:16"
        }

        输出：
        "主体描述, 动作描述, in 环境描述, camera tripod slow push-in, close-up, style cinematic, golden hour lighting, 5s, 9:16"
        """
        subject = data.get("subject", "")
        action = data.get("action", "")
        environment = data.get("environment", "")

        camera_block = self._build_camera_block(data.get("camera", {}))
        style_block = self._build_style_block(data)
        duration = self.vocab.clamp_duration(data.get("duration", 5))
        aspect_ratio = data.get("aspect_ratio", "9:16")
        if aspect_ratio not in self.vocab.ASPECT_RATIOS:
            aspect_ratio = "9:16"

        segments: list[str] = []

        if subject:
            segments.append(subject.strip().rstrip(",."))
        if action:
            segments.append(action.strip().rstrip(",."))
        if environment:
            segments.append(f"in {environment.strip().rstrip(',.')}")
        if camera_block:
            segments.append(f"camera {camera_block}")
        if style_block:
            segments.append(style_block)

        segments.append(f"{duration}s")
        segments.append(aspect_ratio)

        prompt = ", ".join(segments)
        return self._clean(prompt)

    def build_negative_prompt(
        self,
        data: dict[str, Any],
        scene_type: str = "通用",
    ) -> str:
        """
        生成负面提示词。

        自动合并词汇库中的通用/场景负面提示与用户自定义项。
        """
        parts: list[str] = []

        base = self.vocab.get_negative_prompt(scene_type)
        if base:
            parts.append(base)

        custom = data.get("negative_prompt", "")
        if custom:
            parts.append(custom.strip())

        merged = ", ".join(parts)
        return self._deduplicate(merged)

    def add_audio_sync(self, base_prompt: str, dialogue: str, audio_url: str | None = None) -> str:
        """
        音画同步：根据对话和参考音频追加同步描述。

        Args:
            base_prompt: 已组装的 prompt。
            dialogue: 对话文本。
            audio_url: 参考音频 URL（可选）。
        """
        if not dialogue and not audio_url:
            return base_prompt

        suffixes: list[str] = []

        if dialogue and dialogue.strip():
            snippet = dialogue.strip()[:80]
            suffixes.append(
                f'As the character says "{snippet}", '
                f"the lip movements sync naturally, facial expression matches the emotion."
            )

        if audio_url:
            suffixes.append("Audio reference provided, sync with the voiceover.")

        if not suffixes:
            return base_prompt

        return base_prompt + " " + " ".join(suffixes)

    def assemble_from_creative_data(self, creative_data: dict[str, Any]) -> dict[str, str]:
        """
        完整组装：从 creative_data 生成 prompt + negative_prompt。

        Returns:
            {"prompt": "...", "negative_prompt": "..."}
        """
        prompt = self.assemble_six_step(creative_data)

        scene_type = self._infer_scene_type(creative_data)
        negative = self.build_negative_prompt(creative_data, scene_type)

        dialogue = creative_data.get("dialogue", "")
        audio_url = creative_data.get("audio_url")
        if dialogue or audio_url:
            prompt = self.add_audio_sync(prompt, dialogue, audio_url)

        return {"prompt": prompt, "negative_prompt": negative}

    # ── 内部方法 ──────────────────────────────────────────────

    def _build_camera_block(self, camera: dict[str, str]) -> str:
        """组装镜头指令：稳定方式 + 运镜 + 景别。"""
        stability = self.vocab.resolve_stability(camera.get("stability", ""))
        movement = self.vocab.resolve_movement(camera.get("movement", ""))
        shot = self.vocab.resolve_shot(camera.get("shot", ""))

        parts: list[str] = []
        if stability:
            parts.append(stability)
        if movement:
            parts.append(movement)
        if shot:
            parts.append(shot)
        return ", ".join(parts)

    def _build_style_block(self, data: dict[str, Any]) -> str:
        """组装风格+光照指令。"""
        style_cn = data.get("style", "")
        lighting_cn = data.get("lighting", "")

        parts: list[str] = []
        if style_cn:
            style_en = self.vocab.resolve_style(style_cn)
            parts.append(f"style {style_en}")
        if lighting_cn:
            lighting_en = self.vocab.resolve_lighting(lighting_cn)
            parts.append(f"{lighting_en}")

        return ", ".join(parts)

    def _infer_scene_type(self, data: dict[str, Any]) -> str:
        """根据数据推断场景类型，用于选择负面提示模板。"""
        shot = data.get("camera", {}).get("shot", "")
        action = data.get("action", "")
        dialogue = data.get("dialogue", "")

        if shot in ("极特写", "特写"):
            return "特写"
        if shot in ("远景", "大远景"):
            return "远景"
        if dialogue:
            return "对话"
        if action and any(kw in action for kw in ("跑", "打", "追", "跳", "摔", "飞")):
            return "动作"
        return "通用"

    @staticmethod
    def _clean(text: str) -> str:
        import re
        text = re.sub(r",\s*,", ",", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip(", ")

    @staticmethod
    def _deduplicate(text: str) -> str:
        items = [s.strip() for s in text.split(",") if s.strip()]
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            low = item.lower()
            if low not in seen:
                seen.add(low)
                unique.append(item)
        return ", ".join(unique)
