# -*- coding: utf-8 -*-
"""拆书创作编排 (2026-08-19) — 5 步 pipeline + 级联重跑 + 自检 + 硬校验.

方案: docs/design/拆书项目-实施方案.md §3/§3.1。
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
# 2026-08-23: 自称"静"而非"静姐" — 拉大受众群 (静姐限定了已婚熟龄, 静覆盖更广)
_PERSONA_IDENTITY = "我是静，读透一本好书，陪你遇见更好的自己。"
_PERSONA_ENDING = "照顾好自己，让我们一起成长。我是静，下期见。"

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
    "你是\"静读书\"的拆书讲述者静，45岁+，已有上小学的儿子。满级情商、温柔、知性、"
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
def _l0_facing(book: BookProject) -> tuple[list, list]:
    """读 L0 第二层 facing-readers/units (data/l0/{书名}/facing/), 缺失返回空.

    2026-08-22 评论层精修: 优先用 facing 产出 (读者痛点+主题单元), 评论关联单元.
    """
    try:
        from app.services.book_service.l0 import _l0_dir
        facing = _l0_dir(book.book_title) / "facing"
        readers: list = []
        units: list = []
        try:
            readers = json.loads((facing / "facing-readers.json").read_text(encoding="utf-8")).get("readers", [])
        except Exception:
            pass
        try:
            units = json.loads((facing / "facing-units.json").read_text(encoding="utf-8")).get("units", [])
        except Exception:
            pass
        return readers, units
    except Exception:
        return [], []


def _l0_facing_data(book: BookProject) -> dict:
    """读全部 facing (data/l0/{书名}/facing/*.json), 缺失字段为 None."""
    from app.services.book_service.l0 import _l0_dir
    d = _l0_dir(book.book_title)
    facing: dict = {}
    for name, f in {"kernel": "facing-kernel.json", "units": "facing-units.json",
                    "quotes": "facing-quotes.json", "cases": "facing-cases.json",
                    "compliance": "facing-compliance.json", "readers": "facing-readers.json"}.items():
        p = d / "facing" / f
        if p.exists():
            try:
                facing[name] = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                facing[name] = None
    # L0 合并章节
    l0p = d / "l0-chapter-v1.json"
    if l0p.exists():
        try:
            facing["l0"] = json.loads(l0p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return facing


def auto_fill_from_l0(db: Session, book: BookProject) -> list[str]:
    """从 L0/facing 自动填充 (2026-08-22): 补全字段/合规/评论层/总纲 — 免重复点击.

    蒸馏(L0+facing)已产出分析层: 内核/概念/金句/合规/读者痛点/主题单元,
    直接填充 input_json/risk_assessment/comment_layer/episodes, 不再让 LLM 重新读全文.
    返回填充说明列表; 已填字段跳过 (幂等, 人工改过的不覆盖).
    """
    facing = _l0_facing_data(book)
    if not facing:
        return []
    inp = dict(book.input_json or {})
    filled: list[str] = []

    def _set(key: str, val, *, force: bool = False) -> bool:
        if force or not inp.get(key):
            inp[key] = val
            return True
        return False

    # 1) 补全字段 ← kernel + L0 概念/金句
    kernel = facing.get("kernel")
    if kernel and _set("全书核心主张", {"value": kernel.get("one_liner", "")}):
        filled.append("核心主张←内核")
    l0 = facing.get("l0")
    if l0:
        concepts: list[str] = []
        for ch in l0.get("chapters", []):
            for c in (ch.get("concepts") or []):
                n = c.get("name")
                if n and n not in concepts:
                    concepts.append(str(n))
        if concepts and _set("关键概念清单", {"value": concepts[:20]}):
            filled.append(f"概念←L0({len(concepts)}个)")
    quotes = facing.get("quotes")
    if quotes:
        g = [str(q.get("text")) for q in quotes.get("quotes", []) if q.get("type") == "格言型"][:5]
        if g and _set("核心金句", {"value": g}):
            filled.append(f"金句←facing-quotes({len(g)}格言)")

    # 2) 合规 ← facing-compliance → risk_assessment
    compliance = facing.get("compliance")
    if compliance and not inp.get("risk_assessment"):
        su = compliance.get("sensitive_units") or []
        inp["risk_assessment"] = {
            "tier": compliance.get("book_tier", "yellow"),
            "risk_points": [h for u in su for h in (u.get("hits") or [])][:10],
            "min_safe_ops": [str(a) for a in (compliance.get("safe_angles") or [])][:3],
            "abandon": bool(compliance.get("abandon")),
        }
        filled.append(f"合规←facing-compliance({compliance.get('book_tier','?')})")

    # 3) 评论层 ← facing-readers; readers 缺失时回退 LLM 生成 (2026-08-23: 防 facing 只跑部分层 → 评论层 0)
    readers = facing.get("readers")
    if not inp.get("comment_layer"):
        if readers:
            comments = [{"type": "痛点", "comment": r.get("pain", ""), "unit_id": r.get("unit_id", "")}
                        for r in readers.get("readers", [])]
            if comments:
                inp["comment_layer"] = comments
                filled.append(f"评论层←facing-readers({len(comments)}痛点)")
        else:
            try:
                # 用主题单元 flash LLM 生成 (同 确认1 路径); 提交后重读 inp 保住其结果
                build_comment_layer(db, book)
                inp = dict(book.input_json or {})
                if inp.get("comment_layer"):
                    filled.append(f"评论层←LLM回退({len(inp['comment_layer'])}条)")
            except Exception as exc:
                logger.warning("[book] 评论层回退生成失败: %s", exc)

    book.input_json = inp

    # 4) 总纲 ← facing-units (编排 episodes, 每集一单元, 对应书中内容←L0 章节映射)
    units = facing.get("units")
    l0 = facing.get("l0") or {}
    if units:
        from app.models import Episode
        unit_list = units.get("units", [])
        unit_titles = {str(u.get("title", "")).strip() for u in unit_list}
        # 重建条件: 无 episodes / 缺字段(对应书中内容/卖点) / units 已变更(标题不同步) / 对应书中内容含旧文件名 — 人工编辑过的保留
        needs_rebuild = (not book.episodes) or not all(
            (e.roadmap_json or {}).get("对应书中内容") and (e.roadmap_json or {}).get("卖点")
            and (e.title or "").strip() in unit_titles
            and not re.search(r"text\d+\.html", str((e.roadmap_json or {}).get("对应书中内容", "")))
            for e in book.episodes)
        # E1 系列预告升级: 多集时 E1 必须带"系列预告"字段
        if not needs_rebuild and len(unit_list) > 1:
            e1 = next((e for e in book.episodes if e.ep_index == 1), None)
            if not (e1 and (e1.roadmap_json or {}).get("系列预告")):
                needs_rebuild = True
        if needs_rebuild:
            for old in list(book.episodes):
                db.delete(old)
            db.flush()
            for i, u in enumerate(unit_list, 1):
                # 对应书中内容: 单元概念匹配 L0 章节标题 (文件名友好化为"第N章")
                uc = set(str(c) for c in (u.get("concepts") or []))
                hit = []
                for ch in (l0.get("chapters") or []):
                    if any(str(c.get("name", "")) in uc or str(c.get("name", "")) == x
                           for c in (ch.get("concepts") or []) for x in uc):
                        t = str(ch.get("title", ""))
                        if re.match(r"text\d+\.html$", t, re.I):  # 旧 L0 文件名 → 第N章
                            t = f"第{ch.get('idx', '?')}章"
                        hit.append(t)
                prev_ref = f"第{i - 1}集" if i > 1 else "全书导入"
                next_ref = f"第{i + 1}集" if i < len(unit_list) else "系列完结"
                selling = (u.get("selling_point") or "") or (u.get("analogy_hooks") or [""])[0] or str(u.get("core_claim", ""))[:40]
                # 2026-08-22: E1 导读带系列预告 (已知全集数 + 各集主题 → 引导追更/关注)
                preview = ""
                if i == 1 and len(unit_list) > 1:
                    others = [f"第{j}集《{unit_list[j - 1].get('title', '')}》"
                              for j in range(2, len(unit_list) + 1)]
                    preview = (f"本系列共{len(unit_list)}集：第1集导读全书，为什么值得读；"
                               + "；".join(others) + "。"
                               + ("最后一集教你落地应用。本期开头预告整体系列，引导关注追更。" if len(unit_list) > 2 else ""))
                db.add(Episode(
                    book_id=book.id, ep_index=i, title=u.get("title", ""),
                    roadmap_json={"ep": i, "unit_id": u.get("id", ""), "主题": u.get("title", ""),
                                  "对应书中内容": "、".join(hit[:3]) or str(u.get("core_claim", ""))[:40],
                                  "核心任务": u.get("core_claim", ""),
                                  "卖点": selling,
                                  "系列预告": preview,
                                  "承上": f"承接{prev_ref}", "启下": f"引出{next_ref}",
                                  "概念": u.get("concepts", [])},
                    target_duration_sec=600.0, status="pending",
                ))
            book.status = "roadmap_review"
            filled.append(f"总纲←facing-units({len(unit_list)}集)")

    db.commit()
    return filled


def build_comment_layer(db: Session, book: BookProject) -> BookProject:
    inp = dict(book.input_json or {})  # 必须拷贝: 同实例原地改 SQLAlchemy 不记脏
    l0 = source_context(book, cap=6000)
    readers, units = _l0_facing(book)
    reader_txt = _persona_target_reader(db) or (inp.get("目标读者画像") or {}).get("value") or ""
    if readers or units:
        # 精修 (2026-08-22): 输入 facing 产出, 每条评论关联主题单元 → 逐集按单元戳痛点
        sys_p = (
            "你是拆书项目的评论层模块。基于目标读者痛点与主题单元，模拟读者看完这本书后的真实评论，"
            "供逐集创作戳痛点/制造共鸣。"
            "每条评论必须关联一个主题单元(unit_id)，覆盖主要单元。"
            "输出严格 JSON 数组: [{\"type\":\"痛点|质疑|共鸣|好奇|唱反调\",\"comment\":str,\"unit_id\":str}]，8-12 条。"
        )
        user_p = f"书名：《{book.book_title}》\n读者画像：{reader_txt}\n"
        if readers:
            user_p += "\n【读者痛点】\n" + "\n".join(
                f"- {r.get('pain', '')} (unit:{r.get('unit_id', '')})" for r in readers[:10])
        if units:
            user_p += "\n【主题单元】\n" + "\n".join(
                f"- {u.get('id', '')} {u.get('title', '')}: {str(u.get('core_claim', ''))[:80]}" for u in units[:10])
        if l0:
            user_p += f"\n\n【来源节选】\n{l0}"
    else:
        # 回退旧逻辑 (无 facing 时)
        sys_p = (
            "你是拆书项目的评论层模块。模拟目标读者看完这本书后的真实反应，"
            "产出读者反应清单，供逐集创作戳痛点/制造共鸣。"
            "输出严格 JSON 数组: [{\"type\":\"痛点|质疑|共鸣|好奇|唱反调\",\"comment\":str}]，8-10 条。"
        )
        user_p = (
            f"书名：《{book.book_title}》\n核心主张：{book.core_claim or ''}\n"
            f"读者画像：{reader_txt}\n"
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

    # 2026-08-22: 按 L0 第二层 facing-units 自适应集数 (units.length = 该拆几集);
    # 无 units 回退旧 6 集逻辑.
    _readers, units = _l0_facing(book)
    if units:
        n = len(units)
        unit_lines = "\n".join(
            f"- {u.get('id')}《{u.get('title')}》: {str(u.get('core_claim', ''))[:100]}"
            f" 概念:{','.join(str(c) for c in (u.get('concepts') or [])[:4])}"
            for u in units)
        sys_p = (
            "你是拆书稿创作系统的总纲模块。已给出本书的 " + str(n) + " 个主题单元（每单元=可独立讲 5-8 分钟的主题），"
            "按单元生成 N 集路线图，每集对应一个单元（顺序可按讲述逻辑调整，第 1 集可作为全书地图）。"
            "每集必须保留对应单元的 unit_id，主题可追溯到单元 core_claim，严禁编造单元外内容。"
            '输出严格 JSON 数组 ' + str(n) + ' 项: {"ep":int,"unit_id":str,"主题":str,"对应书中内容":str,'
            '"核心任务":str,"承上":str,"启下":str,"概念":[str]}'
        )
        user_p = (
            f"书名：《{book.book_title}》\n核心主张：{book.core_claim or ''}\n【主题单元】\n{unit_lines}\n"
            f"读者反应清单：{json.dumps(inp.get('comment_layer') or [], ensure_ascii=False)[:2000]}"
        )
    else:
        n = 6
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
    if not isinstance(rows, list) or len(rows) != n:
        raise ValueError(f"总纲须为 {n} 行, 实际 {len(rows) if isinstance(rows, list) else type(rows)}")

    # 追溯自检: 关键概念须在总纲有落点 (金句/案例落逐集稿, 不在总纲级查)
    issues: list[str] = []
    blob = json.dumps(rows, ensure_ascii=False)
    for item in (_v("关键概念清单") or [])[:10]:
        key = str(item)[:12]
        if key and key not in blob:
            issues.append(f"关键概念未入总纲: {key}…")

    # 落库 N 集 (N = units 数或回退 6)
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
