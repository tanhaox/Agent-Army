import json
import logging

from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的直播话术分析师。你的任务是分析主播的直播片段，提取出结构化的人设特征。

请从以下维度分析并输出严格的JSON格式：

{
  "name": "人设名称（请直接使用传入的主播昵称，不要自行创造新名称）",
  "global_style": "整体语言风格描述，包含语气、节奏、用词特点",
  "language_style": {
    "tone": "语气倾向（如：温柔、激昂、幽默、理性）",
    "vocabulary": "用词特征描述",
    "rhythm": "语速和节奏特征",
    "habits": "语言习惯（如：常用句式、口头禅位置）"
  },
  "language_style_v2": {
    "rhetorical_question_freq": 0-10,
    "interrupt_tendency": 0-10,
    "sharpness": 0-10,
    "self_deprecation": 0-10,
    "humor_type": "自黑/夸张比喻/冷笑话/讽刺/无厘头/几乎没有",
    "pace": "慢/中/快",
    "max_pause_seconds": 数字,
    "grab_floor_freq": 0-10,
    "monologue_length": "短/中/长",
    "empathy_style": "倾听式/说教式/故事分享式/反问引导式",
    "emotional_volatility": 0-10,
    "emotional_triggers": ["话题1", "话题2"],
    "metaphor_domains": ["域1", "域2"],
    "topic_preferences": ["话题1", "话题2"],
    "punchline_density": 0-10,
    "opening_phrase": "口头禅或null",
    "transition_phrase": "口头禅或null",
    "closing_phrase": "口头禅或null"
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
  },
  "lingo_map": {
    "规范词1": "主播特色用词1",
    "规范词2": "主播特色用词2"
  }
}

language_style_v2 各维度说明：
- rhetorical_question_freq: 每10句中反问句次数，0=从不用反问，10=几乎每句都是反问
- interrupt_tendency: 在对方话未说完时插话的概率
- sharpness: 使用直接批评、否定性词汇的频率，0=温和委婉，10=直接犀利
- self_deprecation: 拿自己开涮vs拿对方开涮，0=从不自黑，10=频繁自黑
- humor_type: 选择最匹配的一种——自黑/夸张比喻/冷笑话/讽刺/无厘头/几乎没有
- pace: 语速推断，慢/中/快
- max_pause_seconds: 制造悬念或情绪转折时的典型停顿长度（数字）
- grab_floor_freq: 打断对方的频率，0=从不抢话，10=高频抢话
- monologue_length: 主播单次发言的平均长度，短(1-2句)/中(3-5句)/长(6句以上)
- empathy_style: 倾听式/说教式/故事分享式/反问引导式
- emotional_volatility: 从平静到激动的跨度
- emotional_triggers: 什么话题让主播情绪变化（多选）
- metaphor_domains: 偏好使用哪类比喻（多选）
- topic_preferences: 通常讨论什么话题（多选）
- punchline_density: 每10句中可独立传播的金句数量
- opening_phrase/transition_phrase/closing_phrase: 功能性口头禅，无则填null

### 第六组：主播黑话 / 代称
分析主播是否使用特定的词汇来替代常见词汇（例如用"2+1"指代"情妇"，用"馒头"指代"钱"），或者给特定事物起代称（例如用"白头鹰"指代"美国"）。
输出格式："lingo_map": {"规范词": "主播特色用词"}
如果主播没有明显的黑话或代称，输出空对象 {}。
注意：只收录主播刻意使用的、有规律性的替代词，不要收录正常的多义词或口语缩写。

注意：
1. 只输出JSON，不要输出其他内容
2. 所有字段都必须填写
3. catchphrases至少3个，sentence_templates至少3个
4. language_style_v2中的数值评分必须基于内容客观评估，不要都给相同分数
5. 基于实际内容分析，不要编造"""

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


def _map_v2_to_legacy(result: dict) -> None:
    """从 language_style_v2 映射出旧版 language_style 数值字段，保持雷达图兼容。"""
    v2 = result.get("language_style_v2")
    if not v2 or not isinstance(v2, dict):
        return
    ls = result.get("language_style") or {}

    ls["aggressiveness"] = round((v2.get("sharpness", 0) + v2.get("interrupt_tendency", 0)) / 2, 1)

    humor_type = v2.get("humor_type", "几乎没有")
    if humor_type == "几乎没有":
        ls["humor"] = 1.0
    else:
        ls["humor"] = round(min(v2.get("self_deprecation", 5) + 2, 10), 1)

    empathy_map = {"倾听式": 8, "说教式": 4, "故事分享式": 7, "反问引导式": 6}
    ls["empathy"] = float(empathy_map.get(v2.get("empathy_style", ""), 5))

    pace_map = {"慢": 3, "中": 5, "快": 8}
    ls["rhythm_score"] = float(pace_map.get(v2.get("pace", "中"), 5))

    domains = v2.get("metaphor_domains") or []
    ls["metaphor_usage"] = 7.0 if domains else 2.0

    ls["catchphrase_density"] = float(v2.get("punchline_density", 0))

    result["language_style"] = ls


class PersonaAnalyzer:
    async def analyze_text(self, text: str, anchor_name: str = "") -> dict:
        user_msg = f"请分析以下直播片段：\n\n{text}"
        if anchor_name:
            user_msg = f"主播昵称: {anchor_name}\n\n{user_msg}"
        try:
            result = await deepseek.chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=3072,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.warning("DeepSeek persona analysis failed, using fallback: %s", e)
            result = _build_minimal_persona(text, anchor_name)
            result["degraded"] = True
        if anchor_name and result.get("name") != anchor_name:
            result["name"] = anchor_name
        _map_v2_to_legacy(result)
        logger.info("Persona analysis complete: name=%s", result.get("name", "unknown"))
        return result

    async def analyze_slices(self, slices: list[str], anchor_name: str = "") -> dict:
        combined = "\n\n---\n\n".join(slices)
        return await self.analyze_text(combined, anchor_name=anchor_name)

    async def analyze_narrative(self, slices: list[str]) -> dict:
        slices_text = "\n\n---\n\n".join(slices)
        system_prompt = NARRATIVE_ANALYSIS_PROMPT.format(slices_text=slices_text)

        try:
            result = await deepseek.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "请分析以上切片的叙事结构和节奏模式。"},
                ],
                temperature=0.3,
                max_tokens=3072,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.warning("Narrative analysis failed, using fallback: %s", e)
            result = {"pacing_summary": "AI 服务暂时不可用，叙事分析降级", "narrative_units": [], "degraded": True}
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

        try:
            result = await deepseek.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,
                max_tokens=3072,
                response_format={"type": "json_object"},
            )
        except Exception as e:
            logger.warning("Incremental analysis failed, returning existing persona: %s", e)
            result = {**existing_persona, "degraded": True}
        _map_v2_to_legacy(result)
        logger.info("Incremental analysis complete: name=%s", result.get("name", "unknown"))
        return result


persona_analyzer = PersonaAnalyzer()


def _build_minimal_persona(text: str, anchor_name: str = "") -> dict:
    """Build a minimal persona dict from raw text when DeepSeek analysis fails."""
    import re as _re

    # Try to extract any JSON-like content from the raw text
    match = _re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            import json as _json
            from json_repair import repair_json
            repaired = repair_json(match.group())
            return _json.loads(repaired) if isinstance(repaired, str) else repaired
        except Exception:
            pass

    # Last resort: build a minimal persona from available info
    snippet = text[:200].replace("\n", " ").strip()
    return {
        "name": anchor_name or "未命名主播",
        "global_style": "AI 服务暂时不可用，此为占位人设，请稍后重试",
        "language_style": {
            "tone": "待分析",
            "vocabulary": "待分析",
            "rhythm": "待分析",
            "habits": "待分析",
            "aggressiveness": 5.0,
            "humor": 5.0,
            "empathy": 5.0,
            "rhythm_score": 5.0,
            "metaphor_usage": 5.0,
            "catchphrase_density": 5.0,
        },
        "language_style_v2": {
            "rhetorical_question_freq": 5,
            "interrupt_tendency": 5,
            "sharpness": 5,
            "self_deprecation": 5,
            "humor_type": "几乎没有",
            "pace": "中",
            "max_pause_seconds": 2,
            "grab_floor_freq": 5,
            "monologue_length": "中",
            "empathy_style": "倾听式",
            "emotional_volatility": 5,
            "emotional_triggers": [],
            "metaphor_domains": [],
            "topic_preferences": [],
            "punchline_density": 5,
            "opening_phrase": None,
            "transition_phrase": None,
            "closing_phrase": None,
        },
        "catchphrases": [],
        "reaction_patterns": {
            "greeting": "待分析",
            "question": "待分析",
            "praise": "待分析",
            "criticism": "待分析",
        },
        "sentence_templates": [],
        "core_values": [],
        "tone_adaptation": {
            "high_energy": "待分析",
            "low_energy": "待分析",
            "emotional": "待分析",
        },
        "lingo_map": {},
    }


def build_narrative_model(
    persona: "Persona",
    slice_count: int = 0,
    total_text_length: int = 0,
) -> dict | None:
    """从 Persona 已有字段中提取信息，构建统一的 narrative_model。"""
    try:
        ns = persona.narrative_style or {}
        opening_style = ""
        if ns.get("opening_pattern"):
            opening_style = ns["opening_pattern"].get("style", "")

        reversal_timing = ""
        if ns.get("reversal_pattern"):
            reversal_timing = ns["reversal_pattern"].get("timing", "")

        rhythm_summary = ns.get("pacing_summary", "")

        narrative_units = ns.get("narrative_units", [])

        catchphrase_count = len(persona.catchphrases or [])

        # distinctive_features: 从 global_style 和 v2 维度提取
        features: list[str] = []
        if persona.global_style:
            first_sentence = persona.global_style.split("。")[0].strip()
            if first_sentence and len(first_sentence) <= 50:
                features.append(first_sentence)
        v2 = persona.language_style_v2 or {}
        if v2.get("humor_type") and v2["humor_type"] != "几乎没有":
            features.append(f"幽默{v2['humor_type']}")
        if v2.get("empathy_style"):
            features.append(f"共情{v2['empathy_style']}")
        ls = persona.language_style or {}
        if not v2 and ls.get("tone"):
            features.append(f"语气{ls['tone']}")
        distinctive_features = features[:3]

        # completeness_score: 切片数(40%) + 文本长度(20%) + 叙事单元(10%) + v2维度(30%)
        slice_score = min(slice_count / 10, 1.0) * 40
        text_score = min(total_text_length / 50000, 1.0) * 20
        unit_score = min(len(narrative_units) / 3, 1.0) * 10
        v2_dims = sum(1 for v in v2.values() if v is not None and v != [] and v != "") if v2 else 0
        v2_score = min(v2_dims / 18, 1.0) * 30
        completeness_score = int(slice_score + text_score + unit_score + v2_score)

        # clarity_score: 置信度基于切片数量
        if slice_count >= 5:
            clarity = "high"
        elif slice_count >= 3:
            clarity = "medium"
        else:
            clarity = "low"

        return {
            "opening_style": opening_style,
            "reversal_timing": reversal_timing,
            "rhythm_summary": rhythm_summary,
            "narrative_units": narrative_units,
            "catchphrase_count": catchphrase_count,
            "distinctive_features": distinctive_features,
            "completeness_score": completeness_score,
            "clarity_score": clarity,
            "slice_count": slice_count,
        }
    except Exception:
        logger.exception("Failed to build narrative_model")
        return None
