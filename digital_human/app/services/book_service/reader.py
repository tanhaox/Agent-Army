# -*- coding: utf-8 -*-
"""书库解析 (2026-08-19) — 目录扫描 + txt/epub 提取 (标准库, 零新依赖).

epub = zip 装排版文本, 非扫描版零 OCR; 全书 >10 万字时下游按自然章节分章提取。
方案: docs/拆书项目-实施方案.md §3.1。
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


def _strip_html(raw: str) -> str:
    return re.sub(r"\s+", "", _TAG_RE.sub("", raw))


def _cut_frontmatter(text: str) -> str:
    """ epub 首章常混入目录/版权页前料: 若含"目录/版权"且后出现章节头, 从首个章节头截断."""
    if ("目录" in text[:200] or "版权" in text[:200]):
        m = _HEAD_ANY_RE.search(text)
        if m:
            return text[m.start():]
    return text


def read_book(path: str | Path) -> dict:
    """解析 txt/md/epub → {book_title, chapters:[{name, text}], total_chars}.

    txt: 有"第X章"头则按头分章, 否则单章"全文";
    epub: 按文件自然章节 (排除封面/目录)。
    """
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".epub":
        chapters = _read_epub(path)
    elif ext in (".txt", ".md"):
        chapters = _read_txt(path)
    else:
        raise ValueError(f"不支持的书源格式: {ext} (txt/md/epub)")
    total = sum(len(c["text"]) for c in chapters)
    return {"book_title": clean_book_title(path.stem), "chapters": chapters, "total_chars": total}


def _read_txt(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
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
    return [c for c in chapters if c["text"].strip()]


def _read_epub(path: Path) -> list[dict]:
    z = zipfile.ZipFile(path)
    names = [n for n in z.namelist() if n.lower().endswith((".html", ".xhtml", ".htm"))]
    body = [n for n in names if not re.search(r"(cover|toc|nav|title)", n, re.I)] or names
    body.sort()
    chapters = []
    for n in body:
        text = _cut_frontmatter(_strip_html(z.read(n).decode("utf-8", errors="replace")))
        if len(text) > 200:  # 过短视为版权页/扉页
            chapters.append({"name": n.split("/")[-1], "text": text})
    return chapters


# ── 知海书页元数据爬取 (2026-08-19) ─────────────────────────────
# 只爬公开元数据/内容简介/目录 (L1), 不自动化下载 EPUB (下载人工)。
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
