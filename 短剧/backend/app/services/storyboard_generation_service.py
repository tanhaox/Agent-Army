"""
分镜自动生成服务 - 根据剧本内容调用 AI 生成分镜草稿。

职责：读取剧本 → 构建提示词 → 调用 LLM → 解析 JSON → 写入数据库。
"""

import json
import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.script import Script
from app.models.storyboard import Storyboard, SHOT_TYPES, CAMERA_MOVES, VFX_OPTIONS
from app.services.llm import get_llm_client, LLMConnectionError, LLMGenerateError
from app.services.storyboard_service import create_storyboard, generate_prompt_text
from app.services.storyboard_rules import validate_and_fix_storyboard
from app.services.video_prompt_templates import build_standard_prompt, build_enhanced_prompt, build_negative_prompt
from app.services.storyboard_service import enhance_video_prompt

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""你是一位专业的短剧分镜师。用户会给你一个剧本的场景列表，请你为每个场景生成分镜参数。

你必须且只能输出一个合法的 JSON 数组，不要输出任何其他文字、解释或 markdown 代码块标记。

直接以 [ 开头，以 ] 结尾。

JSON 数组中每个元素的结构如下（严格使用以下英文字段名）：

[
  {{
    "episode_no": 1,
    "shot_no": 1,
    "shot_type": "近景",
    "camera_move": "固定",
    "action": "角色动作描述，30字内",
    "dialogue": "对话内容，可留空",
    "emotion": "紧张",
    "vfx": "无",
    "environment": "场景环境描述，20字内",
    "lighting": "光线描述，15字内"
  }}
]

规则：
1. shot_type 只能是以下之一：{"、".join(SHOT_TYPES)}
2. camera_move 只能是以下之一：{"、".join(CAMERA_MOVES)}
3. emotion 从以下选取：平静、紧张、愤怒、悲伤、惊喜、甜蜜、恐惧、期待、感动、困惑
4. vfx 从以下选取：{"、".join(VFX_OPTIONS)}。有特效时选择对应类型，无特效则写"无"
5. 为每个场景分配一个递增的 shot_no（同一集内从1开始）
6. environment 要具体，如"豪华办公室，落地窗外是城市夜景"、"昏暗小巷，雨水滴落"
7. lighting 要贴合场景氛围，如"暖色调台灯"、"冷色调荧光灯"、"自然日光"
8. 如果场景有对话，dialogue 填入对话内容；没有对话则填 null
9. action 是对画面的视觉描述，不重复对话内容

再次强调：只输出 JSON 数组，不要输出任何其他内容，不要用 markdown 代码块。
"""


class StoryboardGenerationError(Exception):
    """分镜生成失败时抛出。"""


class StoryboardGenerationService:
    """
    分镜自动生成服务。

    读取项目当前剧本内容，构建提示词调用 LLM 生成结构化分镜数据，
    解析 JSON 后批量写入数据库。
    """

    def __init__(self) -> None:
        self._client = get_llm_client()

    def _extract_json(self, text: str) -> str:
        """
        从 AI 响应中提取 JSON 字符串。

        尝试以下策略：
        1. 直接解析整个文本
        2. 提取 ```json ... ``` 代码块
        3. 查找最外层 [ ] 配对
        """
        text_stripped = text.strip()

        # 策略1：直接尝试
        if text_stripped.startswith("["):
            return text_stripped

        # 策略2：提取代码块
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text_stripped)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 策略3：查找最外层 [ ]
        bracket_match = re.search(r"\[[\s\S]*\]", text_stripped)
        if bracket_match:
            return bracket_match.group(0)

        raise StoryboardGenerationError(
            f"无法从 AI 响应中提取 JSON 数组。原始响应前200字：{text_stripped[:200]}"
        )

    def _validate_storyboard(self, item: dict[str, Any], index: int) -> list[str]:
        """
        校验并修复单个分镜的字段。

        Returns:
            修复后的字段错误列表（空表示通过）。
        """
        errors: list[str] = []
        required = ["episode_no", "shot_no", "shot_type", "camera_move", "action", "emotion", "environment", "lighting"]
        for field in required:
            if field not in item or item[field] is None:
                errors.append(f"第 {index + 1} 个分镜缺少必填字段: {field}")

        # 修正 shot_type
        if item.get("shot_type") and item["shot_type"] not in SHOT_TYPES:
            item["shot_type"] = "中景"

        # 修正 camera_move
        if item.get("camera_move") and item["camera_move"] not in CAMERA_MOVES:
            item["camera_move"] = "固定"

        # 补全 vfx
        if "vfx" not in item or not item["vfx"]:
            item["vfx"] = "无"

        return errors

    def _parse_response(self, raw_text: str) -> list[dict[str, Any]]:
        """
        解析 AI 响应为分镜列表。

        Returns:
            解析后的分镜字典列表。
        """
        json_str = self._extract_json(raw_text)

        # 清理非法控制字符
        json_str = re.sub(r"[\x00-\x1f]", " ", json_str)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise StoryboardGenerationError(
                f"JSON 解析失败: {e}. 原始内容前200字：{json_str[:200]}"
            ) from e

        if not isinstance(data, list):
            raise StoryboardGenerationError(
                f"JSON 根元素不是数组，而是 {type(data).__name__}"
            )

        if len(data) == 0:
            raise StoryboardGenerationError("AI 返回的分镜数组为空")

        # 逐条校验
        all_errors: list[str] = []
        for i, item in enumerate(data):
            errors = self._validate_storyboard(item, i)
            all_errors.extend(errors)

        if all_errors:
            logger.warning("分镜校验有警告: %s", "; ".join(all_errors[:5]))

        return data

    async def generate_storyboards(
        self,
        db: AsyncSession,
        project_id: str,
        regenerate: bool = False,
    ) -> list[Storyboard]:
        """
        根据项目剧本自动生成分镜。

        Args:
            db: 数据库会话。
            project_id: 项目 ID。
            regenerate: 是否重新生成（先删除已有分镜）。

        Returns:
            生成的分镜列表。

        Raises:
            StoryboardGenerationError: 生成或解析失败。
            LLMConnectionError: LLM 连接失败。
            LLMGenerateError: AI 生成失败。
        """
        # 1. 读取项目当前剧本
        result = await db.execute(
            select(Script)
            .where(Script.project_id == project_id)
            .order_by(Script.created_at.desc())
        )
        script = result.scalar_one_or_none()

        if script is None:
            raise StoryboardGenerationError(f"项目 {project_id} 没有关联的剧本，请先生成剧本")

        content = script.content
        if not content or "episodes" not in content:
            raise StoryboardGenerationError("剧本内容格式不正确，缺少 episodes 数据")

        # 2. 如果 regenerate，先删除已有分镜
        if regenerate:
            existing = await db.execute(
                select(Storyboard).where(Storyboard.project_id == project_id)
            )
            old_list = existing.scalars().all()
            for sb in old_list:
                await db.delete(sb)
            await db.flush()
            logger.info("已删除项目 %s 的 %d 条旧分镜", project_id, len(old_list))

        # 3. 构建用户提示词 — 把剧本场景列表传给 AI
        episodes = content.get("episodes", [])
        scenes_text = self._build_scenes_prompt(episodes)

        logger.info(
            "开始生成分镜: project=%s, script=%s, %d集",
            project_id, script.id, len(episodes),
        )

        # 4. 第一次调用
        raw_response = await self._client.generate(scenes_text, system=SYSTEM_PROMPT)

        try:
            storyboards_data = self._parse_response(raw_response)
            logger.info("分镜解析成功: %d 条", len(storyboards_data))
        except StoryboardGenerationError as e:
            logger.warning("首次解析失败: %s，尝试修复...", e)

            # 第二次调用
            fix_prompt = (
                "上一次你输出的内容不是合法的 JSON 数组。请修正并重新输出。\n\n"
                "要求：只输出一个 JSON 数组，不要有任何其他文字。\n\n"
                f"{scenes_text}"
            )
            raw_response = await self._client.generate(fix_prompt, system=SYSTEM_PROMPT)

            try:
                storyboards_data = self._parse_response(raw_response)
                logger.info("修复后解析成功: %d 条", len(storyboards_data))
            except StoryboardGenerationError as e2:
                logger.error("修复后仍解析失败: %s", e2)
                raise StoryboardGenerationError(
                    f"两次尝试均无法解析分镜 JSON。最后错误：{e2}"
                ) from e2

        # 5. 后处理校验（规则库）
        all_warnings: list[str] = []
        for item in storyboards_data:
            warnings = validate_and_fix_storyboard(item)
            all_warnings.extend(warnings)
        if all_warnings:
            for w in all_warnings[:10]:
                logger.warning("分镜规则校验: %s", w)

        # 6. 获取项目视觉设定
        visual_settings = None
        try:
            from app.models.visual_template import VisualTemplate
            vt_result = await db.execute(
                select(VisualTemplate).where(VisualTemplate.id == content.get("visual_template_id"))
            )
            vt = vt_result.scalar_one_or_none()
            if vt and vt.settings:
                visual_settings = vt.settings
        except Exception:
            pass

        # 7. 写入数据库 + 增强版提示词
        created: list[Storyboard] = []
        for item in storyboards_data:
            # 先生成模板版兜底
            standard_prompt = build_standard_prompt(item, visual_settings)
            negative = build_negative_prompt(item)

            prompt_text = standard_prompt

            # 尝试 DeepSeek 增强版（不阻塞主流程）
            try:
                enhanced = await enhance_video_prompt(item, visual_settings)
                if enhanced.get("enhanced"):
                    prompt_text = enhanced["enhanced"]
                if enhanced.get("negative_prompt"):
                    negative = enhanced["negative_prompt"]
                logger.info(
                    "分镜 ep=%d shot=%d 提示词增强成功",
                    item["episode_no"], item["shot_no"],
                )
            except Exception as e:
                logger.warning(
                    "分镜 ep=%d shot=%d 提示词增强失败，使用模板版: %s",
                    item["episode_no"], item["shot_no"], e,
                )

            sb = await create_storyboard(
                db,
                script_id=str(script.id),
                project_id=project_id,
                episode_no=item["episode_no"],
                shot_no=item["shot_no"],
                shot_type=item["shot_type"],
                camera_move=item["camera_move"],
                action=item["action"],
                dialogue=item.get("dialogue"),
                emotion=item["emotion"],
                vfx=item.get("vfx", "无"),
                environment=item["environment"],
                lighting=item["lighting"],
                prompt_text=prompt_text,
                negative_prompt=negative,
            )
            created.append(sb)

        logger.info("分镜生成完成: project=%s, %d 条已写入", project_id, len(created))
        return created

    def _build_scenes_prompt(self, episodes: list[dict]) -> str:
        """
        将剧本场景列表转换为用户提示词。

        Args:
            episodes: 剧本 episodes 数组。

        Returns:
            格式化的场景列表文本。
        """
        lines = ["请根据以下剧本场景列表，为每个场景生成分镜参数：\n"]

        for ep in episodes:
            ep_no = ep.get("episode", 1)
            lines.append(f"第 {ep_no} 集：")
            scenes = ep.get("scenes", [])
            for j, scene in enumerate(scenes):
                shot_type = scene.get("shot_type", "中景")
                action = scene.get("action", "")
                dialogue = scene.get("dialogue", "")
                emotion = scene.get("emotion", "平静")
                lines.append(
                    f"  场景{j + 1}: 景别={shot_type}, 动作={action}, "
                    f"对话={dialogue or '无'}, 情绪={emotion}"
                )
            lines.append("")

        lines.append("请直接输出 JSON 数组，不要包含任何其他文字。")
        return "\n".join(lines)
