# -*- coding: utf-8 -*-
"""拆书步骤 5 — 逐集生成 (创作层 + 编辑层两层契约) + 确认 + 级联重跑.

拆包自 orchestrator.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import BookProject, Episode
from app.services.book_service.creation_common import (
    _FALLBACK_BASE,
    _PERSONA_ENDING,
    _PERSONA_IDENTITY,
    _llm,
    _parse_json,
    _scan_occult_quotes,
    elastic_labels,
    source_context,
    validate_script,
)
from app.services.book_service.creation_steps import _l0_facing
from app.services.book_service.distiller import load_book_rules
from app.services.llm_service import _load_prompt_template

logger = logging.getLogger(__name__)

__all__ = ["generate_episode", "confirm_episode", "rerun_cascade", "editorial_pass"]

# 2026-08-23: 编辑层口语化 — 生成层专注创作, 编辑层专职改口语 (身份激活真人口播语感).
# 两层契约: 创作层用 ⟦⟧ 标记原书原话 → 编辑层见标记一字不改 → 输出清标记.
_QUOTE_MARK_RE = re.compile(r"⟦(.*?)⟧")


def editorial_pass(script: str) -> str:
    """编辑层 (2026-08-23): 专职口语化, 身份=抖音口播稿审核编辑.

    只改表达, 不动内容; ⟦...⟧ 内原书原话一字不改 (删标记保留原话); 输出不得含 ⟦⟧.
    失败回退初稿 (编辑层是增强不是拦路).
    """
    sys_p = (
        "你是抖音拆书口播稿的资深审核编辑，经手过几百条从口播到爆款的稿子。\n"
        "你的工作：把初稿改写成真人说话的样子——让人听不出是 AI 写的。\n"
        "【铁律：只改表达，不动内容】\n"
        "1. 稿中 ⟦…⟧ 包裹的是原书原话/金句，一字不能改（输出时删掉⟦⟧、保留原话）。\n"
        "2. 保留：观点/结构/段落/时间标签【x秒-y秒｜段名】/书名/人设台词(我是静…)/原书术语概念名"
        "(如\"人生坐标\"\"儿童自我状态\"\"父母自我状态\"等, 一律不得替换成其他说法).\n"
        "3. 只改：书面腔→口语、绕口→顺口、空泛→具体；删除写作指令(如“最后留一个生活钩子”这类)。\n"
        "【口语化规则】\n"
        "- 短句优先，一句一意，像说话不像作文\n"
        "- 书面腔改口语（“从不敢说不”→“那个不字反反复复没说出口”）\n"
        "- 比喻用中国人熟悉的日常意象（长命锁从喜庆变枷锁）\n"
        "- 反讽/强调词保留引号\n"
        "输出：只输出改完的完整稿子（不得含⟦⟧），不要解释。"
    )
    try:
        out = _llm().chat(sys_p, script, model="pro", temperature=0.5)
    except Exception as exc:
        logger.warning("[book] 编辑层失败, 回退初稿: %s", exc)
        return script
    out = _QUOTE_MARK_RE.sub(r"\1", out)  # 兜底清 ⟦⟧ 残留
    return out or script


def _relations_block(book: BookProject) -> str:
    """facing-relations 注入 (2026-08-23): 跨章人物图谱 + 概念论证位置 + 作者意图.

    解决 L0 理解欠缺: 獾是谁/核心框架/全书意图 — 逐集生成不再靠猜.
    """
    try:
        from app.services.book_service.l0 import _l0_dir
        p = _l0_dir(book.book_title) / "facing" / "facing-relations.json"
        if not p.exists():
            return ""
        r = json.loads(p.read_text(encoding="utf-8"))
        lines: list[str] = []
        chs = r.get("characters") or []
        if chs:
            lines.append("【本书人物关系 · 首次出现须用此身份介绍】")
            for c in chs:
                lines.append(f"- {c.get('name', '')}：{c.get('identity', '')}（{c.get('relation_to_hero', '')}）。"
                             f"{str(c.get('role_in_book', ''))[:50]}")
        cr = r.get("concept_roles") or []
        if cr:
            lines.append("【核心概念 · 论证位置】")
            for c in cr:
                lines.append(f"- {c.get('name', '')}（{c.get('position_in_argument', '')}）："
                             f"{str(c.get('why_important', ''))[:50]}")
        ai = r.get("author_intent") or {}
        if ai:
            lines.append(f"【作者意图】核心问题：{ai.get('core_question', '')}；"
                         f"框架：{str(ai.get('framework', ''))[:70]}；读者转变：{str(ai.get('reader_journey', ''))[:50]}")
        return "\n" + "\n".join(lines) + "\n" if lines else ""
    except Exception:
        return ""


def _douban_block(book: BookProject) -> str:
    """豆瓣真实读者反应注入 (2026-08-23; ⚠️ 2026-08-24 暂停).

    ⚠️ 用户验收发现参与生成后"不对味儿" — 豆瓣读者语言风格渗入稿子, 冲淡书本身的
    讲述语感. 数据保留 input_json.douban (爬虫/落库/前端展示不回滚), 仅停止注入逐集生成;
    待重新设计使用方式 (如仅槽点规避/人工参考) 后再启用: 删掉下方 early-return 即恢复.
    """
    return ""
    d = (book.input_json or {}).get("douban") or {}
    if not d:
        return ""
    lines: list[str] = ["【豆瓣真实读者反应 · 共鸣/槽点/深度】"]
    for c in (d.get("comments") or [])[:6]:
        lines.append(f"- [短评{c.get('votes', 0)}赞] {str(c.get('text', ''))[:60]}")
    for v in (d.get("reviews") or [])[:2]:
        lines.append(f"- [书评·{v.get('votes', 0)}有用]《{v.get('title', '')}》{str(v.get('summary', ''))[:80]}")
    lines.append("读者槽点(康复太快/对读过的太浅/结局现实)做稿时规避或回应, 不硬拗。")
    return "\n" + "\n".join(lines) + "\n"


def generate_episode(db: Session, ep: Episode) -> Episode:
    book = ep.book
    inp = book.input_json or {}
    labels = elastic_labels(ep.target_duration_sec)
    label_table = "\n".join(f"【{a}-{b}秒｜{n}】" for a, b, n in labels)
    char_hints = "、".join(f"【{n}】约{int((b - a) * 4.7)}字" for a, b, n in labels)

    prev = next((e for e in book.episodes if e.ep_index == ep.ep_index - 1), None)
    coverages = [e.coverage_json or [] for e in book.episodes if e.ep_index < ep.ep_index]
    # ── 基底: 静读书人设模板 (config/jingshu-book.txt, 2026-08-20 复刻老谭科技7层v2) ──
    base = _load_prompt_template("jingshu-book")
    if not base or len(base) < 200:
        logger.warning("[book] config/jingshu-book.txt 缺失或过短, 回退内置兜底基底")
        base = _FALLBACK_BASE
    # ── 附加指令: 动态硬数据, 优先级高于模板 ──
    sys_p = (
        base
        + "\n\n【本集附加指令 · 优先级高于模板】\n"
        + f"1. 本集：第{ep.ep_index}集，目标时长 {ep.target_duration_sec:.0f}s，主题：{ep.title}。\n"
        + f"2. 六段弹性标签（逐字保留，作为段落标题）：\n{label_table}\n"
        + f"3. 各段参考字数（4.7 字/秒）：{char_hints}。\n"
        + "4. 字数基线（硬校验）：全文正文严格≤3000字、推荐2800-2950字，宁短勿超。\n"
        + "5. 必须输出全部 6 个标签行，末段终点≈目标时长±10%。\n"
        + "6. 约束：书中内容≤40%，场景/类比/解读≥60%；观点须可追溯来源，"
          "严禁编造书中不存在的观点；中性表述，禁“你一定/你必须/相信我/震惊/颠覆”；"
          "3处以上日常场景化举例；第1集无回顾（该段写痛点共鸣+引入书籍），"
          "第6集收尾无预告（写系列完结语）；金句无逐字出处只转述不挂引号。"
          "不要加身份段/结尾落款（系统后处理注入）；全稿禁止任何位置出现"
          "'我是XX/我是静姐'自称——自我介绍由系统注入, 创作层只写内容本身。\n"
        + "7. 专业概念（交互分析/人生坐标/自我状态等）口播必须翻译成大白话，"
          "用宝妈/婚姻/亲子/职场的生活例子解释（“你说得好”不如“你一听就懂”），不裸甩专业术语。\n"
        + "8. 结尾抛一个生活化钩子问题（绑定夫妻矛盾/亲子拉扯/职场委屈/讨好型内耗），"
          "自然引导观众留言或追下集，不空洞求关。\n"
        + "9. 规避治疗承诺词：禁'疗愈/治疗/治愈/心理诊疗'，统一'觉察/梳理/看见/练习'；"
          "禁绝对化（最/唯一/顶级/天花板）、迷信（好运/辟邪/转运）、金融（赚钱/暴富/稳赚不赔）、引流（微信/私信我/完整版在xx）。\n"
        + "10. 正文末尾另起一段附严格 JSON 块 {\"coverage\":[str]} 列本集知识点"
          "（不计入字数），该块之后禁止再输出任何文字。\n"
    )
    # Gate B (2026-08-19): 书线合规红线注入 — 配置驱动, 规则集升版自动生效
    rules = load_book_rules()
    hr = " / ".join(v for k, v in (rules.get("high_risk_delete") or {}).items() if not k.startswith("_"))
    mr = " / ".join(v for k, v in (rules.get("medium_risk_rewrite") or {}).items() if not k.startswith("_"))
    mn = " / ".join(v for k, v in (rules.get("minor_risk_framing") or {}).items() if not k.startswith("_"))
    safe = (rules.get("safe_formulas") or ["这本书提出……（书中观点）"])[:2]
    sys_p += (
        f"\n平台合规红线(书线): 禁[{hr}]; 转述改写[{mr}]; 逻辑红线[{mn}]; "
        f"书中观点一律视角限定, 可用{' / '.join(safe)}; L0 精华若有「合规备注」节必须遵守。"
    )
    # 2026-08-21 Gate B 强化: 关键规则单独成行硬约束 (整行拼接权重低, 逐条必守)
    def _rule_text(group: str, key: str) -> str:
        v = (rules.get(group) or {}).get(key)
        return v if isinstance(v, str) else ""
    hard_lines = []
    abs_claim = _rule_text("medium_risk_rewrite", "absolute_claims")
    qual_disc = _rule_text("medium_risk_rewrite", "qualification_disclaimer")
    map_ban = _rule_text("minor_risk_framing", "reality_mapping_ban")
    heal_ban = _rule_text("minor_risk_framing", "healing_vocab_ban")
    scene = _rule_text("minor_risk_framing", "audience_scene")
    abs_ban = _rule_text("minor_risk_framing", "absolute_claims_ban")
    prom_ban = _rule_text("minor_risk_framing", "promise_ban")
    super_ban = _rule_text("minor_risk_framing", "superstition_ban")
    fin_ban = _rule_text("minor_risk_framing", "finance_claims_ban")
    ext_ban = _rule_text("minor_risk_framing", "external_link_ban")
    if abs_claim:
        hard_lines.append(f"1. 书中观点限定: {abs_claim}")
    if qual_disc:
        hard_lines.append(f"2. 资质边界: {qual_disc}")
    if map_ban:
        hard_lines.append(f"3. 不映射现实: {map_ban}")
    if heal_ban:
        hard_lines.append(f"4. 禁治疗承诺词: {heal_ban}")
    if scene:
        hard_lines.append(f"5. 受众场景: {scene}")
    if abs_ban:
        hard_lines.append(f"6. 禁绝对化用语: {abs_ban}")
    if prom_ban:
        hard_lines.append(f"7. 禁虚假承诺: {prom_ban}")
    if super_ban:
        hard_lines.append(f"8. 禁迷信用语: {super_ban}")
    if fin_ban:
        hard_lines.append(f"9. 禁金融承诺: {fin_ban}")
    if ext_ban:
        hard_lines.append(f"10. 禁站外引流: {ext_ban}")
    if hard_lines:
        sys_p += "\n【合规硬约束 · 逐条必守(优先级最高, 与上面汇总同源)】\n" + "\n".join(hard_lines)
    # 2026-08-22: 全系统统一限流词注入 (config/compliance_common.json — 拆书/新闻线共用)
    from app.services.compliance import build_redline_prompt
    sys_p += "\n" + build_redline_prompt()
    # 2026-08-23: 口播稿质量标准 — 系统性防 5 类硬伤 + 口语化示范 (用户验收迭代 v2)
    sys_p += (
        "\n【口播稿质量标准 · 成片前硬性自查】\n"
        "1. 口语化: 像真人聊天, 禁书面腔/AI腔. 反例→正例:\n"
        "   · \"你从不敢说不\" → 那个\"不\"字, 反反复复没说出口\n"
        "   · \"同事推活, 你笑着说好\" → 满心的不情愿, 也还是应了下来\n"
        "   · \"丈夫一皱眉, 你立刻检讨自己\" → 丈夫一皱眉, 你在自己身上找原因\n"
        "   · \"成年后一遇冲突就想道歉\" → 只能道歉\n"
        "   · \"就像一套穿了太久的紧身衣\" → 就像小时候戴的长命锁, 小时候是喜庆, 长大却成了枷锁\n"
        "   · \"这值得花几分钟好好看一看\" → 这值得花几分钟好好聊聊\n"
        "2. 忠实原文: 引用书中台词/金句/对话必须与原文一字不差, 且用 ⟦⟧ 包裹(如 ⟦必须完成的事情，唯有靠他自己才能完成⟧) "
        "— ⟦⟧ 是原话保护标记, 编辑层见标记一字不改; 禁改写/概括/编造; 拿不准就不引.\n"
        "3. 角色连续性: 书中人物首次出现必须一句话介绍身份(是谁、什么关系), 不能直接进对话.\n"
        "4. 生活常识: 场景/对话符合真实生活(孩子作业难是闹不是哭; 丈夫说\"谢谢老婆\"不说\"老婆懂事\"; "
        "领导当面夸员工用\"你还挺靠谱\").\n"
        "5. 反讽引号: 反讽/语境相反义/强调词必须加中文引号(“”), 如蛤蟆\"挺热闹\"其实是假热闹 — "
        "字幕会保留引号, 不加引号就露馅. 不加引号=没读懂反讽.\n"
        "6. 禁写写作指令: 全稿只能是给观众听的话, 禁止把写作要求/提示语写进口播稿 "
        "(如\"最后留一个生活钩子\"\"这里举例\"这类绝不能出现).\n"
        "7. 段落去重: 每段讲新点, 同一概念/例子全稿只讲一次; 后段不得重复前段已讲的定义或场景.\n"
        "8. 比喻贴语感: 比喻须用中国人熟悉的日常意象, 与论证严格对应.\n"
    )
    # 2026-08-25: 女性目标人群语感法则 (用户对第2集逐句验收提炼) — 教判断标准, 不是词表:
    # 同一个意思换表达, 观众感受完全不同; 表达可变, 法则不变.
    sys_p += (
        "\n【女性目标人群语感 · 人设定律】(观众=25-50岁女性, 创作前先读懂再动笔)\n"
        "总纲A · 人群跨度: 25岁和45岁的女性共用这套稿. 措辞必须落在'全跨度大众共识', "
        "只对年轻段有效的'怯懦/小女生'表达, 45岁观众看着就不是自己 — 取公约数, 不取极端.\n"
        "总纲B · 人设复利: 单句改不改都过得去, 但每句都在给主播人设记账. "
        "主播的位置是'清醒的共情者'——看得懂讨好, 但不活成讨好. 台词把'懂事退让'写多了, "
        "人设就从'帮你说话的明白人'滑向'受气包闺蜜', 长期掉粉.\n"
        "法则1 · 心理原声化: 人物反应写脑内第一人称原声, 不写作者的心理概括. "
        "反例→正例: '马上在自己身上找原因' → 第一反应是'我又怎么了'.\n"
        "法则2 · 自我合理化话术: 讨好者不说'我讨好', 说'我顾家'. 行为要用当事人给自己找的台阶呈现. "
        "反例→正例: '把家务全包了' → '顺理成章地调整了生活重心'; "
        "'怪自己要求太高' → '怪自己太讲究形式'. 注意: 自责只能落在'我可以不计较'(形式主义/想开了), "
        "绝不落在'我不该有要求'(要求太高/太贪心) — 后者暗示女性正常诉求是过错, 冒犯观众.\n"
        "法则3 · 憋屈剂量控制: 一个场景示弱只给一层, 语境已立住就不再叠加. "
        "反例→正例: 忘了纪念日这个语境已经够憋屈, 口边的话是'没关系'就够了, "
        "再加一句'你忙'就成了叠层示弱 — 观众的同情有配额, 超额就从共鸣变反感.\n"
        "法则4 · 大众词优先于病理词: 台词要落在'大多数女性真说得出口的话'. "
        "反例→正例: 职场被抢功, 口边是'没事'(强装大度, 大众常态), 不是'没关系'(认怂退让, 小众). "
        "'强装大度'人人有共鸣, '怯懦'只有少数人对号入座.\n"
        "法则5 · 歧义审计: 逐句自查'这个词在女性读者耳朵里有没有第二种解读'. "
        "反例→正例: '随叫随到'有歧义误读, 换'恨不得24小时在线'.\n"
    )
    if ep.ep_index == 1 and rules.get("opening_disclaimer"):
        # 2026-08-21 免责视觉化: 免责不上口播(省开篇黄金时间), 由成片首帧右上角字幕呈现
        sys_p += ("\n强制免责(视觉化, 不上口播): 系统会在成片首帧画面右上角加免责字幕"
                  "('以下仅为这本书的作者观点…'), 口播稿不要念免责声明, "
                  "把开篇 0-3 秒黄金时间留给痛点钩子。")
    # 2026-08-22 逐集按单元消费: 从 roadmap 的 unit_id 取对应主题单元素材 (core_claim/概念/共鸣/类比/敏感),
    # 评论按 unit_id 过滤; 用单元概念在 L0 章节定位 quotes/cases.
    unit_block = ""
    unit_comments = inp.get("comment_layer") or []
    l0_unit = None
    if ep.roadmap_json and ep.roadmap_json.get("unit_id"):
        _r, units = _l0_facing(book)
        l0_unit = next((u for u in units if u.get("id") == ep.roadmap_json["unit_id"]), None)
        if l0_unit:
            unit_block = (
                f"\n【本集主题单元 · 素材】(优先级高于全书输入)\n"
                f"- 单元:{l0_unit.get('id')}《{l0_unit.get('title')}》\n"
                f"- 核心主张:{l0_unit.get('core_claim', '')}\n"
                f"- 概念:{','.join(str(c) for c in (l0_unit.get('concepts') or []))}\n"
                f"- 读者共鸣:{';'.join(str(r) for r in (l0_unit.get('reader_resonance') or []))}\n"
                f"- 类比钩子:{';'.join(str(a) for a in (l0_unit.get('analogy_hooks') or []))}\n"
                + (f"- 敏感:{l0_unit['sensitive'].get('level', '')} 安全讲法:{l0_unit['sensitive'].get('safe_angle', '')}"
                   if l0_unit.get("sensitive") else "")
            )
            unit_comments = [c for c in unit_comments if c.get("unit_id") == l0_unit["id"]]
    # L0 章节定位 (单元概念命中 → 该章 quotes/cases 注入)
    unit_quotes_cases = ""
    try:
        from app.services.book_service.l0 import _l0_dir
        l0_path = _l0_dir(book.book_title) / "l0-chapter-v1.json"
        if l0_path.exists() and l0_unit:
            l0 = json.loads(l0_path.read_text(encoding="utf-8"))
            unit_concepts = set(str(c) for c in (l0_unit.get("concepts") or []))
            hit_ch = [ch for ch in l0.get("chapters", [])
                      if any(str(c.get("name", "")) in unit_concepts or
                             any(str(c.get("name", "")) == uc for uc in unit_concepts)
                             for c in (ch.get("concepts") or []))]
            qs = [q for ch in hit_ch for q in (ch.get("quotes") or [])][:6]
            cs = [c for ch in hit_ch for c in (ch.get("cases") or [])][:4]
            if qs or cs:
                unit_quotes_cases = "\n【本单元书内金句/案例】\n"
                if qs:
                    unit_quotes_cases += "金句: " + " / ".join(str(q.get("text", ""))[:60] for q in qs) + "\n"
                if cs:
                    unit_quotes_cases += "案例: " + " / ".join(str(c.get("desc", ""))[:60] for c in cs) + "\n"
            # 2026-08-22: 源头书注入 — 本书相关章节引用的书/理论 (reference_library 消除孤岛, 逐集内容关联)
            refs = []
            for ch in hit_ch:
                for r in ch.get("references") or []:
                    nm = str(r.get("name", "")).strip()
                    if nm and nm not in refs:
                        refs.append(nm)
            if refs:
                unit_quotes_cases += f"\n【本书相关章节引用的源头书/理论(可自然带出, 不硬塞)】{', '.join(refs[:5])}\n"
            # 2026-08-22: 相关人物/实体注入 — 消除 entities 孤岛 (讲情节/案例时自然称呼)
            ents = []
            for ch in hit_ch:
                for e in (ch.get("entities") or []):
                    nm = str(e).strip()
                    if nm and nm not in ents:
                        ents.append(nm)
            if ents:
                unit_quotes_cases += f"\n【本单元相关人物/实体(讲情节或案例时自然带出, 勿平铺罗列)】{', '.join(ents[:5])}\n"
    except Exception:
        pass

    # E1 系列预告注入 (2026-08-22): 已知全集数+各集主题 → E1 稿开头预告整体系列, 引导关注追更
    series_inject = ""
    if ep.ep_index == 1:
        prev_txt = (ep.roadmap_json or {}).get("系列预告") or ""
        if not prev_txt:
            others = [f"第{e.ep}集《{e.title}》" for e in sorted(book.episodes, key=lambda x: x.ep_index) if e.ep > 1]
            if others:
                prev_txt = f"本系列共{len(book.episodes)}集：" + "、".join(others)
        if prev_txt:
            series_inject = (f"\n【系列预告 · E1 必带】本期开头用 20-30 秒预告整体系列：{prev_txt}"
                             "（引导观众关注/追更，具体不空洞，禁止'记得点赞关注'式直白求关）。\n")

    # 2026-08-22: facing-hooks 注入 (开篇钩子/结尾互动/下集预告) + kernel.why_read (E1 导读)
    hook_block = ""
    try:
        from app.services.book_service.l0 import _l0_dir
        facing_d = _l0_dir(book.book_title) / "facing"
        hooks = json.loads((facing_d / "facing-hooks.json").read_text(encoding="utf-8")).get("hooks", [])
        uid = (ep.roadmap_json or {}).get("unit_id")
        hk = next((h for h in hooks if h.get("unit_id") == uid), None) or (hooks[0] if hooks else None)
        if hk:
            parts = []
            if hk.get("opening_hook"):
                parts.append(f"开篇钩子(3秒): {hk['opening_hook']}")
            if hk.get("closing_question"):
                parts.append(f"结尾互动: 抛生活化问题引导评论→{hk['closing_question']}")
            if hk.get("next_teaser"):
                parts.append(f"下集预告: {hk['next_teaser']}")
            if parts:
                hook_block = "\n【本集钩子·design】\n" + "\n".join(parts) + "\n"
    except Exception:
        pass
    kernel_why = ""
    if ep.ep_index == 1:
        try:
            from app.services.book_service.l0 import _l0_dir
            k = json.loads((_l0_dir(book.book_title) / "facing" / "facing-kernel.json").read_text(encoding="utf-8"))
            if k.get("why_read"):
                kernel_why = f"\n【为什么值得读 · E1 导读必带】{k['why_read']}\n"
        except Exception:
            pass

    user_p = (
        f"书名：《{book.book_title}》 第{ep.ep_index}集：{ep.title}\n"
        f"本集路线图：{json.dumps(ep.roadmap_json or {}, ensure_ascii=False)}\n"
        f"全书输入：{json.dumps({k: (v or {}).get('value') for k, v in inp.items() if isinstance(v, dict)}, ensure_ascii=False)[:4000]}\n"
        + _relations_block(book)
        + _douban_block(book)
        + unit_block
        + unit_quotes_cases
        + series_inject
        + kernel_why
        + hook_block
        + f"读者反应：{json.dumps(unit_comments or [], ensure_ascii=False)[:1200]}\n"
        f"素材精华：{json.dumps(inp.get('materials') or [], ensure_ascii=False)[:1500]}\n"
        f"前序覆盖清单：{json.dumps(coverages, ensure_ascii=False)[:1500]}\n"
        + (f"上集尾部：{(prev.script_text or '')[-200:]}\n本集【回顾+引入】须与之咬合。\n" if prev and prev.script_text else "")
        + (f"\n【L0 来源节选】\n{source_context(book, cap=8000)}" if book.source_path else "")
    )
    out = _llm().chat(sys_p, user_p, model="pro", temperature=0.8)

    m = re.search(r"\{[\s\S]*\"coverage\"[\s\S]*\}\s*$", out)
    coverage: list = []
    if m:
        try:
            coverage = _parse_json(m.group(0)).get("coverage") or []
            out = out[:m.start()].rstrip()
        except Exception:
            pass

    # 硬校验: 不达标带 issues 重试一次; 灵性金句未锚定也触发重写 (2026-08-21)
    ok, issues = validate_script(out, ep.target_duration_sec)
    occult_issues = _scan_occult_quotes(out)
    if occult_issues:
        issues = list(issues) + occult_issues
        ok = False
    if not ok:
        retry = _llm().chat(
            sys_p, user_p + f"\n\n上一版问题，请修正：{'; '.join(issues)}",
            model="pro", temperature=0.6)
        m2 = re.search(r"\{[\s\S]*\"coverage\"[\s\S]*\}\s*$", retry)
        if m2:
            try:
                coverage = _parse_json(m2.group(0)).get("coverage") or coverage
                retry = retry[:m2.start()].rstrip()
            except Exception:
                pass
        out2_ok, issues2 = validate_script(retry, ep.target_duration_sec)
        if out2_ok and not _scan_occult_quotes(retry):
            out = retry
        else:
            logger.warning("[book] ep%d 硬校验二次仍不过: %s", ep.ep_index, issues2)

    # 2026-08-23: 编辑层口语化 — 生成层专注创作, 编辑层专职改口语 (身份激活真人口播语感)
    out = editorial_pass(out)

    # 人设后处理注入: 身份段放第二段末尾(钩子+回顾之后, 非段首), 固定结尾收尾
    if _PERSONA_IDENTITY not in out:
        # 第3段标签 = 第2段内容结束点 → 身份插在它前面 (钩子+回顾完成后才自报家门)
        label3 = "【%d-%d秒｜%s】" % labels[2] if len(labels) > 2 else None
        if label3 and label3 in out:
            out = out.replace(label3, _PERSONA_IDENTITY + "\n" + label3, 1)
        else:
            # 兜底: 插在第二段标签行后
            out = out.replace("【%d-%d秒｜%s】" % labels[1],
                              "【%d-%d秒｜%s】\n%s" % (*labels[1], _PERSONA_IDENTITY), 1)
    if _PERSONA_ENDING not in out:
        # 剥离模型自写的结尾收束语(照顾好自己/一起成长/下期见), 防与系统结尾重复
        import re as _re
        tail = out.rstrip()
        m = _re.search(
            r"[。！？!?\s]*(照顾好自己[^。！？]*[。！？]?|一起成长[^。！？]*[。！？]?|我们?下期见[^。！？]*[。！？]?)\s*$",
            tail,
        )
        if m and len(tail) - m.start() < 150:
            tail = tail[: m.start()].rstrip()
        out = tail + "\n" + _PERSONA_ENDING

    # 三项自检 (记录, 不阻塞)
    checks: dict[str, Any] = {}
    blob_roadmap = json.dumps(ep.roadmap_json or {}, ensure_ascii=False)
    theme = (ep.roadmap_json or {}).get("主题", "")
    checks["theme_in_script"] = bool(theme) and theme[:8] in out
    if prev:
        prev_theme = (prev.roadmap_json or {}).get("主题", "")
        checks["links_prev"] = bool(prev_theme) and prev_theme[:8] in out
    if coverage and coverages:
        flat = [c for cs in coverages for c in cs]
        dup = [c for c in coverage if c in flat]
        checks["coverage_dup"] = dup[:5]

    ep.script_text = out
    ep.coverage_json = coverage
    ep.status = "draft"
    ep.roadmap_json = {**(ep.roadmap_json or {}), "_checks": checks, "_issues": issues if not ok else []}
    db.commit()
    return ep


def confirm_episode(db: Session, ep: Episode) -> Episode:
    ep.status = "confirmed"
    if all(e.status == "confirmed" for e in ep.book.episodes):
        ep.book.status = "done"
    db.commit()
    return ep


# ── 级联重跑: 重跑 N 作废 N..6 ───────────────────────────────────
def rerun_cascade(db: Session, book: BookProject, ep_index: int) -> BookProject:
    for e in book.episodes:
        if e.ep_index >= ep_index:
            e.status = "pending"
            e.script_text = None
            e.coverage_json = []
    book.status = "writing"
    db.commit()
    return book
