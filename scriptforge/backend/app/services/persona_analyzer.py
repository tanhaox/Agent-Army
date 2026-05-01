import json
import logging

from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的直播话术分析师。你的任务是分析主播的直播片段，提取出结构化的人设特征。

请从以下维度分析并输出严格的JSON格式：

{
  "name": "人设名称（根据内容概括，2-6个字）",
  "global_style": "整体语言风格描述，包含语气、节奏、用词特点",
  "language_style": {
    "tone": "语气倾向（如：温柔、激昂、幽默、理性）",
    "vocabulary": "用词特征描述",
    "rhythm": "语速和节奏特征",
    "habits": "语言习惯（如：常用句式、口头禅位置）"
  },
  "catchphrases": ["口头禅1", "口头禅2", "口头禅3"],
  "reaction_patterns": {
    "greeting": "遇到新观众时的反应模式",
    "question": "被提问时的反应模式",
    "praise": "被赞美时的反应模式",
    "criticism": "被批评时的反应模式"
  },
  "sentence_templates": [
    "常用句式模板1（用{变量}表示可替换部分）",
    "常用句式模板2"
  ],
  "core_values": ["核心价值观1", "核心价值观2"],
  "tone_adaptation": {
    "high_energy": "高能量场景的语气调整策略",
    "low_energy": "低能量场景的语气调整策略",
    "emotional": "情感场景的语气调整策略"
  }
}

注意：
1. 只输出JSON，不要输出其他内容
2. 所有字段都必须填写
3. catchphrases至少3个，sentence_templates至少3个
4. 基于实际内容分析，不要编造"""

NARRATIVE_ANALYSIS_PROMPT = """你是一位叙事学专家，专门分析直播对话的叙事结构和节奏模式。

请分析以下主播的对话切片，提取以下叙事维度的特征：

1. **开场模式**：
   - 如何抛出话题？（直接提问/自述经历/制造悬念/假设情景/抛出一个反常识观点）
   - 开场到第一个笑点/冲突点通常需要几轮对话？
   - 开场惯用语式（如"兄弟们我今天必须说个事"）

2. **转折模式**：
   - 反转通常发生在第几轮对话？
   - 反转方式是（自嘲/揭露真相/突然反问/偷换概念/制造对立）？
   - 反转前是否有明显铺垫信号（如停顿、重复、反问）？

3. **节奏锚点**：
   - 每多少轮对话会有一个情绪小高潮或笑点？
   - 高潮后是立即降温还是连续冲击？
   - 如何控制对话的"呼吸感"（什么时候加速、什么时候放慢）？

4. **收尾模式**：
   - 如何结束话题？（总结升华/留悬念/引导互动/抛出下一个话题）
   - 结束前的标志性信号是什么？

5. **叙事模板**：
   - 提取 2-3 个反复出现的"叙事单元"（如"抛出反常识观点→对方质疑→用生活例子证明→反转→升华"）
   - 每个叙事单元描述为完整的步骤序列

【输入切片】
{slices_text}

【输出格式】严格 JSON：
{{
  "opening_pattern": {{
    "style": "风格描述",
    "avg_rounds_to_first_hook": 3,
    "typical_phrase": "开场惯用语"
  }},
  "reversal_pattern": {{
    "timing": "通常在对话的第X轮",
    "method": "反转方式",
    "signals": ["铺垫信号1", "铺垫信号2"]
  }},
  "rhythm_anchors": {{
    "climax_interval": "每X轮一个小高潮",
    "post_climax_behavior": "描述",
    "breathing_control": "呼吸感控制方式"
  }},
  "closing_pattern": {{
    "style": "收尾风格",
    "typical_signal": "标志性信号"
  }},
  "narrative_units": [
    {{
      "name": "叙事单元名称",
      "steps": ["步骤1", "步骤2", "步骤3"],
      "usage_frequency": "高频/中频/低频"
    }}
  ],
  "pacing_summary": "整体节奏一句话总结"
}}"""

INCREMENTAL_PROMPT_TEMPLATE = """你是一位资深的直播网红风格分析师。你正在对一位已有人设进行增量学习。

【现有人设特征基线】（经过以往 {existing_count} 个切片分析得出）
{existing_persona_json}

【新上传的切片】
{new_slices_text}

【增量分析要求】
1. 保留现有核心口头禅和反应模式不变，除非新切片呈现更强的替代模式
2. 如果新切片中出现了新的口头禅，追加到 catchphrases 数组
3. 如果新切片在某种情境下展现了不同的反应方式，更新 reaction_patterns 对应条目
4. 雷达图各维度评分可微调，但变化幅度不超过 ±1.5 分
5. 风格综述需融合新旧特征
6. name 字段保持与现有人设一致
7. 输出格式与初次分析完全一致（完整 JSON）

请基于以上要求，输出融合后的完整人设特征 JSON。"""


class PersonaAnalyzer:
    async def analyze_text(self, text: str) -> dict:
        result = await deepseek.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请分析以下直播片段：\n\n{text}"},
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        logger.info("Persona analysis complete: name=%s", result.get("name", "unknown"))
        return result

    async def analyze_slices(self, slices: list[str]) -> dict:
        combined = "\n\n---\n\n".join(slices)
        return await self.analyze_text(combined)

    async def analyze_narrative(self, slices: list[str]) -> dict:
        slices_text = "\n\n---\n\n".join(slices)
        system_prompt = NARRATIVE_ANALYSIS_PROMPT.format(slices_text=slices_text)

        result = await deepseek.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请分析以上切片的叙事结构和节奏模式。"},
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        logger.info("Narrative analysis complete: pacing=%s", result.get("pacing_summary", "unknown"))
        return result

    async def incremental_analyze(
        self,
        existing_persona: dict,
        new_slices: list[str],
        existing_slice_count: int,
    ) -> dict:
        existing_json = json.dumps(existing_persona, ensure_ascii=False, indent=2)
        new_text = "\n\n---\n\n".join(new_slices)

        system_prompt = INCREMENTAL_PROMPT_TEMPLATE.format(
            existing_count=existing_slice_count,
            existing_persona_json=existing_json,
            new_slices_text=new_text,
        )
        user_message = "请对以上新切片进行增量分析，输出融合后的完整人设特征。"

        result = await deepseek.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )
        logger.info("Incremental analysis complete: name=%s", result.get("name", "unknown"))
        return result


persona_analyzer = PersonaAnalyzer()
