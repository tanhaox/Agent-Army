import json
import logging

from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)

STRATEGY_EXTRACTOR_PROMPT = """你是一位顶级的直播内容策略分析师。你的任务是从提供的直播对话切片文本中，提取可复用的编剧策略和结构模式。

【分析维度】
1. pattern_type：策略类型（选择最匹配的）：
   - hook：开场钩子（如何在3秒内抓住注意力）
   - transition：话题过渡（如何自然转向核心话题）
   - climax：高潮引爆（如何制造情绪巅峰或冲突）
   - closure：收尾技巧（如何留下余味或引导互动）
   - reversal：反转技巧（如何制造意外或打脸）

2. description：策略描述（50字以内，说明这个策略的核心手法）

3. sentence_templates：可复用的句式模板（1-3个，用___代替可变部分）

4. emotional_curve：情绪走向描述（如"开场:好奇→中段:共鸣→高潮:感动→结尾:温暖"）

5. tags：风格标签（2-4个，如"自嘲"、"反差"、"共情"、"幽默比喻"）

6. quality_score：策略质量评分（1-10分，基于通用性、可复用性、独特性的综合评估）

【输入文本】
__TEXT_PLACEHOLDER__

【输出格式】
严格输出 JSON（不要包含 markdown 标记），顶层key为 "strategies"，值为数组，每个元素包含 pattern_type、description、sentence_templates、emotional_curve、tags、quality_score 字段。"""


def _build_prompt(text: str) -> str:
    return STRATEGY_EXTRACTOR_PROMPT.replace("__TEXT_PLACEHOLDER__", text)


class StrategyExtractor:
    async def extract_strategies(self, text: str, category: str) -> list[dict]:
        system_prompt = _build_prompt(text)
        user_message = f"请从以上直播文本（类型：{category}）中提取可复用的编剧策略。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = await deepseek.chat(
            messages,
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        strategies = result.get("strategies", [])
        logger.info("Extracted %d strategies from text (%d chars)", len(strategies), len(text))
        return strategies

    async def batch_extract(self, items: list[dict]) -> list[list[dict]]:
        results = []
        for item in items:
            text = item.get("text", "")
            category = item.get("category", "monologue")
            strategies = await self.extract_strategies(text, category)
            results.append(strategies)
        return results


strategy_extractor = StrategyExtractor()
