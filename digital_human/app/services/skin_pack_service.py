# -*- coding: utf-8 -*-
"""系列皮肤包 (SeriesSkinPack) — 拆书 5-6 集视觉统一的载体 (2026-08-21).

路线 (plan §锁定方案): 原坐标保留 + 加动画层 + 全局皮肤对齐 (2C).
母本集人工指定 (mark-master), 抽皮肤包落盘; ep2-6 渲染前 apply_skin_to_slides
统一背景/文字配色/字号 token. 不做逐页版式对齐.

皮肤包键 = book_id, 存 ppt_work_root/series_skins/{book_id}/.
"""
from __future__ import annotations

import base64
import json
import logging
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from app.config import get_config
from app.services.ppt_service import Slide, parse_pptx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

__all__ = [
    "SeriesSkinPack",
    "skin_dir",
    "extract_master",
    "load_skin",
    "apply_skin_to_slides",
]

# 跨集统一字体栈 (pptx 字体名不可靠, 全系列硬编码保持一致)
_DEFAULT_FONT_FAMILY = '"Source Han Serif SC","Noto Serif SC","Songti SC","Playfair Display",serif'
_DEFAULT_ANIM = {"stagger": 0.22, "in_dur": 0.55, "effect": "fade-slide-up"}


@dataclass
class SeriesSkinPack:
    book_id: str
    master_ep: int
    created_ts: str
    background_path: str          # 相对 ppt_work_root, 复用背景图文件
    color_tokens: list[str]       # 主→次 ["#8B4513","#1F2329","#FFFFFF"]
    fontsize_tokens: list[float]  # pt 降序 [32,16,14]
    bg_avg_hex: str = "#1a1a1a"   # 母本背景平均色 (2026-08-21, 对比度校验用)
    font_family: str = _DEFAULT_FONT_FAMILY
    style_images: dict = field(default_factory=dict)  # v1 空, 风格图跨集复用推迟 phase2
    animation_profile: dict = field(default_factory=lambda: dict(_DEFAULT_ANIM))


# ── 对比度工具 (2026-08-21): 皮肤映射后保证文字可读 ─────────────────────────
# 背景平均色亮度 <0.35 视为暗背景 → 文字向白提亮; 否则向黑压暗. 保色相.
_MIN_CONTRAST = 3.0


def _srgb_luminance(hex_str: str) -> float:
    c = _norm_color(hex_str) or "#000000"
    h = c.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    def _lin(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def _contrast_ratio(c1: str, c2: str) -> float:
    l1, l2 = _srgb_luminance(c1), _srgb_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _adjust_for_contrast(color_hex: str, bg_hex: str, min_ratio: float = _MIN_CONTRAST) -> str:
    """朝黑/白方向迭代调整文字色直到对比度达标, 保持色相 (暗底提亮/亮底压暗)."""
    c = _norm_color(color_hex) or "#FFFFFF"
    bg = _norm_color(bg_hex) or "#1a1a1a"
    if _contrast_ratio(c, bg) >= min_ratio:
        return c
    bg_lum = _srgb_luminance(bg)
    rgb = [int(c.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    for _ in range(24):
        if bg_lum < 0.5:
            rgb = [min(255, int(v * 1.4 + 14)) for v in rgb]
        else:
            rgb = [max(0, int(v * 0.6)) for v in rgb]
        c2 = "#%02X%02X%02X" % tuple(rgb)
        if _contrast_ratio(c2, bg) >= min_ratio:
            return c2
    return "#FFFFFF" if bg_lum < 0.5 else "#000000"


def skin_root() -> Path:
    return Path(get_config().defaults.ppt_work_root) / "series_skins"


def skin_dir(book_id: str) -> Path:
    return skin_root() / book_id


def _norm_color(hex_str: str | None) -> str | None:
    """pptx rgb (如 '8B4513') → '#8B4513'."""
    if not hex_str:
        return None
    s = str(hex_str).strip()
    return s if s.startswith("#") else "#" + s


def _has_master(book_id: str) -> bool:
    return (skin_dir(book_id) / "skin.json").exists()


def extract_master(job_workdir: Path, book_id: str, ep_index: int) -> SeriesSkinPack:
    """从母本集 pptx 抽皮肤包落盘. job_workdir 下应有 source.pptx."""
    slides = parse_pptx(job_workdir / "source.pptx")
    if not slides:
        raise ValueError("母本 pptx 无页, 无法抽皮肤包")

    # 色彩 token: 全部 TextBlock.color 频次降序 top5 去重
    color_counter: Counter = Counter()
    for s in slides:
        for tb in s.text_blocks:
            c = _norm_color(tb.color)
            if c:
                color_counter[c] += 1
    color_tokens = [c for c, _ in color_counter.most_common(5)]

    # 字号 token: 频次降序 top6 去重 (避免 16 档全量导致 apply 时逐 rank 拉伸失真)
    from collections import Counter as _C
    size_counter = _C()
    for s in slides:
        for tb in s.text_blocks:
            if tb.font_size_pt:
                size_counter[tb.font_size_pt] += 1
    # 主力档优先 (14/16/32 这类高频), 作为可用档池
    sizes_by_freq = [sz for sz, _ in size_counter.most_common(6)]
    sizes = sorted(sizes_by_freq, reverse=True)

    # 背景图: 取第一页背景写文件 (母本首页通常是封面/系列基调)
    bg_src = None
    for s in slides:
        if s.background_b64:
            bg_src = s.background_b64
            break
    if not bg_src:
        raise ValueError("母本无背景图可抽 (p:bg 提取失败?)")

    # data URI → 文件
    header, b64data = bg_src.split(",", 1)
    # header 形如 data:image/jpeg;base64
    ext = "jpg"
    if "png" in header:
        ext = "png"
    elif "jpeg" in header or "jpg" in header:
        ext = "jpg"

    d = skin_dir(book_id)
    d.mkdir(parents=True, exist_ok=True)
    bg_file = d / f"background.{ext}"
    bg_file.write_bytes(base64.b64decode(b64data))

    # 背景平均色 (对比度校验基准)
    bg_avg_hex = "#1a1a1a"
    try:
        from PIL import Image
        import io as _io
        im = Image.open(_io.BytesIO(base64.b64decode(b64data))).convert("RGB")
        px = im.resize((64, 36)).getdata()
        n = len(px)
        avg = tuple(round(sum(p[i] for p in px) / n) for i in range(3))
        bg_avg_hex = "#%02X%02X%02X" % avg
    except Exception as exc:
        logger.warning("[skin] 背景平均色计算失败: %s", exc)

    import datetime
    pack = SeriesSkinPack(
        book_id=book_id,
        master_ep=ep_index,
        created_ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        background_path=str(bg_file.relative_to(Path(get_config().defaults.ppt_work_root))),
        color_tokens=color_tokens,
        fontsize_tokens=sizes,
        bg_avg_hex=bg_avg_hex,
    )
    (d / "skin.json").write_text(
        json.dumps(asdict(pack), ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("[skin] 母本皮肤包已生成 book=%s ep=%d 色=%s 字号=%s",
                book_id, ep_index, color_tokens[:3], sizes[:4])
    return pack


def load_skin(book_id: str) -> SeriesSkinPack | None:
    """装载书系列皮肤包; 不存在返回 None."""
    p = skin_dir(book_id) / "skin.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return SeriesSkinPack(**raw)


def _token_by_rank(value, tokens: list, rank: int) -> object:
    """按本页 rank (0=最大) 取母本 token, 越界取末位."""
    if not tokens:
        return value
    idx = min(rank, len(tokens) - 1)
    return tokens[idx]


def _skin_bg_hex(skin: SeriesSkinPack) -> str:
    """母本背景平均色: 优先皮肤包记录; 旧包缺字段(默认哨兵)时从背景文件现算."""
    if getattr(skin, "bg_avg_hex", None) and skin.bg_avg_hex != "#1a1a1a":
        return skin.bg_avg_hex
    try:
        root = Path(get_config().defaults.ppt_work_root)
        p = root / skin.background_path
        if p.exists():
            from PIL import Image
            im = Image.open(p).convert("RGB").resize((64, 36))
            data = list(im.getdata())
            n = max(len(data), 1)
            avg = tuple(round(sum(c[i] for c in data) / n) for i in range(3))
            return "#%02X%02X%02X" % avg
    except Exception:
        pass
    return "#1a1a1a"


def apply_skin_to_slides(slides: list[Slide], skin: SeriesSkinPack) -> list[Slide]:
    """把母本皮肤应用到漂移集 (不改坐标, 只改背景/色/字号). 就地改.

    映射 (2C 全局皮肤, 不逐页对齐):
    - background: 全页 override 为母本背景 b64
    - color: 按本页字号 rank 映射母本 color_tokens (bold 块优先 primary),
      **映射后按背景对比度自动调整** (2026-08-21: 防止母本色板套上后
      棕字配棕底等不可读 — 暗底提亮/亮底压暗, 保色相)
    - fontsize: 不改 (豆包主档 14/16/32 跨集本就一致, 改了反而拉伸失真)
    - image: 不改 (搜图沿用各集)
    """
    # 读母本背景文件 → b64 (供 build_slide_html 内联)
    bg_b64 = _read_bg_as_b64(skin)
    if not bg_b64:
        return slides  # 背景读不到则不 apply (graceful)
    bg_hex = _skin_bg_hex(skin)

    for s in slides:
        s.background_b64 = bg_b64
        # 本页字号降序排 rank
        page_sizes = sorted(
            {tb.font_size_pt for tb in s.text_blocks if tb.font_size_pt},
            reverse=True,
        )
        size_rank = {sz: i for i, sz in enumerate(page_sizes)}
        for tb in s.text_blocks:
            # color 映射
            if skin.color_tokens:
                if tb.bold:
                    tb.color = skin.color_tokens[0]  # bold 优先 primary
                elif tb.font_size_pt in size_rank:
                    tb.color = _token_by_rank(
                        tb.color, skin.color_tokens, size_rank[tb.font_size_pt])
            # 对比度兜底: 映射后若与背景对比度不足 → 自动调整
            if tb.color:
                tb.color = _adjust_for_contrast(tb.color, bg_hex, _MIN_CONTRAST)
    return slides


def _read_bg_as_b64(skin: SeriesSkinPack) -> str | None:
    """读母本背景文件 → data URI b64."""
    root = Path(get_config().defaults.ppt_work_root)
    p = root / skin.background_path
    if not p.exists():
        logger.warning("[skin] 母本背景文件缺失: %s", p)
        return None
    ext = p.suffix.lower().lstrip(".")
    ctype = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "image/jpeg")
    return f"data:{ctype};base64,{base64.b64encode(p.read_bytes()).decode()}"
