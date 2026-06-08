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

【主播人设 — 必须严格遵循以下风格，这是脚本质量的核心评判标准】
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
    # ── 第一组：娱乐互动类 ──
    "entertainment_comedy": """【场景约束：搞笑整蛊连线】
- 核心目标：制造笑点和意外反转，让观众笑出声
- 话题方向：奇葩经历、整蛊挑战、神回复、无厘头对话
- 互动节奏：快节奏，每3-5轮对话必须有一个笑点或反转
- 禁忌：不能人身攻击、不能低俗下流
- 切片关键词：搞笑、反转、笑喷""",

    "entertainment_chat": """【场景约束：聊天陪伴连线】
- 核心目标：营造轻松闲聊的氛围，给观众陪伴感
- 话题方向：日常分享、兴趣爱好、随机吐槽、生活趣事
- 互动节奏：舒缓自然，像朋友聊天
- 禁忌：避免过度煽情或制造对立
- 切片关键词：陪伴、治愈、下饭""",

    "entertainment_game": """【场景约束：游戏互动连线】
- 核心目标：通过猜谜、答题或对抗游戏制造互动热度
- 话题方向：看图猜词、脑筋急转弯、PK小游戏、知识竞赛
- 互动节奏：紧张刺激，有输赢悬念
- 禁忌：不能涉及赌博性质的游戏
- 切片关键词：互动、挑战、上头""",

    "entertainment_gossip": """【场景约束：热点八卦连线】
- 核心目标：围绕最新热点事件展开讨论，制造话题度
- 话题方向：娱乐八卦、社会新闻、体育赛事、网络热梗
- 互动节奏：快节奏，观点鲜明，金句频出
- 禁忌：不传播谣言、不恶意炒作、不涉及政治敏感
- 切片关键词：吃瓜、热议、观点""",

    # ── 第二组：知识与观点类 ──
    "knowledge_science": """【场景约束：知识科普连线】
- 核心目标：寓教于乐，用生动方式传播知识
- 话题方向：历史故事、科学冷知识、生活技巧、奇闻异事
- 互动节奏：娓娓道来，用故事或比喻包装知识
- 禁忌：不能传播伪科学、不能枯燥说教
- 切片关键词：涨知识、干货、学到了""",

    "knowledge_debate": """【场景约束：观点辩论连线】
- 核心目标：围绕有争议的话题展开理性辩论
- 话题方向：社会争议话题、价值观碰撞、行业不同看法
- 互动节奏：针锋相对但有风度，用事实和逻辑说话
- 禁忌：不人身攻击、不极端化、不涉及政治敏感话题
- 切片关键词：辩论、观点、犀利分析""",

    "knowledge_career": """【场景约束：职业揭秘连线】
- 核心目标：揭秘各行各业的真实内幕和奇葩经历
- 话题方向：职业经历、行业内幕、奇葩同事、职场潜规则
- 互动节奏：悬念式展开，细节丰富，真实感强
- 禁忌：不泄露真实公司和个人隐私
- 切片关键词：揭秘、内幕、真实经历""",

    # ── 第三组：情感与关系类 ──
    "emotion_love": """【场景约束：恋爱婚姻连线】
- 核心目标：解决两性情感困惑，引发观众共鸣
- 话题方向：恋爱技巧、婚姻经营、分手挽回、情感陷阱
- 互动节奏：先倾听→再共情→然后给建议→最后升华
- 禁忌：不鼓励极端行为、不教唆分离
- 切片关键词：情感、恋爱、破防""",

    "emotion_family": """【场景约束：亲情家庭连线】
- 核心目标：处理家庭关系问题，引发深度共鸣
- 话题方向：婆媳矛盾、亲子教育、家族纠纷、赡养问题
- 互动节奏：温和但有立场，先理解各方再给建设性意见
- 禁忌：不煽动家庭对立、不鼓励断绝关系
- 切片关键词：家庭、催泪、共鸣""",

    "emotion_friendship": """【场景约束：友情社交连线】
- 核心目标：处理朋友、同事、社交关系问题
- 话题方向：友情破裂、职场人际、社交恐惧、被孤立
- 互动节奏：共情为主，分享经验，给实用建议
- 禁忌：不鼓励报复行为
- 切片关键词：朋友、社交、真实""",

    # ── 第四组：才艺与展示类 ──
    "talent_performance": """【场景约束：才艺表演连线】
- 核心目标：展示才艺+连线互动，让观众享受表演
- 话题方向：点歌献唱、即兴创作、才艺教学、合作表演
- 互动节奏：表演为主，对话为辅，张弛有度
- 禁忌：不涉及版权争议内容
- 切片关键词：才艺、惊艳、点歌""",

    "talent_encouragement": """【场景约束：暖心鼓励连线】
- 核心目标：给处于低谷的连线者以力量和温暖
- 话题方向：鼓励低谷中的人、分享励志故事、传递正能量
- 互动节奏：先倾听陪伴→再共情理解→然后给予力量→最后温暖收尾
- 禁忌：不说教、不鸡汤、不弱化对方的痛苦
- 切片关键词：感动、励志、正能量""",
}

# ── 向后兼容：旧 key 映射到新场景 ──
SCENE_TYPE_PROMPTS["entertainment"] = SCENE_TYPE_PROMPTS["entertainment_comedy"]
SCENE_TYPE_PROMPTS["talent"] = SCENE_TYPE_PROMPTS["talent_performance"]
SCENE_TYPE_PROMPTS["emotional"] = SCENE_TYPE_PROMPTS["emotion_love"]

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

    v2 = persona.language_style_v2
    if v2:
        parts.append("")
        parts.append("【主播语言风格 — 精细约束】")
        parts.append(f"- 反问频率：{v2.get('rhetorical_question_freq', 0)}/10")
        parts.append(f"- 打断倾向：{v2.get('interrupt_tendency', 0)}/10")
        parts.append(f"- 用词尖锐度：{v2.get('sharpness', 0)}/10")
        parts.append(f"- 自黑倾向：{v2.get('self_deprecation', 0)}/10")
        parts.append(f"- 幽默类型：{v2.get('humor_type', '未识别')}")

        parts.append("")
        parts.append("【主播节奏模式】")
        parts.append(f"- 语速：{v2.get('pace', '中')}")
        parts.append(f"- 最长停顿：{v2.get('max_pause_seconds', '-')}秒（在反转前停顿）")
        parts.append(f"- 抢话频率：{v2.get('grab_floor_freq', 0)}/10")
        parts.append(f"- 单次发言长度：{v2.get('monologue_length', '中')}")

        parts.append("")
        parts.append("【主播情绪模式】")
        parts.append(f"- 共情方式：{v2.get('empathy_style', '未识别')}")
        parts.append(f"- 情绪波动幅度：{v2.get('emotional_volatility', 0)}/10")
        triggers = v2.get('emotional_triggers') or []
        parts.append(f"- 情绪触发点：{'、'.join(triggers) if triggers else '无明显触发点'}")

        parts.append("")
        parts.append("【主播内容偏好】")
        domains = v2.get('metaphor_domains') or []
        parts.append(f"- 比喻来源：{'、'.join(domains) if domains else '无明显偏好'}")
        topics = v2.get('topic_preferences') or []
        parts.append(f"- 话题偏好：{'、'.join(topics) if topics else '无特别偏好'}")
        parts.append(f"- 金句密度：{v2.get('punchline_density', 0)}/10")

        parts.append("")
        parts.append("【主播口头禅功能】")
        parts.append(f"- 开场：{v2.get('opening_phrase') or '未识别'}")
        parts.append(f"- 转折：{v2.get('transition_phrase') or '未识别'}")
        parts.append(f"- 收尾：{v2.get('closing_phrase') or '未识别'}")
    elif persona.language_style:
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


def _build_lingo_context(persona: Persona) -> str:
    """构建 lingo_map 替换词表上下文，注入到 Prompt 中指导生成。"""
    lm = persona.lingo_map
    if not lm:
        return ""

    parts = ["【主播专属词汇表 — 必须在对话中使用以下替换】"]
    parts.append("以下词语是该主播的习惯用语，生成台词时请直接使用右侧词语，不要使用左侧的常规表达：")
    for src, dst in lm.items():
        parts.append(f'  - 说"{dst}"，不说"{src}"')
    parts.append("重要：这些替换词是主播个人风格的核心标识，必须自然融入台词中。")
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


ROLE_TYPE_LABELS = {
    "anchor": "主播",
    "caller": "连线人",
    "extra": "群演",
}

PERSPECTIVE_LABELS = {
    "first_person_experience": "第一人称亲身经历（用自己的视角讲述亲身经历）",
    "first_person_participant": "第一人称参与（作为事件的参与者讲述）",
    "third_person": "第三视角客观讲述（以旁观者角度讲述）",
}


def _build_director_section(
    director_roles: list[dict] | None,
    director_acts: list[dict] | None,
) -> str:
    """Build the director constraint prompt section."""
    if not director_roles and not director_acts:
        return ""

    parts = ["【编导模式 - 剧情约束 - 最高优先级】"]
    parts.append("以下是由编导设定的剧情框架。脚本必须严格在此框架内完成，但允许角色在框架内有适度的情绪发挥和自然对话。")

    # ── Roles ──
    if director_roles:
        parts.append("")
        parts.append("角色设定")
        for r in director_roles:
            role_label = ROLE_TYPE_LABELS.get(r["role_type"], r["role_type"])
            line = f"- [{role_label}] {r['name']}"
            if r.get("position"):
                line += f"（{r['position']}）"
            if r.get("function"):
                line +=f" — 分工：{r['function']}"
            parts.append(line)
            if r["role_type"] == "anchor":
                parts.append(f"  → 使用其绑定的AI仿生人设的口吻、节奏和语言风格。如果绑定了 persona_id，使用该人设的所有特征（口头禅、叙事模式、18维风格等）。")
            elif r["role_type"] == "caller":
                if r.get("storyline"):
                    parts.append(f"  → 故事线：{r['storyline']}")
                if r.get("perspective"):
                    p_label = PERSPECTIVE_LABELS.get(r["perspective"], r["perspective"])
                    parts.append(f"  → 叙事视角：{p_label}")
            elif r["role_type"] == "extra":
                if r.get("storyline"):
                    parts.append(f"  → 背景信息：{r['storyline']}")

    # ── Acts ──
    if director_acts:
        parts.append("")
        parts.append("剧情大纲")
        parts.append("剧本必须按以下麦序结构组织对话：")
        for i, a in enumerate(director_acts):
            participants = "、".join(a.get("participants", []))
            parts.append(f"{'第一' if i == 0 else '第二' if i == 1 else '第三' if i == 2 else '第四' if i == 3 else f'第{i+1}'}麦：{a['title']} — {a['task']}（参与者：{participants}）")

    parts.append("")
    parts.append("重要规则")
    parts.append("- 每麦的开头标明【{title}】，然后展开对话")
    parts.append("- 每麦必须完成指定的剧情任务")
    parts.append("- 角色之间的对话要自然流畅，不能生硬地推进剧情")
    parts.append("- 主播角色可以使用其标志性的口头禅和叙事模式")
    parts.append("- 连线人和群演角色应严格基于其故事线和叙事视角发言")

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
        topic: str | None = None,
        required_lines: list[str] | None = None,
        db: AsyncSession | None = None,
        user_id: uuid.UUID | None = None,
        director_roles: list[dict] | None = None,
        director_acts: list[dict] | None = None,
        custom_tone: str | None = None,
    ) -> dict:
        own_session = db is None
        if own_session:
            db = async_session_factory()

        tone_uuid: uuid.UUID | None = None

        try:
            if custom_tone:
                # Custom tone: skip tone_id lookup, use a dummy tone
                class _DummyTone:
                    core_rules = custom_tone
                    forbidden_topics = ""
                    is_active = True
                tone = _DummyTone()
            else:
                tone_uuid = uuid.UUID(tone_id)
                tone = await db.get(RoomTone, tone_uuid)
                if not tone or not tone.is_active:
                    raise ValueError(f"RoomTone not found or inactive: {tone_id}")

            persona_uuid = uuid.UUID(persona_id)
            persona = await db.get(Persona, persona_uuid)
            if not persona or not persona.is_active:
                raise ValueError(f"Persona not found or inactive: {persona_id}")

            persona_context = _build_persona_context(persona)
            narrative_context = _build_narrative_context(persona)
            lingo_context = _build_lingo_context(persona)

            # Build narrative model section (injected right after persona context)
            narrative_model_section = ""
            nm = persona.narrative_model
            if nm and nm.get("completeness_score", 0) >= 30:
                units_text = ""
                for u in nm.get("narrative_units", []):
                    steps = " → ".join(u.get("steps", []))
                    units_text += f"\n  - {u.get('name', '')}（{u.get('usage_frequency', '')}）：{steps}"
                narrative_model_section = (
                    f"【该主播的专属叙事模式 — 必须严格遵循】\n"
                    f"- 开场方式：{nm.get('opening_style', '未知')}\n"
                    f"- 反转时机：{nm.get('reversal_timing', '未知')}\n"
                    f"- 节奏特征：{nm.get('rhythm_summary', '未知')}\n"
                    f"- 常用叙事单元（请尽量遵循）：{units_text}\n"
                    f"- 请务必模仿以上叙事模式生成脚本，使脚本听起来像是该主播本人的作品。"
                )

            # Combine all persona-related context into one strong block
            persona_full_context = "\n\n".join(filter(None, [
                persona_context,
                narrative_context,
                narrative_model_section,
                lingo_context,
            ]))

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
                room_tone_rules=custom_tone or tone.core_rules,
                room_tone_forbidden="" if custom_tone else (tone.forbidden_topics or "无特殊禁止话题"),
                persona_context=persona_full_context,
                persona_narrative_context="",
                emotion_curve_instruction=emotion_curve_instruction,
                hot_topic_instruction=hot_topic_instruction,
                scene_type_instruction=scene_type_instruction,
                caller_enhancement_instruction=caller_enhancement_instruction,
            )

            logger.info(
                "[PersonaContext] persona=%s, v2=%s, narrative_model=%s, lingo_map=%d, context_len=%d",
                persona.name,
                bool(persona.language_style_v2),
                bool(nm),
                len(persona.lingo_map or {}),
                len(persona_full_context),
            )

            # Inject director constraints (highest priority, at top of prompt)
            director_section = _build_director_section(director_roles, director_acts)
            if director_section:
                base_prompt = director_section + "\n\n" + base_prompt

            # Inject topic and required lines
            topic_section = ""
            if topic:
                topic_section = f"\n【话题与爆点约束】\n- 本次连线的核心话题是：{topic}\n- 脚本中的所有对话必须围绕此话题展开，不得偏题"
                if required_lines:
                    lines_text = "\n".join(f"  {i+1}. {line}" for i, line in enumerate(required_lines))
                    topic_section += f"\n- 以下句子或场景必须出现在对话中（标记为 is_highlight=true）：\n{lines_text}\n- 每条爆点应自然融入对话，不要生硬插入"
            if topic_section:
                base_prompt = base_prompt.rstrip() + topic_section

            guest_desc = self._build_guest_desc(guest_config)

            strategy_section = await self._retrieve_relevant_strategies(
                tone_context=tone.core_rules,
                persona_context=persona_context,
                guest_context=guest_desc,
            )
            if strategy_section:
                base_prompt = base_prompt.rstrip() + "\n\n" + strategy_section

            logger.info("[ScriptGen] Final prompt length: %d chars, persona=%s, scene=%s",
                        len(base_prompt), persona.name, scene_type)

            if multi_version:
                return await self._generate_multi_version(
                    base_prompt, guest_desc, tone_uuid, persona_uuid,
                    emotion_curve, strategy_mix, db, user_id,
                    lingo_map=persona.lingo_map or {},
                )

            result = await self._call_deepseek(base_prompt, guest_desc, temperature=0.8)

            # Ensure dialogues is always a list
            raw_dialogues = result.get("dialogues") or []
            result["dialogues"] = raw_dialogues

            # Apply lingo_map replacement after generation
            lingo_map = persona.lingo_map or {}
            if lingo_map:
                for d in result.get("dialogues", []):
                    t = d.get("text", "")
                    for src, dst in lingo_map.items():
                        t = t.replace(src, dst)
                    d["text"] = t

            full_text = " ".join(d.get("text", "") for d in result.get("dialogues", []))
            compliance_result = await self._check_compliance(full_text)
            highlights = self._extract_highlights(result.get("dialogues", []))
            word_count = len(full_text)

            script_project = ScriptProject(
                title=result.get("title", "未命名脚本"),
                tone_id=tone_uuid,
                persona_id=persona_uuid,
                script_content={**result, "custom_tone": custom_tone} if custom_tone else result,
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
                "dialogues": raw_dialogues,
                "compliance": compliance_result,
                "highlights": highlights,
                "word_count": word_count,
                "emotion_curve_actual": result.get("emotion_curve_actual") or [],
                "overall_style_note": result.get("overall_style_note") or "",
            }
        finally:
            if own_session:
                await db.close()

    async def _generate_multi_version(
        self, base_prompt: str, guest_desc: str,
        tone_uuid, persona_uuid,
        emotion_curve, strategy_mix, db, user_id=None,
        lingo_map: dict | None = None,
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
            # Apply lingo_map replacement
            if lingo_map:
                for d in result.get("dialogues", []):
                    t = d.get("text", "")
                    for src, dst in lingo_map.items():
                        t = t.replace(src, dst)
                    d["text"] = t
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

    def _build_guest_desc(self, guest_config: dict | list) -> str:
        if isinstance(guest_config, list):
            if len(guest_config) <= 1:
                return self._build_guest_desc(guest_config[0] if guest_config else {})

            parts = ["请为以下多个角色生成一段完整的直播对话脚本："]
            for i, gc in enumerate(guest_config, 1):
                role_lines = []
                if gc.get("name"):
                    role_lines.append(f"名称：{gc['name']}")
                if gc.get("personality") or gc.get("occupation"):
                    role_lines.append(f"身份：{gc.get('personality', '')}{('，' + gc['occupation']) if gc.get('occupation') else ''}")
                if gc.get("core_issue"):
                    role_lines.append(f"核心问题：{gc['core_issue']}")
                if gc.get("perspective"):
                    pmap = {"first_person_experience": "第一人称亲身经历", "first_person_participant": "第一人称参与", "third_person": "第三视角客观讲述"}
                    role_lines.append(f"叙事视角：{pmap.get(gc['perspective'], gc['perspective'])}")
                parts.append(f"\n角色{i}：\n" + "\n".join(f"  {l}" for l in role_lines))

            parts.append("\n重要：脚本中每个角色必须用自己的名字发言，不得混淆。")
            return "\n".join(parts)

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
        try:
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
        except Exception as e:
            logger.warning("DeepSeek script generation failed, returning fallback: %s", e)
            # Extract topic from user_message if present
            topic = ""
            if "核心话题" in (system_prompt + user_message):
                import re as _re
                m = _re.search(r"核心话题[是为：:]+\s*(.+?)[\n。]", system_prompt + user_message)
                if m:
                    topic = m.group(1).strip()
            return _build_fallback_script(topic or "连线互动")

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


def _build_fallback_script(topic: str) -> dict:
    """Return a generic script template when DeepSeek is unavailable."""
    dialogues = [
        {"turn": 1, "speaker": "主播", "text": f"欢迎来到直播间！今天我们来聊聊{topic}，这个话题很多人都在关注。", "emotion": "热情", "is_highlight": False},
        {"turn": 2, "speaker": "连线观众", "text": f"主播你好，我对{topic}特别感兴趣，能说说你的看法吗？", "emotion": "好奇", "is_highlight": False},
        {"turn": 3, "speaker": "主播", "text": f"好问题！关于{topic}，我觉得首先得从根本上看这个问题……", "emotion": "认真", "is_highlight": False},
        {"turn": 4, "speaker": "连线观众", "text": "确实是这样，我之前没从这个角度想过。", "emotion": "认同", "is_highlight": False},
        {"turn": 5, "speaker": "主播", "text": "对吧？而且你往下想，这背后其实还有一个更深层的原因……", "emotion": "引导", "is_highlight": True, "highlight_title": "反转引入"},
        {"turn": 6, "speaker": "连线观众", "text": "什么原因？快说说！", "emotion": "期待", "is_highlight": False},
        {"turn": 7, "speaker": "主播", "text": "其实就是——大部分人只看到了表面，没看到本质。关于{topic}，真正重要的是……", "emotion": "激动", "is_highlight": True, "highlight_title": "核心观点"},
        {"turn": 8, "speaker": "连线观众", "text": "哇，说得太对了！我完全被说通了。", "emotion": "惊喜", "is_highlight": False},
        {"turn": 9, "speaker": "主播", "text": "所以兄弟们，记住这个道理。喜欢主播说的点个关注，咱们下期继续聊！", "emotion": "收尾", "is_highlight": False},
        {"turn": 10, "speaker": "连线观众", "text": "关注了关注了，下次一定来！", "emotion": "热情", "is_highlight": False},
    ]
    return {
        "title": f"[降级] {topic} — 通用连线模板",
        "dialogues": dialogues,
        "emotion_curve_actual": ["开场:热情", "发展:认真", "高潮:激动", "收尾:温暖"],
        "overall_style_note": "AI 服务暂时不可用，此为降级生成的通用脚本模板，请稍后重试获取定制脚本",
        "degraded": True,
    }


script_generator = ScriptGenerator()
