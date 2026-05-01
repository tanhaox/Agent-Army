import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.persona import Persona
from app.models.room_tone import RoomTone
from app.models.script_project import ScriptProject
from app.services.compliance import compliance_checker
from app.services.deepseek_client import deepseek

logger = logging.getLogger(__name__)

EMOTION_CURVES = {
    "default": "自然起伏：开场暖场→引出话题→轻微冲突→化解→共鸣收尾",
    "rollercoaster": "过山车式：开场平静→突然激烈冲突→反转→再反转→意外收尾",
    "warm": "温水煮蛙：开场温馨→逐渐深入→情感爆发→感动收尾",
    "confrontation": "对抗式：开场针锋相对→升级冲突→第三方视角化解→和解或保留意见",
    "mystery": "悬疑式：开场抛出谜题→层层揭秘→意外真相→回味收尾",
}

VERSION_STYLES = {
    "version_1": {
        "name": "反转型",
        "instruction": "额外风格侧重：在对话中段设置一个出人意料的话题转折或身份反转，让连线观众和观众都感到惊讶",
        "temperature": 0.8,
    },
    "version_2": {
        "name": "共鸣型",
        "instruction": "额外风格侧重：深挖连线观众的情感诉求，制造感动和认同，对话节奏舒缓但有力，结尾要有催泪金句",
        "temperature": 0.7,
    },
    "version_3": {
        "name": "搞笑型",
        "instruction": "额外风格侧重：用夸张比喻、无厘头对比制造笑点，节奏轻快，金句密度高，让人忍不住想截图分享",
        "temperature": 0.9,
    },
}

SYSTEM_PROMPT_TEMPLATE = """你是一位顶级的直播连线脚本编剧，服务于抖音平台。

【直播间规则 - 最高优先级】
{room_tone_rules}
{room_tone_forbidden}

【主播人设】
{persona_context}

{persona_narrative_context}

{scene_type_instruction}

{caller_enhancement_instruction}

【内容合规要求 - 必须严格遵守】
1. 禁止出现政治敏感、色情低俗、暴力恐怖内容
2. 禁止出现抖音平台明确禁止的词汇（包括但不限于竞品平台名称）
3. 禁止诱导未成年人打赏或危险行为
4. 内容必须积极健康，符合社会主义核心价值观
5. 台词不出现明确的广告、微信号、手机号等联系方式

【切片化脚本生成要求 — 最高优先级】
整个脚本必须为"直播后切片"而创作，每个切片是一个 30-90 秒的独立短视频：

1. **金句密度**：
   - 每 3-5 句台词中，必须有一句"金句"（可独立传播的短句，适合作为切片标题或字幕封面）
   - 金句特征：押韵、反转、共鸣、反常识、幽默比喻
   - 在 JSON 输出中，金句的 is_highlight 字段必须设为 true

2. **情绪陡坡**：
   - 每 6-8 轮对话必须出现一个明确的情绪转折点
   - 转折方向可以是：平淡→冲突、冲突→反转、反转→共鸣、共鸣→升华
   - 每个转折点标记为 is_highlight=true，highlight_title 填写适合的切片标题

3. **开头钩子（前 3 轮对话内）**：
   - 必须有"钩子"——让观众在 3 秒内决定停留的话术
   - 钩子类型：反常识观点、悬念提问、剧烈反差、情感共鸣
   - 钩子所在回合标记 is_highlight=true

4. **结尾升华（最后 2 轮对话内）**：
   - 必须有"收尾金句"——适合切片结尾的高共鸣或高反转短句
   - 收尾后对话自然结束或引导互动
   - 收尾金句标记 is_highlight=true

5. **独立切片单元**：
   - 整个脚本可以分为 2-3 个"可独立传播的切片单元"
   - 每个单元包含：钩子 → 展开 → 高潮 → 收尾
   - 单元边界标记在 emotion_curve_actual 中

6. **切片标题生成**：
   - 每个高光时刻的 highlight_title 必须是完整的、可直接使用的切片标题
   - 标题风格：悬疑问、数字式、反转式、共鸣式
   - 示例："连线到一个35岁被裁的程序员，他这句话让我愣了三秒"
   - 标题字数 10-25 字

7. **基础要求**：
   - 对话长度控制在 20-30 轮之间
   - 主播的台词风格必须严格符合人设特征
   - 连线观众的台词要符合其设定的身份、年龄、性格和问题
   - 对话中的角色名必须严格使用"主播"和"连线观众"，禁止使用"观众"等其他变体

【情绪曲线要求】
{emotion_curve_instruction}

【热点关联】
{hot_topic_instruction}

【输出格式】
请严格按照以下 JSON 格式输出（不要包含任何 markdown 标记）：
{{
  "title": "脚本标题（吸引人的，有梗的）",
  "dialogues": [
    {{
      "turn": 1,
      "speaker": "主播" 或 "连线观众"（只能用这两个值，绝不能用"观众"），
      "text": "台词内容",
      "emotion": "情绪",
      "is_highlight": false,
      "highlight_title": ""
    }}
  ],
  "emotion_curve_actual": ["开场:xxx", "发展:xxx", "高潮:xxx", "收尾:xxx"],
  "overall_style_note": "整体风格备注"
}}
重要提醒：speaker 字段必须且只能使用"主播"或"连线观众"这两个值。
"""

SCENE_TYPE_PROMPTS = {
    "entertainment": """【场景约束：泛娱乐连线】
- 核心目标：制造娱乐效果和可切片的高能时刻
- 话题方向：可涉及热点、奇葩经历、反转故事
- 互动节奏：快节奏，多反转，笑点密集
- 切片关键词：搞笑、反转、神回复""",

    "talent": """【场景约束：才艺主播维护连线】
- 核心目标：维护付费用户（榜一/大哥）情感关系，同时制造直播效果
- 话题方向：感谢陪伴、分享近况、适度情感互动
- 互动节奏：温和但有温度，不制造对抗
- 禁忌：不能过度索取、不能暴露隐私、不能引发其他粉丝不满
- 切片关键词：感动、陪伴、真心话""",

    "emotional": """【场景约束：情感倾诉连线】
- 核心目标：倾听连线者的情感困惑，引发直播间观众共鸣
- 话题方向：恋爱问题、家庭矛盾、职场困境
- 互动节奏：先倾听→再共情→然后给出有智慧的建议→最后升华
- 切片关键词：共鸣、破防、人间清醒""",
}

CALLER_ENHANCEMENT_PROMPT = """【连线者角色增强 — 隐性节奏注入】
当前连线者的说话逻辑参考了某位高粉主播的叙事风格，但请注意：

1. **去标签化**：绝不要使用该大V的标志性口头禅、语气词或个人标签句式
2. **保留内核**：保留其"叙事逻辑"——
   - 何时抛出一个让对方惊讶的观点
   - 如何用生活化的例子解释复杂问题
   - 在什么时机反问对方制造互动
   - 用多长时间铺垫一个反转
3. **身份适配**：以上逻辑必须适配连线者当前的身份设定（年龄、职业、性格、问题）
4. **效果目标**：观众听完会觉得"这个连线人说话好有道理/好有趣"，但不会联想到任何具体的大V"""


def _build_persona_context(persona: Persona) -> str:
    parts = [f"主播名称：{persona.name}"]
    parts.append(f"整体风格：{persona.global_style}")

    if persona.language_style:
        ls = persona.language_style
        parts.append(f"语气倾向：{ls.get('tone', '未设定')}")
        parts.append(f"用词特征：{ls.get('vocabulary', '未设定')}")
        parts.append(f"语速节奏：{ls.get('rhythm', '未设定')}")

    if persona.catchphrases:
        parts.append(f"口头禅：{'、'.join(persona.catchphrases)}")

    if persona.sentence_templates:
        templates = "、".join(persona.sentence_templates[:5])
        parts.append(f"常用句式：{templates}")

    if persona.reaction_patterns:
        rp = persona.reaction_patterns
        parts.append("反应模式：")
        for key, val in rp.items():
            parts.append(f"  - {key}：{val}")

    if persona.core_values:
        parts.append(f"核心价值观：{'、'.join(persona.core_values)}")

    return "\n".join(parts)


def _build_narrative_context(persona: Persona) -> str:
    """从 persona.narrative_style 构建叙事节奏上下文。"""
    ns = persona.narrative_style
    if not ns:
        return ""

    parts = ["【叙事节奏参考（提取自该主播的对话切片）】"]

    op = ns.get("opening_pattern", {})
    if op:
        parts.append(f"开场方式：{op.get('style', '未知')}")
        if op.get("typical_phrase"):
            parts.append(f"开场惯用语：{op.get('typical_phrase')}")
        if op.get("avg_rounds_to_first_hook"):
            parts.append(f"首钩子轮次：约第{op['avg_rounds_to_first_hook']}轮")

    rp = ns.get("reversal_pattern", {})
    if rp:
        parts.append(f"反转时机：{rp.get('timing', '未知')}")
        parts.append(f"反转方式：{rp.get('method', '未知')}")

    ra = ns.get("rhythm_anchors", {})
    if ra:
        parts.append(f"高潮间隔：{ra.get('climax_interval', '未知')}")
        parts.append(f"呼吸控制：{ra.get('breathing_control', '未知')}")

    cp = ns.get("closing_pattern", {})
    if cp:
        parts.append(f"收尾风格：{cp.get('style', '未知')}")
        if cp.get("typical_signal"):
            parts.append(f"收尾信号：{cp.get('typical_signal')}")

    units = ns.get("narrative_units", [])
    if units:
        for u in units:
            freq = u.get("usage_frequency", "")
            parts.append(f"叙事单元「{u.get('name', '')}」（{freq}）：{' → '.join(u.get('steps', []))}")

    if ns.get("pacing_summary"):
        parts.append(f"节奏总结：{ns['pacing_summary']}")

    return "\n".join(parts)


class ScriptGenerator:
    async def generate(
        self,
        tone_id: str,
        persona_id: str,
        guest_config: dict,
        emotion_curve: str | None = None,
        strategy_mix: str = "conservative",
        hot_topic: str | None = None,
        multi_version: bool = False,
        scene_type: str = "entertainment",
        enable_caller_enhancement: bool = False,
        db: AsyncSession | None = None,
        user_id: uuid.UUID | None = None,
    ) -> dict:
        own_session = db is None
        if own_session:
            db = async_session_factory()

        try:
            tone_uuid = uuid.UUID(tone_id)
            persona_uuid = uuid.UUID(persona_id)
        except ValueError:
            raise ValueError("Invalid tone_id or persona_id format")

        try:
            tone = await db.get(RoomTone, tone_uuid)
            if not tone or not tone.is_active:
                raise ValueError(f"RoomTone not found or inactive: {tone_id}")

            persona = await db.get(Persona, persona_uuid)
            if not persona or not persona.is_active:
                raise ValueError(f"Persona not found or inactive: {persona_id}")

            persona_context = _build_persona_context(persona)
            narrative_context = _build_narrative_context(persona)

            emotion_curve_instruction = EMOTION_CURVES.get(
                emotion_curve or "default", EMOTION_CURVES["default"]
            )
            hot_topic_instruction = (
                f"请在脚本中自然融入以下热点话题：{hot_topic}"
                if hot_topic
                else "无需绑定特定热点话题"
            )

            scene_type_instruction = SCENE_TYPE_PROMPTS.get(
                scene_type, SCENE_TYPE_PROMPTS["entertainment"]
            )

            caller_enhancement_instruction = (
                CALLER_ENHANCEMENT_PROMPT if enable_caller_enhancement else ""
            )

            base_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                room_tone_rules=tone.core_rules,
                room_tone_forbidden=tone.forbidden_topics or "无特殊禁止话题",
                persona_context=persona_context,
                persona_narrative_context=narrative_context,
                emotion_curve_instruction=emotion_curve_instruction,
                hot_topic_instruction=hot_topic_instruction,
                scene_type_instruction=scene_type_instruction,
                caller_enhancement_instruction=caller_enhancement_instruction,
            )

            guest_desc = self._build_guest_desc(guest_config)

            strategy_section = await self._retrieve_relevant_strategies(
                tone_context=tone.core_rules,
                persona_context=persona_context,
                guest_context=guest_desc,
            )
            if strategy_section:
                base_prompt = base_prompt.rstrip() + "\n\n" + strategy_section

            if multi_version:
                return await self._generate_multi_version(
                    base_prompt, guest_desc, tone_uuid, persona_uuid,
                    emotion_curve, strategy_mix, db, user_id,
                )

            result = await self._call_deepseek(base_prompt, guest_desc, temperature=0.8)

            full_text = " ".join(d.get("text", "") for d in result.get("dialogues", []))
            compliance_result = await self._check_compliance(full_text)
            highlights = self._extract_highlights(result.get("dialogues", []))
            word_count = len(full_text)

            script_project = ScriptProject(
                title=result.get("title", "未命名脚本"),
                tone_id=tone_uuid,
                persona_id=persona_uuid,
                script_content=result,
                emotion_curve=emotion_curve or "default",
                strategy_mix=strategy_mix,
                multi_version=False,
                word_count=word_count,
                sensitive_hits=compliance_result.get("hits", []),
                status="completed",
                created_by=user_id,
            )
            db.add(script_project)
            await db.commit()
            await db.refresh(script_project)

            return {
                "script_id": str(script_project.id),
                "title": result.get("title", ""),
                "dialogues": result.get("dialogues", []),
                "compliance": compliance_result,
                "highlights": highlights,
                "word_count": word_count,
                "emotion_curve_actual": result.get("emotion_curve_actual", []),
                "overall_style_note": result.get("overall_style_note", ""),
            }
        finally:
            if own_session:
                await db.close()

    async def _generate_multi_version(
        self, base_prompt: str, guest_desc: str,
        tone_uuid, persona_uuid,
        emotion_curve, strategy_mix, db, user_id=None,
    ) -> dict:
        import asyncio

        async def gen_one(version_key: str, version_meta: dict) -> dict:
            style_prompt = base_prompt.replace(
                "{emotion_curve_instruction}",
                base_prompt.split("【情绪曲线要求】")[1].split("【")[0].strip()
                if "【情绪曲线要求】" in base_prompt else ""
            )
            prompt_with_style = base_prompt + f"\n\n{version_meta['instruction']}"
            result = await self._call_deepseek(prompt_with_style, guest_desc, temperature=version_meta["temperature"])
            full_text = " ".join(d.get("text", "") for d in result.get("dialogues", []))
            compliance_result = await self._check_compliance(full_text)
            highlights = self._extract_highlights(result.get("dialogues", []))
            return {
                "version_id": version_key,
                "version_name": version_meta["name"],
                "title": result.get("title", ""),
                "dialogues": result.get("dialogues", []),
                "highlights": highlights,
                "compliance": compliance_result,
                "word_count": len(full_text),
                "emotion_curve_actual": result.get("emotion_curve_actual", []),
                "overall_style_note": result.get("overall_style_note", ""),
                "status": "completed",
            }

        async def gen_one_safe(version_key: str, version_meta: dict) -> dict:
            try:
                return await gen_one(version_key, version_meta)
            except Exception as e:
                logger.error("Version %s generation failed: %s", version_key, e)
                return {
                    "version_id": version_key,
                    "version_name": version_meta["name"],
                    "error": str(e),
                    "status": "failed",
                }

        versions = await asyncio.gather(
            gen_one_safe("version_1", VERSION_STYLES["version_1"]),
            gen_one_safe("version_2", VERSION_STYLES["version_2"]),
            gen_one_safe("version_3", VERSION_STYLES["version_3"]),
        )

        successful = [v for v in versions if v.get("status") != "failed"]
        if not successful:
            raise RuntimeError("All three script versions failed to generate")

        total_word_count = sum(v.get("word_count", 0) for v in versions)
        all_hits = []
        for v in versions:
            if v.get("compliance"):
                all_hits.extend(v["compliance"].get("hits", []))

        script_project = ScriptProject(
            title=f"多版本脚本 ({successful[0]['title']})",
            tone_id=tone_uuid,
            persona_id=persona_uuid,
            script_content={"multi_version": True, "versions": [v for v in versions]},
            emotion_curve=emotion_curve or "default",
            strategy_mix=strategy_mix,
            multi_version=True,
            word_count=total_word_count,
            sensitive_hits=all_hits,
            status="completed",
            created_by=user_id,
        )
        db.add(script_project)
        await db.commit()
        await db.refresh(script_project)

        return {
            "script_id": str(script_project.id),
            "multi_version": True,
            "versions": [
                {
                    "version_id": v["version_id"],
                    "version_name": v["version_name"],
                    "dialogues": v["dialogues"],
                    "highlights": v["highlights"],
                    "compliance": v["compliance"],
                    "word_count": v["word_count"],
                    "emotion_curve_actual": v["emotion_curve_actual"],
                    "overall_style_note": v["overall_style_note"],
                }
                for v in versions
            ],
            "recommended_version": 0,
            "word_count": total_word_count,
        }

    def _build_guest_desc(self, guest_config: dict) -> str:
        parts = []
        if guest_config.get("name"):
            parts.append(f"名称：{guest_config['name']}")
        if guest_config.get("age_range"):
            parts.append(f"年龄段：{guest_config['age_range']}")
        if guest_config.get("occupation"):
            parts.append(f"职业：{guest_config['occupation']}")
        if guest_config.get("personality"):
            parts.append(f"性格：{guest_config['personality']}")
        if guest_config.get("core_issue"):
            parts.append(f"核心诉求/问题：{guest_config['core_issue']}")

        guest_info = "\n".join(parts) if parts else "普通观众"
        return f"请为以下连线观众生成一段完整的直播对话脚本：\n\n{guest_info}"

    async def _call_deepseek(
        self, system_prompt: str, user_message: str, temperature: float = 0.8,
    ) -> dict:
        return await deepseek.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=4096,
            timeout=120.0,
            response_format={"type": "json_object"},
        )

    async def _check_compliance(self, text: str) -> dict:
        await compliance_checker._ensure_loaded()
        return compliance_checker.check(text)

    def _extract_highlights(self, dialogues: list[dict]) -> list[dict]:
        highlights = []
        for d in dialogues:
            if d.get("is_highlight"):
                highlights.append({
                    "turn": d.get("turn", 0),
                    "title": d.get("highlight_title", f"高光时刻 - 第{d.get('turn', '?')}轮"),
                    "reason": d.get("emotion", ""),
                })
        return highlights

    async def _retrieve_relevant_strategies(
        self,
        tone_context: str,
        persona_context: str,
        guest_context: str,
        top_k: int = 3,
    ) -> str | None:
        try:
            from app.services.vector_store import vector_store
            if vector_store._col().count() == 0:
                return None

            query_text = f"{tone_context[:100]} {persona_context[:100]} {guest_context[:100]}"
            results = vector_store.query_vectors(query_text, top_k=top_k)

            if not results:
                return None

            lines = ["【参考爆款策略】（以下是历史上效果好的对话策略，请作为参考但不强制照搬）"]
            for i, r in enumerate(results, 1):
                meta = r.get("metadata", {})
                pt = meta.get("pattern_type", "unknown")
                doc = r.get("document", "")
                lines.append(f"{i}. [{pt}] {doc}")

            logger.info("Injected %d strategies into prompt", len(results))
            return "\n".join(lines)
        except Exception as e:
            logger.warning("Strategy retrieval skipped: %s", e)
            return None


script_generator = ScriptGenerator()
