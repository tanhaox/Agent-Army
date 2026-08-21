# -*- coding: utf-8 -*-
"""拆书创作编排 (2026-08-19) — 5 步 pipeline + 级联重跑 + 自检 + 硬校验.

方案: docs/拆书项目-实施方案.md §3/§3.1。
5 步: 补全(flash)【确认1】→ 评论层∥素材(flash,轻确认) → 总纲(pro)【确认2】→ 逐集(pro)【确认3】。
防幻觉: 核心四字段仅 L0/人工; L2 须佐证; 金句无逐字出处不挂引号; 总纲追溯自检。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import BookProject, Episode
from app.services.book_service.reader import read_book
from app.services.book_service.distiller import load_book_rules, GemmaClient
from app.services.llm_service import LLMService, _load_prompt_template

logger = logging.getLogger(__name__)

__all__ = [
    "complete_input", "build_comment_layer", "build_materials",
    "build_roadmap", "generate_episode", "confirm_episode", "rerun_cascade",
    "elastic_labels", "validate_script", "source_context",
]

# ── 人设后处理注入层 (P1 定稿措辞): 创作 LLM 保持中性, 身份段/结尾在此加 ──
_PERSONA_IDENTITY = "我是静姐，读透一本好书，陪你遇见更好的自己。"
_PERSONA_ENDING = "照顾好自己，让我们一起成长。我是静姐，下期见。"

# ── 灵性金句锚定扫描 (2026-08-21): 生成后确定性检查, 未锚定→触发重写 ──
# 本书/灵性主题流传广的金句, 出现必须带"书里/书中/作者"锚定, 防宿命论/向内归罪/伪科学.
_OCCULT_QUOTE_PATTERNS = [
    r"外面没有别人",
    r"凡是你抗拒的",
    r"都是[^。，]{0,14}的礼物",
    r"事件[^。，]{0,8}中性",
    r"内在[^。，]{0,8}(镜子|投射)",
    r"内在投射",
    r"爱[^。，]{0,4}喜悦[^。，]{0,4}和平",
    r"心想事成",
    r"境由心转",  # 唯心/心转断言, 须锚定书里比喻
    r"二十一天",  # 21天固定周期, 须锚定书里建议/弱化确定性
]
_ANCHOR_RE = re.compile(r"(书里|书中|作者|按照书|这本书|书里讲|书里说|书里提到|书中提出|书中记录|书中的看法)")


def _scan_occult_quotes(out: str) -> list[str]:
    """扫描未锚定书中观点的灵性金句, 返回问题清单 (每句一条).

    判定: 金句所在句(上一个句末标点到金句结束)内必须出现锚定词(书里/书中/作者/按照书等);
    跨句的'这本书'泛介绍不算锚定.
    """
    issues: list[str] = []
    for pat in _OCCULT_QUOTE_PATTERNS:
        for m in re.finditer(pat, out):
            parts = re.split(r"[。！？!?；;\n]", out[: m.end()])
            sentence = parts[-1] if parts else ""
            if not _ANCHOR_RE.search(sentence):
                issues.append(
                    f"「{m.group(0)}」需锚定书中观点——前句带'书里有一句比喻/书中提出/按照书里的看法'主语，禁作客观真理")
    return issues

# 兜底基底 (2026-08-20): config/jingshu-book.txt 缺失/过短时回退, 防管线静默崩坏.
# 精简版人设 + 六段结构说明; 附加指令/Gate B 仍由 generate_episode 动态追加.
_FALLBACK_BASE = (
    "你是\"静读书\"的拆书讲述者静姐，45岁+，已有上小学的儿子。满级情商、温柔、知性、"
    "通过分享达到精神成长。说话不端着、不卖弄、不居高临下，拒绝煽情和鸡汤腔。\n"
    "【核心任务】基于【本集输入】（书名/本集路线图/全书输入/读者反应/素材包/前序覆盖），"
    "按六段结构写一集口播稿：把这本书拆透、讲人话。\n"
    "【受众画像】抖音、小红书：25-50岁女性，希望通过阅读、听书获得成长。喜欢知识沉淀，"
    "又没有太多时间进行仔细阅读；爱听\"这本书说的，对我有什么用\"，打比方用职场/育儿/"
    "关系/深夜独处等生活场景。\n"
    "【口吻红线】普遍规律用\"咱们\"、个人建议才用\"你\"；转场极简；禁元叙述/计数预告句；"
    "比喻须与论证严格对应；温柔但不绵软——软声说硬话，观点清晰有立场。\n"
    "【拆书约束】同一引导词全篇最多1次；每句≤20字；强比喻≤3个；"
    "书中内容≤40%、场景/解读≥60%；观点须可追溯来源，书中观点一律\"书中提出/作者认为\"视角限定；"
    "金句转述不挂引号。\n"
    "【六段结构】钩子 → 回顾+引入 → 核心概念拆解（一）→（二）→（三）→ 总结+下期预告，"
    "每段以附加指令给的【A-B秒｜段名】标签行开头，逐字保留。\n"
    "【输出】纯口播文本，末尾另起一段附严格 JSON 块 {\"coverage\":[str]} 列本集知识点，"
    "该块之后禁止再输出任何文字。"
)

# 防幻觉核心四字段: 仅 L0 提取或人工输入可入总纲
_CORE_FIELDS = ("全书核心主张", "关键概念清单", "核心金句", "核心案例")

# 弹性标签六段基准 (270s), 按目标时长等比缩放
_LABEL_BASE = [
    (0, 10, "钩子"),
    (10, 40, "回顾+引入"),
    (40, 100, "核心概念拆解（一）"),
    (100, 170, "核心概念拆解（二）"),
    (170, 220, "核心概念拆解（三）"),
    (220, 270, "总结+下期预告"),
]
_LABEL_RE = re.compile(r"【(\d+)-(\d+)秒｜([^】]+)】")


def _llm() -> LLMService:
    return LLMService(get_config().deepseek)


def _parse_json(text: str) -> Any:
    """LLM 输出取 JSON: 去 markdown 围栏后解析."""
    t = (text or "").strip()
    t = re.sub(r"^```(?:json)?", "", t)
    t = re.sub(r"```$", "", t).strip()
    m = re.search(r"[\[{]", t)
    if m and not t.startswith(("{", "[")):
        t = t[m.start():]
    return json.loads(t)


def _first_list(data: Any) -> list:
    """LLM 常把数组包进 dict — 取第一个非空 dict 列表值."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def elastic_labels(target: float) -> list[tuple[int, int, str]]:
    """六段结构按目标时长等比缩放 (默认 600s)."""
    k = target / 270.0
    return [(round(a * k), round(b * k), name) for a, b, name in _LABEL_BASE]


def validate_script(text: str, target: float) -> tuple[bool, list[str]]:
    """硬校验: 字数 2700-3000 + 六标签完整 + 末段终点≈目标±10%."""
    issues: list[str] = []
    body = _LABEL_RE.sub("", text or "")
    n = len(re.sub(r"\s", "", body))
    if not 2700 <= n <= 3000:
        issues.append(f"字数 {n} {'超出 3000' if n > 3000 else '不足 2700'}")
    labels = _LABEL_RE.findall(text or "")
    names = [x[2].strip() for x in labels]
    for _a, _b, name in _LABEL_BASE:
        if name not in names:
            issues.append(f"缺标签【{name}】")
    if labels:
        end = max(int(b) for _a, b, _n in labels)
        if abs(end - target) > target * 0.1:
            issues.append(f"末段终点 {end}s 偏离目标 {target:.0f}s ±10%")
    return (not issues, issues)


def source_context(book: BookProject, cap: int = 12000) -> str:
    """L0 来源上下文: 精华/原书章节摘要 (cap 内), 无来源返回空串."""
    if not book.source_path:
        return ""
    try:
        parsed = read_book(book.source_path)
    except Exception as exc:
        logger.warning("[book] L0 读取失败 %s: %s", book.source_path, exc)
        return ""
    parts, used = [], 0
    for ch in parsed["chapters"]:
        if used >= cap:
            break
        take = ch["text"][: max(500, cap - used)]
        parts.append(f"【{ch['name']}】{take}")
        used += len(take)
    return "\n".join(parts)


# ── Gate 0: 蒸馏前置预评估 (2026-08-19, 豆包第4发框架) ────────────
def assess_book_risk(title: str, author: str | None = None,
                     meta: dict | None = None) -> dict:
    """丢书名定档: green/yellow/red + 核心雷区 + 最低安全操作 + 是否放弃.

    防几十分钟蒸馏浪费; 评估失败 fail-open 到 yellow (谨慎) 不阻塞。
    """
    rules = load_book_rules()
    g = rules.get("book_grading") or {}
    sys_p = (
        "你是短视频读书解说前置评估官。按书名/作者/书页简介快速判定适不适合短视频口播解说。"
        f"三档: 🟢低风险={g.get('green', '')}; 🟡中风险={g.get('yellow', '')}; "
        f"🔴建议放弃={g.get('red_abandon', '')}。"
        "铁律: 书能出版≠适合短视频解说; 视频+醒目大字幕=审核最严模式。"
        "输出严格 JSON: {\"tier\":\"green|yellow|red\",\"risk_points\":[str],"
        "\"min_safe_ops\":[str],\"abandon\":bool}"
    )
    user_p = f"书名：《{title}》\n作者：{author or '未知'}"
    if meta and meta.get("blurb"):
        user_p += f"\n内容简介：{(meta.get('blurb') or '')[:800]}"
    try:
        out = LLMService(get_config().deepseek).chat(sys_p, user_p, model="pro",
                                                     temperature=0.2, timeout=300)
        a = GemmaClient.parse_json_block(out)
    except Exception as exc:
        logger.warning("[book] 预评估失败 (fail-open yellow): %s", exc)
        return {"tier": "yellow", "risk_points": [], "min_safe_ops": [],
                "abandon": False, "error": str(exc)}
    tier = a.get("tier") if a.get("tier") in ("green", "yellow", "red") else "yellow"
    return {
        "tier": tier,
        "risk_points": [str(x) for x in (a.get("risk_points") or [])][:8],
        "min_safe_ops": [str(x) for x in (a.get("min_safe_ops") or [])][:8],
        "abandon": bool(a.get("abandon")) or tier == "red",
    }


# ── 步骤 1: 输入补全 (flash) ─────────────────────────────────────
def _enrich_meta_fallback(book: BookProject, meta: dict | None) -> dict:
    """书页信息截断/缺失兜底 (2026-08-19): 页面优先, 搜索补简介, txt L0 补目录.

    用户实测部分书页简介截断/目录缺 → 阈值检测后降级补全; 全缺不编 (红线)。
    """
    from app.services.zhipu_search import ZhipuSearchError, zhipu_web_search

    meta = dict(meta or {})
    filled: list[str] = []

    # 简介: 页面 <200 字视为截断 → 搜索取最长 snippet
    if len(meta.get("blurb") or "") < 200:
        try:
            hits = zhipu_web_search(f"{book.book_title} {meta.get('author') or ''} 内容简介 简介", count=4)
            best = max((h.get("content") or "" for h in hits), key=len, default="")
            if len(best) > len(meta.get("blurb") or ""):
                meta["blurb"] = best[:3000]
                filled.append("blurb←搜索")
        except ZhipuSearchError as exc:
            logger.warning("[book] 简介兜底搜索不可用: %s", exc)

    # 目录: 页面 <5 条且 L0 为 txt(章节名干净) → 用 L0 章节名
    if len(meta.get("toc") or []) < 5 and book.source_path:
        try:
            parsed = read_book(book.source_path)
            names = [c["name"] for c in parsed["chapters"]
                     if c["name"] != "全文" and len(c["name"]) <= 40][:40]
            if len(names) >= 5:
                meta["toc"] = names
                filled.append("toc←L0章节")
        except Exception as exc:
            logger.warning("[book] 目录兜底失败: %s", exc)

    if filled:
        meta["_gaps_filled"] = filled
    return meta
def complete_input(db: Session, book: BookProject) -> BookProject:
    l0 = source_context(book)
    tier = "L0" if l0 else "L2"
    sys_p = (
        "你是拆书稿创作系统的输入补全模块。基于用户提供的书名/作者"
        + ("和【书籍来源文本】" if l0 else "（无来源文本，凭你的知识）")
        + "，补全创作输入清单。严禁编造：来源没有的字段列入 missing，不得猜测填充。"
        + "输出严格 JSON: {\"书籍类型\":str,\"全书核心主张\":str,\"章节结构\":[str],"
        "\"关键概念清单\":[str],\"核心金句\":[str],\"核心案例\":[str],"
        "\"目标读者画像\":str,\"missing\":[str]}"
    )
    user_p = f"书名：《{book.book_title}》\n作者：{book.author or '未知'}"
    # 知海书页 L1 (元数据/简介/目录) — 免搜索; 抓取失败静默降级
    if getattr(book, "source_url", None):
        from app.services.book_service.reader import fetch_zhihailib_meta
        meta = _enrich_meta_fallback(book, fetch_zhihailib_meta(book.source_url))
        if meta:
            pre = dict(book.input_json or {})
            pre["book_meta"] = {k: meta.get(k) for k in
                                ("title", "author", "publisher", "pub_date", "blurb", "toc")}
            book.input_json = pre
            if not book.author and meta.get("author"):
                book.author = meta["author"]
            user_p += (
                f"\n\n【书页信息 L1】作者 {meta.get('author', '')} / 出版社 {meta.get('publisher', '')} / "
                f"出版 {meta.get('pub_date', '')}\n内容简介: {(meta.get('blurb') or '')[:1500]}"
                f"\n目录: {' / '.join((meta.get('toc') or [])[:40])}")
    if l0:
        user_p += f"\n\n【书籍来源文本（节选）】\n{l0}"
    data = _parse_json(_llm().chat(sys_p, user_p, model="flash", temperature=0.3))

    inp = dict(book.input_json or {})
    for k in ("书籍类型", "全书核心主张", "章节结构", "关键概念清单",
              "核心金句", "核心案例", "目标读者画像"):
        v = data.get(k)
        if v not in (None, "", []):
            inp[k] = {"value": v, "tier": tier}
    # 目标读者画像 (2026-08-20): 账号人设级属性, 书级缺省继承 — 不再要求录入时人工补.
    # LLM 给了书级特定画像用之, 否则回退 Persona.target_reader (静读书固定受众).
    if not (inp.get("目标读者画像") or {}).get("value"):
        reader = _persona_target_reader(db)
        if reader:
            inp["目标读者画像"] = {"value": reader, "tier": "persona", "inherited": True}
    missing = list(data.get("missing") or [])
    # 目标读者画像已由人设兜底, 从 missing 剔除
    if "目标读者画像" in missing:
        missing.remove("目标读者画像")
    # 核心四字段: 无 L0 时 L2 一律标待补 (防幻觉红线)
    needs = list(missing)
    if not l0:
        for f in _CORE_FIELDS:
            if f not in needs:
                needs.append(f)
    inp["needs_supplement"] = needs
    book.input_json = inp
    book.book_type = (inp.get("书籍类型") or {}).get("value")
    book.core_claim = (inp.get("全书核心主张") or {}).get("value")
    book.status = "input_review"
    db.commit()
    return book


def _persona_target_reader(db: Session) -> str | None:
    """书账号人设的目标读者画像 (静读书). 供书级缺省继承."""
    from .persona import ensure_book_account
    from app.models import Persona
    try:
        host = ensure_book_account(db)
        p = db.query(Persona).filter(Persona.host_id == host.id).first()
        return (p.target_reader or "").strip() if p else None
    except Exception as exc:
        logger.warning("[book] persona target_reader lookup failed: %s", exc)
        return None


# ── 步骤 2: 评论层书化 (flash) — 读者反应清单 ─────────────────────
def build_comment_layer(db: Session, book: BookProject) -> BookProject:
    inp = dict(book.input_json or {})  # 必须拷贝: 同实例原地改 SQLAlchemy 不记脏
    l0 = source_context(book, cap=6000)
    sys_p = (
        "你是拆书项目的评论层模块。模拟目标读者看完这本书后的真实反应，"
        "产出读者反应清单，供逐集创作戳痛点/制造共鸣。"
        "输出严格 JSON 数组: [{\"type\":\"痛点|质疑|共鸣|好奇|唱反调\",\"comment\":str}]，8-10 条。"
    )
    user_p = (
        f"书名：《{book.book_title}》\n核心主张：{book.core_claim or ''}\n"
        f"读者画像：{(inp.get('目标读者画像') or {}).get('value') or _persona_target_reader(db) or ''}\n"
        + (f"\n【来源节选】\n{l0}" if l0 else "")
    )
    data = _first_list(_parse_json(_llm().chat(sys_p, user_p, model="flash", temperature=0.8)))
    inp["comment_layer"] = data
    book.input_json = inp
    db.commit()
    return book


# ── 步骤 3: 素材包书化 — 搜索 L1 (书评/访谈/延伸阅读) ─────────────
def build_materials(db: Session, book: BookProject) -> BookProject:
    from app.services.zhipu_search import ZhipuSearchError, zhipu_web_search

    queries = [
        f"{book.book_title} {book.author or ''} 书评",
        f"{book.book_title} 核心观点 解读",
        f"{book.author or book.book_title} 访谈",
    ]
    items: list[dict] = []
    for q in queries:
        try:
            hits = zhipu_web_search(q, count=3)
        except ZhipuSearchError as exc:
            logger.warning("[book] 素材搜索不可用: %s", exc)
            break
        for h in hits:
            items.append({"title": h.get("title"), "media": h.get("media"),
                          "snippet": (h.get("content") or "")[:300], "link": h.get("link")})
    inp = dict(book.input_json or {})  # 拷贝防 ORM 同实例不记脏
    inp["materials"] = items
    book.input_json = inp
    db.commit()
    return book


# ── 步骤 4: 多集总纲 (pro) + 追溯自检 ────────────────────────────
def build_roadmap(db: Session, book: BookProject) -> tuple[BookProject, list[str]]:
    inp = book.input_json or {}

    def _v(k):
        return (inp.get(k) or {}).get("value")

    sys_p = (
        "你是拆书稿创作系统的总纲模块。按 6 集系列拆解规则生成【6集拆解路线图】："
        "第1集全书地图/第2-5集核心模块(每集1-2概念, 层层深入)/第6集落地收尾(行动清单)。"
        "每集主题必须可追溯到书籍来源，严禁凭空编造。"
        "输出严格 JSON 数组 6 项: {\"ep\":int,\"主题\":str,\"对应书中内容\":str,"
        "\"核心任务\":str,\"承上\":str,\"启下\":str,\"概念\":[str]}"
    )
    user_p = (
        f"书名：《{book.book_title}》\n核心主张：{book.core_claim or ''}\n"
        f"关键概念：{_v('关键概念清单')}\n章节结构：{_v('章节结构')}\n"
        f"读者反应清单：{json.dumps(inp.get('comment_layer') or [], ensure_ascii=False)[:2000]}"
    )
    rows = _first_list(_parse_json(_llm().chat(sys_p, user_p, model="pro", temperature=0.5)))
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError(f"总纲须为 6 行, 实际 {len(rows) if isinstance(rows, list) else type(rows)}")

    # 追溯自检: 关键概念须在总纲有落点 (金句/案例落逐集稿, 不在总纲级查)
    issues: list[str] = []
    blob = json.dumps(rows, ensure_ascii=False)
    for item in (_v("关键概念清单") or [])[:10]:
        key = str(item)[:12]
        if key and key not in blob:
            issues.append(f"关键概念未入总纲: {key}…")

    # 落库 6 集
    for old in list(book.episodes):
        db.delete(old)
    for r in rows:
        db.add(Episode(
            book_id=book.id, ep_index=int(r.get("ep", 0)) or rows.index(r) + 1,
            title=str(r.get("主题", "")), roadmap_json=r,
            target_duration_sec=600.0, status="pending",
        ))
    book.status = "roadmap_review"
    db.commit()
    return book, issues


# ── 步骤 5: 逐集生成 (pro) + 自检 + 硬校验 + 人设注入 ─────────────
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
        + "7. 正文末尾另起一段附严格 JSON 块 {\"coverage\":[str]} 列本集知识点"
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
    if abs_claim:
        hard_lines.append(f"1. 书中观点限定: {abs_claim}")
    if qual_disc:
        hard_lines.append(f"2. 资质边界: {qual_disc}")
    if map_ban:
        hard_lines.append(f"3. 不映射现实: {map_ban}")
    if hard_lines:
        sys_p += "\n【合规硬约束 · 逐条必守(优先级最高, 与上面汇总同源)】\n" + "\n".join(hard_lines)
    if ep.ep_index == 1 and rules.get("opening_disclaimer"):
        # 2026-08-21 免责视觉化: 免责不上口播(省开篇黄金时间), 由成片首帧右上角字幕呈现
        sys_p += ("\n强制免责(视觉化, 不上口播): 系统会在成片首帧画面右上角加免责字幕"
                  "('以下仅为这本书的作者观点…'), 口播稿不要念免责声明, "
                  "把开篇 0-3 秒黄金时间留给痛点钩子。")
    user_p = (
        f"书名：《{book.book_title}》 第{ep.ep_index}集：{ep.title}\n"
        f"本集路线图：{json.dumps(ep.roadmap_json or {}, ensure_ascii=False)}\n"
        f"全书输入：{json.dumps({k: (v or {}).get('value') for k, v in inp.items() if isinstance(v, dict)}, ensure_ascii=False)[:4000]}\n"
        f"读者反应：{json.dumps(inp.get('comment_layer') or [], ensure_ascii=False)[:1500]}\n"
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
