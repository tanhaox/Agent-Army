"""
剧本生成服务 - 调用 AI 生成结构化剧本。

职责：提示词构建、JSON 解析与修复、内容包装。
"""

import json
import logging
import re
import time
from typing import Any, Optional

from app.services.llm import get_llm_client, LLMConnectionError, LLMGenerateError

logger = logging.getLogger(__name__)

# 系统提示词模板，约束 AI 输出严格 JSON 格式
SYSTEM_PROMPT = """你是一位专业的短剧编剧。用户会给你一个短剧主题，请你生成一个完整的竖屏微短剧剧本。

你必须且只能输出一个合法的 JSON 对象，不要输出任何其他文字、解释或 markdown 代码块标记。

直接以 { 开头，以 } 结尾。

JSON 结构如下（严格使用以下英文字段名）：

{
  "title": "剧名",
  "episodes": [
    {
      "episode": 1,
      "hook": "开篇钩子，20字内",
      "scenes": [
        {
          "shot_type": "近景",
          "action": "画面描述，30字内",
          "dialogue": "角色对话，可留空",
          "emotion": "紧张"
        }
      ],
      "cliffhanger": "结尾悬念，20字内"
    }
  ],
  "total_episodes": 3
}

创作规则：
1. 总集数控制在 3 集（不要超过）
2. 每集 3-4 个 scenes
3. 竖屏短剧风格：节奏快、反转多、每集结尾留悬念
4. shot_type 只能是：远景、中景、近景、特写
5. emotion 只能是：平静、紧张、愤怒、悲伤、惊喜、甜蜜、恐惧
6. 对话简短有力
7. **严格禁止** 使用对角色外貌的主观评价词汇（如"性感""漂亮""帅气""迷人""妩媚""英俊"等）。
8. 允许客观的外貌描述（如"穿红色外套""长发""戴眼镜""身材高大"），但必须是可视觉呈现的。
9. 动作和画面描述应聚焦于角色的行为、表情、环境，而非外貌评判。

再次强调：只输出 JSON，不要输出任何其他内容，不要用 markdown 代码块。
"""


class ScriptParseError(Exception):
    """剧本 JSON 解析失败时抛出。"""


class ScriptGenerationService:
    """
    剧本生成服务。

    调用 LLM 生成结构化剧本，处理 JSON 解析与修复。
    """

    def __init__(self) -> None:
        self._client = get_llm_client()
        self._system_prompt = SYSTEM_PROMPT

    def _build_prompt(self, theme: str, episodes_hint: Optional[int]) -> str:
        """
        构建用户提示词。

        Args:
            theme: 剧本主题。
            episodes_hint: 用户建议的集数（可选）。

        Returns:
            完整的用户提示词。
        """
        parts = [f"请根据以下主题创作一部竖屏微短剧剧本：\n\n主题：{theme}"]

        if episodes_hint is not None:
            parts.append(f"\n建议集数：{episodes_hint} 集（你可以根据故事需要适当调整）")

        parts.append("\n\n请直接输出 JSON，不要包含任何其他文字。")
        return "\n".join(parts)

    def _extract_json(self, text: str) -> str:
        """
        从 AI 响应中提取 JSON 字符串。

        尝试以下策略：
        1. 直接解析整个文本
        2. 提取 ```json ... ``` 代码块
        3. 查找最外层 { } 配对

        Args:
            text: AI 原始响应文本。

        Returns:
            提取出的 JSON 字符串。

        Raises:
            ScriptParseError: 无法提取有效 JSON。
        """
        # 策略1：直接尝试
        text_stripped = text.strip()
        if text_stripped.startswith("{"):
            return text_stripped

        # 策略2：提取 ```json ... ``` 代码块
        code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text_stripped)
        if code_block_match:
            return code_block_match.group(1).strip()

        # 策略3：查找最外层 { }
        brace_match = re.search(r"\{[\s\S]*\}", text_stripped)
        if brace_match:
            return brace_match.group(0)

        raise ScriptParseError(f"无法从 AI 响应中提取 JSON。原始响应前200字：{text_stripped[:200]}")

    def _validate_script_structure(self, data: dict[str, Any]) -> None:
        """
        校验剧本结构是否符合规范。

        Args:
            data: 解析后的剧本字典。

        Raises:
            ScriptParseError: 结构不符合要求。
        """
        if "title" not in data:
            raise ScriptParseError("剧本缺少 title 字段")
        if "episodes" not in data or not isinstance(data["episodes"], list):
            raise ScriptParseError("剧本缺少 episodes 数组")
        if len(data["episodes"]) == 0:
            raise ScriptParseError("episodes 数组为空")

        for i, ep in enumerate(data["episodes"]):
            if "scenes" not in ep or not isinstance(ep["scenes"], list):
                raise ScriptParseError(f"第 {i + 1} 集缺少 scenes 数组")
            if len(ep["scenes"]) < 2:
                raise ScriptParseError(f"第 {i + 1} 集场景数不足（至少需要2个）")

        # 补全 total_episodes
        if "total_episodes" not in data:
            data["total_episodes"] = len(data["episodes"])

    def _parse_response(self, raw_text: str) -> dict[str, Any]:
        """
        解析 AI 响应为剧本字典。

        Args:
            raw_text: AI 原始响应文本。

        Returns:
            解析后的剧本字典。

        Raises:
            ScriptParseError: 解析或校验失败。
        """
        json_str = self._extract_json(raw_text)

        # 清理 JSON 中的非法控制字符（换行、制表符等）
        import re
        json_str = re.sub(r'[\x00-\x1f]', ' ', json_str)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ScriptParseError(
                f"JSON 解析失败: {e}. 原始内容前200字：{json_str[:200]}"
            ) from e

        if not isinstance(data, dict):
            raise ScriptParseError(f"JSON 根元素不是对象，而是 {type(data).__name__}")

        self._validate_script_structure(data)
        return data

    async def generate_script(
        self,
        theme: str,
        project_name: str,
        episodes_hint: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        生成完整剧本。

        流程：
        1. 构建提示词 → 2. 调用 LLM → 3. 解析 JSON
        4. 若解析失败，重试一次（附带修复提示）→ 5. 包装返回

        Args:
            theme: 剧本主题。
            project_name: 项目名称。
            episodes_hint: 建议集数（可选）。

        Returns:
            完整的剧本 content 字典，包含 title, episodes, total_episodes, metadata。

        Raises:
            LLMConnectionError: LLM 连接失败。
            LLMGenerateError: AI 生成失败。
            ScriptParseError: JSON 解析失败（重试后仍失败）。
        """
        prompt = self._build_prompt(theme, episodes_hint)

        # 第一次调用
        logger.info("开始生成剧本: project=%s, theme前30字=%s", project_name, theme[:30])
        raw_response = await self._client.generate(prompt, system=self._system_prompt)

        try:
            script_data = self._parse_response(raw_response)
            logger.info("剧本解析成功: %s, %d集", script_data.get("title"), len(script_data.get("episodes", [])))
        except ScriptParseError as e:
            logger.warning("首次解析失败: %s，尝试修复...", e)

            # 第二次调用：请求修复 JSON
            fix_prompt = (
                f"上一次你输出的内容不是合法的 JSON。请修正并重新输出。\n\n"
                f"要求：只输出一个 JSON 对象，不要有任何其他文字。\n\n"
                f"原始主题：{theme}"
            )
            raw_response = await self._client.generate(fix_prompt, system=self._system_prompt)

            try:
                script_data = self._parse_response(raw_response)
                logger.info("修复后解析成功: %s", script_data.get("title"))
            except ScriptParseError as e2:
                logger.error("修复后仍解析失败: %s", e2)
                raise ScriptParseError(
                    f"两次尝试均无法解析剧本 JSON。最后错误：{e2}。"
                    f"原始响应前300字：{raw_response[:300]}"
                ) from e2

        # 包装完整 content
        content = {
            "title": script_data.get("title", project_name),
            "episodes": script_data["episodes"],
            "total_episodes": script_data["total_episodes"],
            "metadata": {
                "theme": theme,
                "episodes_hint": episodes_hint,
                "actual_episodes": len(script_data["episodes"]),
            },
        }
        return content

    async def generate_from_outline(
        self,
        outline_text: str,
        style: str,
        project_name: str = "未命名",
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """
        根据剧情概要生成完整剧本（含质量检测 + 自动重试）。

        Args:
            outline_text: 剧情概要（200-300字）。
            style: 风格标签（如"虐心催泪"）。
            project_name: 项目名称。
            max_retries: 质量不达标时最大重试次数。

        Returns:
            完整的剧本 content 字典。

        Raises:
            LLMConnectionError: LLM 连接失败。
            LLMGenerateError: AI 生成失败。
            ScriptParseError: JSON 解析失败。
        """
        from app.services.blockbuster_library import build_library_context
        from app.services.script_quality_checker import run_all_checks

        library_ctx = build_library_context()

        outline_system_prompt = f"""你是一位顶尖短剧编剧，擅长创作{style}风格的竖屏微短剧。

你必须且只能输出一个合法的 JSON 对象，不要输出任何其他文字、解释或 markdown 代码块标记。

直接以 {{ 开头，以 }} 结尾。

JSON 结构如下（严格使用以下英文字段名）：

{{
  "title": "剧名",
  "episodes": [
    {{
      "episode": 1,
      "hook": "开篇钩子，20字内",
      "scenes": [
        {{
          "shot_type": "近景",
          "action": "画面描述，30字内",
          "dialogue": "角色对话，可留空，30字内",
          "emotion": "紧张"
        }}
      ],
      "cliffhanger": "结尾悬念，20字内"
    }}
  ],
  "total_episodes": 3
}}

创作规则：
1. 总集数 3-5 集
2. 每集 3-6 个 scenes
3. 竖屏短剧风格：节奏快、反转多、每集结尾留悬念
4. shot_type 只能是：远景、全景、中景、近景、特写
5. emotion 只能是：愤怒、悲伤、喜悦、紧张、恐惧、甜蜜、惊讶、平静、期待、感动
6. 对话简短有力，30字以内
7. 突出{style}风格特点
8. 每集至少包含一次反转或情绪突变
9. hook 要在前3秒抓住观众
10. **严格禁止** 使用对角色外貌的主观评价词汇（如"性感""漂亮""帅气""迷人""妩媚""英俊""清纯""可爱"等）。
11. 允许客观的外貌描述（如"穿红色外套""长发""戴眼镜""身材高大"），但必须是可视觉呈现的。
12. 动作和画面描述应聚焦于角色的行为、表情、环境，而非外貌评判。

{library_ctx}

再次强调：只输出 JSON，不要输出任何其他内容，不要用 markdown 代码块。"""

        prompt = (
            f"请根据以下剧情概要，创作一部{style}风格的竖屏微短剧完整剧本：\n\n"
            f"【剧情概要】\n{outline_text}\n\n"
            f"要求：严格遵循上述 JSON 格式输出，不要包含任何其他文字。"
        )

        quality_issues: list[str] = []

        total_start = time.time()

        for attempt in range(max_retries + 1):
            logger.info(
                "[ScriptGen] 从概要生成剧本: attempt=%d/%d, style=%s",
                attempt + 1, max_retries + 1, style,
            )

            # 如果是重试，把质量问题加入 prompt
            if quality_issues:
                issue_text = "\n".join(f"- {q}" for q in quality_issues[:10])
                prompt = (
                    f"上一次生成的剧本存在以下质量问题，请修正：\n\n"
                    f"{issue_text}\n\n"
                    f"请根据以下剧情概要重新创作：\n\n"
                    f"【剧情概要】\n{outline_text}\n\n"
                    f"要求：严格遵循 JSON 格式，确保每集都有 hook 和 cliffhanger，"
                    f"场景数 3-6 个，对话 30 字以内。"
                )

            t0 = time.time()
            raw_response = await self._client.generate(prompt, system=outline_system_prompt)
            logger.info("[ScriptGen] LLM 调用完成: attempt=%d, 耗时=%.1fs, 响应长度=%d",
                        attempt + 1, time.time() - t0, len(raw_response))

            try:
                script_data = self._parse_response(raw_response)
            except ScriptParseError as e:
                logger.warning("第 %d 次尝试 JSON 解析失败: %s", attempt + 1, e)
                quality_issues = [f"JSON 解析失败: {e}"]
                continue

            # 包装 content
            content = {
                "title": script_data.get("title", project_name),
                "episodes": script_data["episodes"],
                "total_episodes": script_data["total_episodes"],
                "metadata": {
                    "outline": outline_text,
                    "style": style,
                    "actual_episodes": len(script_data["episodes"]),
                    "attempt": attempt + 1,
                },
            }

            # 质量检测
            passed, issues = run_all_checks(content)
            if passed:
                logger.info("[ScriptGen] 质量检测通过: attempt=%d, 总耗时=%.1fs",
                            attempt + 1, time.time() - total_start)
                return content

            quality_issues = issues
            logger.warning(
                "[ScriptGen] 质量检测未通过: attempt=%d, %d个问题, 已耗时=%.1fs",
                attempt + 1, len(issues), time.time() - total_start,
            )

        # 超过重试次数，返回最后一次的结果（带警告）
        logger.warning("[ScriptGen] 超过最大重试次数，返回最后生成的剧本, 总耗时=%.1fs",
                       time.time() - total_start)
        return content
