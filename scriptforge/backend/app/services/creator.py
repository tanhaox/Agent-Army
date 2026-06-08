import json
import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.persona import Persona
from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)

PERSONA_CREATOR_PROMPT = """你是一位顶级的网红人设设计师，专门为抖音直播连线场景打造爆款主播人设。

【任务】根据用户提供的风格要求，创建一个完整的网红人设档案。

【用户要求】
__REQUIREMENTS__

__REFERENCE_SECTION__

【输出格式】严格 JSON（不要 markdown 标记），包含以下字段：
- persona_name: 人设名称（4-8个字，有记忆点）
- global_style: 总体风格综述（100字以内）
- language_style: 包含 aggressiveness, humor, empathy, rhythm, metaphor_usage, catchphrase_density（各0-10）
- catchphrases: 口头禅列表（至少5个）
- reaction_patterns: 面对"诉苦"/"吹牛"/"挑衅"/"共鸣"各一种反应模式
- sentence_templates: 常用句式模板（至少5个，用___代替可变部分）
- core_values: 核心价值观列表
- tone_adaptation: 各调性适配系数（情感解忧铺、怼人脱口秀、知识暴击场、玄学聊天室、做饭聊人生，各0-1）
- style_summary: 人设定位总结（50字以内）
- recommended_scenarios: 最适合的直播间调性列表

【设计要求】
1. 人设必须有鲜明的记忆点和辨识度，避免平庸
2. 口头禅要朗朗上口，有传播性
3. 反应模式要体现人格一致性
4. 评分要合理，避免极端"""

GUEST_BATCH_PROMPT = """你是一位直播连线内容策划，专门设计有节目效果的连线人角色。

【任务】根据指定主题，生成 __COUNT__ 个差异化的连线人身份卡。

【主题】__TOPIC__

【要求】
1. 每个连线人都要有明确的身份、年龄、职业、性格和核心问题
2. 连线人之间要有明显差异（不同年龄层、职业、性格、问题类型）
3. 核心问题要具有话题性，能引发讨论和共鸣
4. 避免刻板印象，但要真实接地气

【输出格式】严格 JSON，顶层 key 为 "guests"，值为数组，每个元素包含：
- name: 连线人代称（如"北漂小张"）
- age_range: 18-25/25-35/35-45/45+
- occupation: 职业
- personality: 性格描述（15字以内）
- core_issue: 核心连线问题（30字以内）
- speaking_style: 说话风格特征
- tags: 标签列表
- expected_reaction: 预期的主播反应类型"""

STYLE_FUSION_PROMPT = """你是一位人设设计师，专门进行网红人设的风格融合。

【任务】将两套人设特征按照指定比例融合，生成一个全新的、内部一致的人设。

【人设 A】（权重 __RATIO_A__%）
__PERSONA_A__

【人设 B】（权重 __RATIO_B__%）
__PERSONA_B__

【融合要求】
1. 口头禅：从两人设的口头禅中各取几个，综合排序
2. 反应模式：按权重侧重某一方，但融合出内部一致的新风格
3. 评分：按权重计算加权平均，可微调
4. 核心价值观：合并去重，保留不冲突的部分
5. 新人设必须有独立辨识度，不是简单拼接

【输出格式】严格 JSON，与标准人设分析报告一致，包含：
persona_name, global_style, language_style(aggressiveness/humor/empathy/rhythm/metaphor_usage/catchphrase_density 0-10), catchphrases, reaction_patterns, sentence_templates, core_values, tone_adaptation, style_summary"""


def _build_persona_prompt(requirements: str, reference: str) -> str:
    prompt = PERSONA_CREATOR_PROMPT.replace("__REQUIREMENTS__", requirements)
    if reference and reference != "暂无参考策略":
        prompt = prompt.replace("__REFERENCE_SECTION__", f"【参考爆款策略】\n{reference}")
    else:
        prompt = prompt.replace("__REFERENCE_SECTION__", "")
    return prompt


def _build_guest_prompt(topic: str, count: int) -> str:
    return GUEST_BATCH_PROMPT.replace("__COUNT__", str(count)).replace("__TOPIC__", topic)


def _build_fusion_prompt(persona_a: dict, persona_b: dict, ratio: float) -> str:
    ratio_a = int(ratio * 100)
    ratio_b = 100 - ratio_a
    return STYLE_FUSION_PROMPT \
        .replace("__RATIO_A__", str(ratio_a)) \
        .replace("__RATIO_B__", str(ratio_b)) \
        .replace("__PERSONA_A__", json.dumps(persona_a, ensure_ascii=False, indent=2)) \
        .replace("__PERSONA_B__", json.dumps(persona_b, ensure_ascii=False, indent=2))


class CreatorService:
    async def _call_deepseek(self, system_prompt: str, user_message: str, temperature: float = 0.9) -> dict:
        return await deepseek.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=4096,
            timeout=90.0,
            response_format={"type": "json_object"},
        )

    async def _get_reference_strategies(self, query: str) -> str:
        try:
            from app.services.vector_store import vector_store
            if vector_store._col().count() == 0:
                return "暂无参考策略"
            results = vector_store.query_vectors(query, top_k=3)
            if results:
                lines = []
                for r in results:
                    meta = r.get("metadata", {})
                    pt = meta.get("pattern_type", "")
                    doc = r.get("document", "")
                    lines.append(f"- [{pt}] {doc}")
                return "\n".join(lines)
        except Exception as e:
            logger.warning("Strategy retrieval skipped: %s", e)
        return "暂无参考策略"

    async def create_persona(self, requirements: str) -> dict:
        reference = await self._get_reference_strategies(requirements)
        prompt = _build_persona_prompt(requirements, reference)
        user_message = "请根据以上要求，设计一个完整的网红人设档案。"
        try:
            result = await self._call_deepseek(prompt, user_message, temperature=0.9)
        except Exception as e:
            logger.warning("Persona creation failed, returning fallback: %s", e)
            return _fallback_persona(requirements)
        logger.info("Created persona: %s", result.get("persona_name", "unknown"))
        return result

    async def create_guests(self, topic: str, count: int = 20) -> list[dict]:
        prompt = _build_guest_prompt(topic, count)
        user_message = f"请生成 {count} 个关于「{topic}」主题的差异化连线人角色。"
        try:
            result = await self._call_deepseek(prompt, user_message, temperature=0.8)
            guests = result.get("guests", [])
        except Exception as e:
            logger.warning("Guest creation failed, returning fallback: %s", e)
            guests = _fallback_guests(topic, min(count, 5))
        logger.info("Created %d guests for topic: %s", len(guests), topic)
        return guests

    async def fuse_personas(
        self, persona_id_a: str, persona_id_b: str, ratio: float = 0.5, db: AsyncSession | None = None
    ) -> dict:
        own_session = db is None
        if own_session:
            db = async_session_factory()

        try:
            try:
                uuid_a = uuid.UUID(persona_id_a)
                uuid_b = uuid.UUID(persona_id_b)
            except ValueError:
                raise ValueError("Invalid persona UUID format")

            persona_a = await db.get(Persona, uuid_a)
            persona_b = await db.get(Persona, uuid_b)
            if not persona_a or not persona_b:
                raise ValueError("Persona not found")

            a_data = {
                "name": persona_a.name,
                "global_style": persona_a.global_style,
                "language_style": persona_a.language_style or {},
                "catchphrases": persona_a.catchphrases or [],
                "reaction_patterns": persona_a.reaction_patterns or {},
                "sentence_templates": persona_a.sentence_templates or [],
                "core_values": persona_a.core_values or [],
                "tone_adaptation": persona_a.tone_adaptation or {},
            }
            b_data = {
                "name": persona_b.name,
                "global_style": persona_b.global_style,
                "language_style": persona_b.language_style or {},
                "catchphrases": persona_b.catchphrases or [],
                "reaction_patterns": persona_b.reaction_patterns or {},
                "sentence_templates": persona_b.sentence_templates or [],
                "core_values": persona_b.core_values or [],
                "tone_adaptation": persona_b.tone_adaptation or {},
            }

            prompt = _build_fusion_prompt(a_data, b_data, ratio)
            user_message = "请将以上两个人设按指定比例融合，生成一个全新的人设。"
            result = await self._call_deepseek(prompt, user_message, temperature=0.8)
            logger.info("Fused persona: %s + %s -> %s", persona_a.name, persona_b.name, result.get("persona_name", "unknown"))
            return result
        finally:
            if own_session:
                await db.close()


def _fallback_persona(requirements: str) -> dict:
    """Return a placeholder persona when DeepSeek is unavailable."""
    return {
        "persona_name": "降级人设",
        "global_style": "AI 服务暂时不可用，此为占位人设，请稍后重试",
        "language_style": {"tone": "待分析", "vocabulary": "待分析", "rhythm": "待分析", "habits": "待分析"},
        "catchphrases": ["（待分析）"],
        "reaction_patterns": {"greeting": "待分析", "question": "待分析", "praise": "待分析", "criticism": "待分析"},
        "sentence_templates": [],
        "core_values": [],
        "tone_adaptation": {"high_energy": "待分析", "low_energy": "待分析", "emotional": "待分析"},
        "degraded": True,
    }


def _fallback_guests(topic: str, count: int) -> list[dict]:
    """Return preset guest templates when DeepSeek is unavailable."""
    templates = [
        {"name": "热情粉丝", "personality": "外向热情，容易激动", "core_issue": f"对{topic}有很多疑问", "speaking_style": "快节奏，感叹多"},
        {"name": "理性分析", "personality": "冷静理性，喜欢追根究底", "core_issue": f"想深入了解{topic}的本质", "speaking_style": "有条理，逻辑清晰"},
        {"name": "感性共鸣", "personality": "感情丰富，容易共情", "core_issue": f"在{topic}上有切身经历", "speaking_style": "叙述式，情感丰富"},
        {"name": "质疑挑战", "personality": "独立思考，不轻易信服", "core_issue": f"对{topic}的主流观点持怀疑态度", "speaking_style": "反问多，直接"},
        {"name": "沉默寡言", "personality": "内向少言，但观点深刻", "core_issue": f"对{topic}有独特见解但不太会表达", "speaking_style": "短句为主，偶尔爆金句"},
    ]
    return [{**t, "tags": ["降级"], "degraded": True} for t in templates[:count]]


creator_service = CreatorService()
