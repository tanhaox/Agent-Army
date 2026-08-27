# -*- coding: utf-8 -*-
"""书库解析 (2026-08-22 v3) — txt/epub 提取 + L0 结构 (docs/design/蒸馏产物schema设计.md §7).

L0 P0 增强：
- 排版强调保留：`<b>/<strong>`/class bold → §B§…§/B§，`<i>/<em>` → §I§…§/I§，
  `<blockquote>/<table>` → §BOX§…§/BOX§（不再全剥标签压空白，保句读）
- epub OPF 元数据：publisher/isbn/pub_date/creator → meta（书内，非爬虫）
- epub 目录：toc.ncx / nav.xhtml → toc（比文件名排序准）
- 注释/角标：epub 锚点 `<a href="#noteN">`+注释块 / txt 角标 `【N】` → notes
- 序言/附录定位：frontmatter / backmatter role（内容/标题特征，不靠文件名）

返回：{book_title, meta, frontmatter[], chapters[], backmatter[], total_chars}
epub = zip 装排版文本，非扫描版零 OCR。
"""
from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = ["scan_book_sources", "read_book", "clean_book_title"]

_TAG_RE = re.compile(r"<[^>]+>")
# 文件名后缀: (zhihailib.com) / （Z-Library） / [电子书] 等来源标记
_SUFFIX_RE = re.compile(r"[\(（\[][^()（）\[\]]*?(zhihailib|zlibrary|libgen|ebook|电子书)[^()（）\[\]]*?[\)）\]]", re.IGNORECASE)
# 章节头: 第X章/节/部 (中文数字或阿拉伯)
_HEAD_RE = re.compile(r"^第[一二三四五六七八九十百零\d]+[章节部]")
# 文中章节头 (无锚点, 供前料截断用)
_HEAD_ANY_RE = re.compile(r"第[一二三四五六七八九十百零\d]+[章节部]")

# 序言 (frontmatter) / 附录 (backmatter) 关键词 (内容/标题特征)
_FRONT_KEYWORDS = ("作者序", "自序", "再版", "新版序", "序言", "前言", "序", "导言", "引子", "写在", "译者序")
_BACK_KEYWORDS = ("附录", "术语表", "参考文献", "索引", "后记", "致谢", "附言", "鸣谢", "注释")

# ── 排版强调内联标记 ─────────────────────────────────────────────
# 作者/出版商的排版标记 = 划重点信号 (金句/公式/重点高置信标注), L0 必须保留.
def _strip_html_with_emphasis(raw: str) -> str:
    """XHTML → 文本, 保留排版强调为内联标记 (§B§/§I§/§BOX§), 不压空白保句读."""
    raw = re.sub(r"<(?:b|strong)(\s[^>]*)?>", "§B§", raw, flags=re.I)
    raw = re.sub(r"</(?:b|strong)>", "§/B§", raw, flags=re.I)
    raw = re.sub(r"<(?:i|em)(\s[^>]*)?>", "§I§", raw, flags=re.I)
    raw = re.sub(r"</(?:i|em)>", "§/I§", raw, flags=re.I)
    raw = re.sub(r"<(?:blockquote|table)(\s[^>]*)?>", "§BOX§", raw, flags=re.I)
    raw = re.sub(r"</(?:blockquote|table)>", "§/BOX§", raw, flags=re.I)
    # class 含 bold/strong/em 的 span/div/p → §B§ (排除 calibre 系排版类)
    def _class_em(m: re.Match[str]) -> str:
        cls = m.group(1).lower()
        if "calibre" not in cls and any(k in cls for k in ("bold", "strong", "em", "emphasis")):
            return "§B§"
        return ""
    raw = re.sub(r'<(?:span|div|p)\b[^>]*class="([^"]*)"[^>]*>', lambda m: _class_em(m), raw, flags=re.I)
    text = re.sub(r"<[^>]+>", "", raw)
    # 归一化: 横向空白压一个空格, 保留换行/段落
    text = re.sub(r"[ \t　]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def _cut_frontmatter(text: str) -> str:
    """ epub 首章常混入目录/版权页前料: 若含"目录/版权"且后出现章节头, 从首个章节头截断."""
    if ("目录" in text[:200] or "版权" in text[:200]):
        m = _HEAD_ANY_RE.search(text)
        if m:
            return text[m.start():]
    return text


def clean_book_title(filename_stem: str) -> str:
    """文件名 → 书名: 去来源后缀标记."""
    return _SUFFIX_RE.sub("", filename_stem).strip()


def scan_book_sources(root: str | Path) -> list[dict]:
    """扫描书库目录: txt/md/epub, 文件名=书名. 返回按文件名排序的清单."""
    root = Path(root)
    if not root.is_dir():
        logger.warning("[book] 书库目录不存在: %s", root)
        return []
    out = []
    for p in sorted(root.iterdir()):
        if p.is_file() and p.suffix.lower() in (".txt", ".md", ".epub"):
            st = p.stat()
            out.append({
                "filename": p.name,
                "path": str(p),
                "book_title": clean_book_title(p.stem),
                "ext": p.suffix.lower().lstrip("."),
                "size": st.st_size,
                "mtime": st.st_mtime,  # 2026-08-20: 排序/折叠用
            })
    return out


# ── epub 元数据 / 目录 / 注释 (标准库, 零新依赖) ─────────────────
def _epub_meta(z: zipfile.ZipFile) -> dict:
    """epub OPF metadata → {author, publisher, isbn, pub_date}. 书内来源, 非爬虫."""
    meta: dict = {}
    try:
        container = z.read("META-INF/container.xml").decode("utf-8", errors="replace")
        m = re.search(r'full-path="([^"]+\.opf)"', container)
        if not m:
            return meta
        opf = z.read(m.group(1)).decode("utf-8", errors="replace")
        md = re.search(r"<metadata.*?</metadata>", opf, re.S)
        if not md:
            return meta
        block = md.group(0)

        def _dc(tag: str) -> str:
            mm = re.search(rf"<dc:{tag}[^>]*>(.*?)</dc:{tag}>", block, re.S)
            if not mm:
                return ""
            return re.sub(r"<[^>]+>", "", mm.group(1)).strip()

        author = _dc("creator")
        if author:
            meta["author"] = author
        pub = _dc("publisher")
        if pub:
            meta["publisher"] = pub
        ident = _dc("identifier")
        if ident:
            meta["isbn"] = ident
        date = _dc("date")
        if date:
            meta["pub_date"] = date[:10]  # YYYY-MM-DD
    except Exception as exc:
        logger.warning("[book] epub 元数据解析失败: %s", exc)
    return meta


def _epub_toc(z: zipfile.ZipFile) -> list[str]:
    """epub 目录 (toc.ncx / nav.xhtml) → 章节标题列表."""
    toc: list[str] = []
    for name in z.namelist():
        ln = name.lower()
        if "toc.ncx" in ln or (ln.endswith((".xhtml", ".html")) and re.search(r"/(nav|toc)", ln)):
            try:
                raw = z.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            titles = re.findall(r"<text[^>]*>(.*?)</text>", raw, re.S)  # ncx
            if not titles:
                titles = re.findall(r"<a[^>]*>(.*?)</a>", raw, re.S)  # nav
            toc = [re.sub(r"<[^>]+>", "", t).strip() for t in titles]
            toc = [t for t in toc if t]
            if toc:
                break
    return toc[:60]


def _epub_toc_map(z: zipfile.ZipFile) -> dict[str, str]:
    """epub 目录 → {章节文件: 标题} (toc.ncx/nav) — 章节名用标题替代文件名 (2026-08-22)."""
    m: dict[str, str] = {}
    for name in z.namelist():
        ln = name.lower()
        if "toc.ncx" in ln or (ln.endswith((".xhtml", ".html")) and re.search(r"/(nav|toc)", ln)):
            try:
                raw = z.read(name).decode("utf-8", errors="replace")
            except Exception:
                continue
            if "toc.ncx" in ln:
                # <navLabel><text>标题</text></navLabel><content src="file"/>
                for mm in re.finditer(
                        r"<navLabel>\s*<text>(.*?)</text>\s*</navLabel>\s*<content src=\"([^\"]+)\"", raw, re.S):
                    t = re.sub(r"<[^>]+>", "", mm.group(1)).strip()
                    if t:
                        m[mm.group(2).lstrip("/")] = t
            else:
                # <a href="file"><span>标题</span></a>
                for mm in re.finditer(
                        r'<a[^>]*href="([^"]+\.(?:x?html))"[^>]*>(.*?)</a>', raw, re.S):
                    t = re.sub(r"<[^>]+>", "", mm.group(2)).strip()
                    if t:
                        m[mm.group(1).lstrip("/")] = t
            if m:
                break
    return m


def _epub_notes(raw: str) -> list[dict]:
    """epub 注释锚点 → [{ref_marker, explanation}]. `<a href="#noteN">[2]</a>` + `<div id="noteN">`."""
    notes: list[dict] = []
    id_blocks: dict[str, str] = {}
    for m in re.finditer(r'<(?:div|p|span)[^>]*id="([^"]*)"[^>]*>(.*?)</(?:div|p|span)>', raw, re.S):
        nid, content = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if re.search(r"(note|footnote|注释|注\d)", nid, re.I) and content:
            id_blocks[nid] = content
    for m in re.finditer(r'<a[^>]*href="#([^"]+)"[^>]*>\s*([\[【（(]?\d+[\]】）)]?|.)\s*</a>', raw, re.I):
        target, marker = m.group(1), m.group(2).strip()
        if target in id_blocks:
            notes.append({"ref_marker": marker, "explanation": id_blocks[target]})
    return notes


def _epub_spine_order(z: zipfile.ZipFile) -> list[str] | None:
    """epub OPF spine → 章节文件顺序 (manifest idref→href 映射). 失败返回 None (回退文件名排序)."""
    try:
        container = z.read("META-INF/container.xml").decode("utf-8", errors="replace")
        m = re.search(r'full-path="([^"]+\.opf)"', container)
        if not m:
            return None
        opf = z.read(m.group(1)).decode("utf-8", errors="replace")
        href_by_id: dict[str, str] = {}
        for im in re.finditer(r'<item\b[^>]*id="([^"]+)"[^>]*href="([^"]+)"', opf):
            href_by_id[im.group(1)] = im.group(2)
        spine = re.findall(r'<itemref\b[^>]*idref="([^"]+)"', opf)
        order = []
        for rid in spine:
            href = href_by_id.get(rid)
            if href and href not in order:
                order.append(href)
        return order or None
    except Exception as exc:
        logger.warning("[book] epub spine 解析失败, 回退文件名排序: %s", exc)
        return None


def _split_chapters(text: str) -> list[tuple[str, str]]:
    """epub 文件内按"第X章 标题"分节 (2026-08-22) — 无结构化 h1/h2 的书, 章是正文"第X章"文本.

    - 去排版标记(§B§/§I§)后匹配"第X章" (正文章节标题常带粗体标记)
    - 标题行 + 下一行短标题合并 (如"第一章"+"整个人都不太好" → "第一章 整个人都不太好")
    - 目录项(无正文的短节)由调用方按长度过滤
    """
    lines = text.split("\n")
    secs: list[tuple[str, str]] = []
    cur_name, cur = "", []
    i = 0
    while i < len(lines):
        s = re.sub(r"§/?[BI]§", "", lines[i]).strip()
        if _HEAD_RE.match(s) and len(s) <= 40:
            title = s
            if i + 1 < len(lines):
                nxt = re.sub(r"§/?[BI]§", "", lines[i + 1]).strip()
                if nxt and len(nxt) <= 30 and not _HEAD_RE.match(nxt) \
                        and "目录" not in nxt and "CONTENTS" not in nxt and "contents" not in nxt:
                    title = f"{s} {nxt}"
                    i += 1
            if cur_name or cur:
                secs.append((cur_name or "前言", "\n".join(cur)))
            cur_name, cur = title, []
        else:
            cur.append(lines[i])
        i += 1
    if cur_name or cur:
        secs.append((cur_name or "前言", "\n".join(cur)))
    return secs or [("", text)]


def _section_role(name: str, text: str) -> str:
    """章节角色: frontmatter(序/前言) / backmatter(附录/参考文献/后记) / body."""
    head = text[:80]
    for k in _BACK_KEYWORDS:
        if (k in head and len(head) < 200) or k in name:
            return "backmatter"
    for k in _FRONT_KEYWORDS:
        if (k in head and len(head) < 200) or k in name:
            return "frontmatter"
    return "body"


def _read_epub(path: Path) -> dict:
    """epub → {meta, toc, frontmatter[], chapters[], backmatter[]}."""
    z = zipfile.ZipFile(path)
    meta = _epub_meta(z)
    toc = _epub_toc(z)
    toc_map = _epub_toc_map(z)  # 2026-08-22: 章节名用 toc 标题替代文件名
    order = _epub_spine_order(z)
    names = [n for n in z.namelist() if n.lower().endswith((".html", ".xhtml", ".htm"))]
    names = [n for n in names if not re.search(r"(cover|toc|nav|title|ncx|opf)", n, re.I)] or names
    if order:
        by_name = {n: n for n in names}
        ordered = [o for o in order if o in by_name or o.lstrip("/") in by_name]
        if ordered:
            names = ordered
    else:
        names.sort()

    frontmatter, chapters, backmatter = [], [], []
    for n in names:
        try:
            raw = z.read(n).decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("[book] 章节读取失败 %s: %s", n, exc)
            continue
        notes = _epub_notes(raw)
        text = _strip_html_with_emphasis(raw)
        text = _cut_frontmatter(text)
        if len(text) <= 200:  # 过短视为版权页/扉页
            continue
        fname = n.split("/")[-1]
        base_name = toc_map.get(n.lstrip("/")) or toc_map.get(fname) or fname
        # 文件内按"第X章"分节 (2026-08-22) — 粒度 = 真实章
        for sec_name, sec_text in _split_chapters(text):
            if len(sec_text) <= 200:
                continue
            name = sec_name or base_name
            role = _section_role(name, sec_text)
            item: dict = {"name": name, "text": sec_text, "role": role}
            if notes:
                item["notes"] = notes
            if role == "frontmatter":
                frontmatter.append(item)
            elif role == "backmatter":
                backmatter.append(item)
            else:
                chapters.append(item)
    return {"meta": meta, "toc": toc,
            "frontmatter": frontmatter, "chapters": chapters, "backmatter": backmatter}


def _read_txt(path: Path) -> dict:
    """txt/md → {meta, toc, frontmatter[], chapters[], backmatter[]}. 角标【N】→ notes."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    # 开头元信息: 目录 / 作者简介 (前 8KB 扫描)
    meta: dict = {}
    head = raw[:8000]
    for kw in ("关于作者", "作者简介", "作者简介：", "作者简介:"):
        i = head.find(kw)
        if i >= 0:
            seg = head[i + len(kw):i + len(kw) + 400]
            j = seg.find("\n\n")
            bio = seg if j < 0 else seg[:j]
            if bio.strip() and len(bio.strip()) < 300:
                meta["author_bio"] = re.sub(r"\s+", " ", bio).strip()
                break

    chapters: list[dict] = []
    cur_name, cur = "全文", []
    for line in raw.split("\n"):
        s = line.strip()
        if not s:
            continue
        if _HEAD_RE.match(s) and len(s) <= 30 and cur:
            chapters.append({"name": cur_name, "text": "".join(cur)})
            cur_name, cur = s, []
        cur.append(s)
    chapters.append({"name": cur_name, "text": "".join(cur)})
    chapters = [c for c in chapters if c["text"].strip()]

    frontmatter, body, backmatter = [], [], []
    for c in chapters:
        c["role"] = _section_role(c["name"], c["text"])
        # 角标注释: 【N】在正文, 匹配章节内"注释"段 (简化: 仅识别存在, 精确关联由第二层)
        m = re.findall(r"[【\[](\d{1,3})[】\]]", c["text"][:2000])
        if m:
            c["notes_hint"] = f"正文含角标 {len(m)} 处"
        if c["role"] == "frontmatter":
            frontmatter.append(c)
        elif c["role"] == "backmatter":
            backmatter.append(c)
        else:
            body.append(c)

    # 目录: 开头"目录"段 (若无章节头书, 从"目录"到首个章节头)
    toc: list[str] = []
    if "目录" in raw[:500]:
        i = raw.find("目录", 0, 500)
        seg = raw[i:i + 1500].split("\n")
        for line in seg[1:]:
            s = line.strip()
            if not s:
                continue
            if _HEAD_RE.match(s) and len(s) <= 30:
                toc.append(s)
            elif toc and _HEAD_RE.match(s):
                break
    return {"meta": meta, "toc": toc[:60],
            "frontmatter": frontmatter, "chapters": body, "backmatter": backmatter}


def read_book(path: str | Path) -> dict:
    """解析 txt/md/epub → {book_title, meta, frontmatter[], chapters[], backmatter[], total_chars}.

    txt: 有"第X章"头则按头分章, 否则单章"全文"; epub: 按 spine 顺序自然章节.
    chapters[]: {name, text(带 § 排版强调标记), role, notes?}
    """
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".epub":
        parsed = _read_epub(path)
    elif ext in (".txt", ".md"):
        parsed = _read_txt(path)
    else:
        raise ValueError(f"不支持的书源格式: {ext} (txt/md/epub)")
    total = sum(len(c["text"]) for c in parsed["chapters"])
    parsed["book_title"] = clean_book_title(path.stem)
    parsed["total_chars"] = total
    return parsed


# ── 知海书页元数据爬取 (2026-08-19, L0 元信息兜底) ───────────────
# 仅作书内缺失字段的可选补全 (如 epub 无作者简介时), 非必需路径.
_ZHL_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_zhihailib_meta(url: str, timeout: int = 30) -> dict | None:
    """知海书页 → {title, author, publisher, pub_date, blurb, toc}. 失败返回 None."""
    import requests as _rq
    try:
        r = _rq.get(url, headers=_ZHL_UA, timeout=timeout)
        r.raise_for_status()
        t = r.text
    except Exception as exc:
        logger.warning("[book] 知海书页抓取失败: %s", exc)
        return None

    meta: dict = {"url": url}
    m = re.search(r"《([^》]+)》[^:]*:?\s*作者[:：]\s*([^,，]+)[,，]\s*出版社[:：]\s*([^,，]+)[,，]\s*出版日期[:：]\s*([^,，]+)", t)
    if m:
        meta.update(title=m.group(1).strip(), author=m.group(2).strip(),
                    publisher=m.group(3).strip(), pub_date=m.group(4).strip())
    plain = re.sub(r"<[^>]+>", "\n", t)
    plain = re.sub(r"\n\s*\n+", "\n", plain)

    def _block(start_key: str, end_keys: tuple, cap: int) -> str:
        i = plain.find(start_key)
        if i < 0:
            return ""
        i += len(start_key)
        j = min((plain.find(k, i) for k in end_keys if plain.find(k, i) >= 0), default=i + cap)
        return re.sub(r"\s+", " ", plain[i:min(j, i + cap)]).strip()

    meta["blurb"] = _block("内容简介", ("作者简介", "译者简介", "作者／译者简介", "目录"), 3000)
    # 目录: 条目本身可能含"作者／译者简介"等词, 不能当终止符 → 按条目模式逐行收
    toc: list[str] = []
    i = plain.find("\n目录\n")
    if i >= 0:
        pat = re.compile(r"^(\d{1,3}[　\s]|第[一二三四五六七八九十\d]+[章节部]|人物表|作者|译者|前言|序|附录|后记|致谢)")
        for line in plain[i + 4:].split("\n"):
            s = line.strip()
            if not s:
                continue
            if pat.match(s) and len(s) <= 60:
                toc.append(s)
            elif toc:
                break
            if len(toc) >= 60:
                break
    meta["toc"] = toc
    return meta
