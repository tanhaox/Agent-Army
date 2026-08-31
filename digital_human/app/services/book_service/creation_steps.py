# -*- coding: utf-8 -*-
"""拆书创作步骤 1-4 + Gate0 — 输入补全 / 评论层 / 素材包 / 多集总纲 / L0 自动填充.

拆包自 orchestrator.py (2026-09-01), 函数体原样搬运零行为变更.
"""
from __future__ import annotations

import json
import logging
import re

from sqlalchemy.orm import Session

from app.config import get_config
from app.models import BookProject, Episode
from app.services.book_service.creation_common import (
    _CORE_FIELDS,
    _first_list,
    _llm,
    _parse_json,
    source_context,
)
from app.services.book_service.distiller import GemmaClient, load_book_rules
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

__all__ = ["assess_book_risk", "complete_input", "auto_fill_from_l0",
           "build_comment_layer", "build_materials", "build_roadmap"]


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
            from app.services.book_service.reader import read_book
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
