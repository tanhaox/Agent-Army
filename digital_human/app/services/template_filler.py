"""Template filler — copy template source files into a per-job workspace,
then perform safe ``{{KEY}}`` placeholder substitution inside ``index.html``.

Placeholder rules:
- Only whitelisted keys are substituted (no LLM-style injection).
- Unknown ``{{...}}`` tokens are left untouched (HF template is authoritative).
- ``avatar.b64`` is copied verbatim (template controls its own asset name).

The workspace is ``<hf_visual_root>/<job_id>/``.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from app.config import get_config


# Whitelist of placeholders the orchestrator will substitute.  Anything outside
# this set is left as-is to keep the template author in full control.
_SAFE_KEYS = frozenset(
    {
        "title",
        "subtitle",
        "kicker",
        "metric_label_1",
        "metric_value_1",
        "metric_label_2",
        "metric_value_2",
        "metric_label_3",
        "metric_value_3",
        "metric_label_4",
        "metric_value_4",
        "chart_label_1",
        "chart_value_1",
        "chart_label_2",
        "chart_value_2",
        "chart_label_3",
        "chart_value_3",
        "chart_label_4",
        "chart_value_4",
        "chart_label_5",
        "chart_value_5",
        "chart_json",
        # 开场字幕卡 (hf_opening, 2026-08-11): 多行台词 + 关键冲击词
        "opening_lines_json",
        "opening_red_words",
        "opening_accent_words",
        # 财经片头 (hf_opening v3, 2026-08-11): hero/热词/副句/scatter
        "hero_text",
        "hot_word",
        "sub_text",
        "scatter_words",
        # 引用卡 (hf_quote, 2026-08-11): 一句话观点 + 出处/人物 + 人像
        "quote_text",
        "attrib_name",
        "attrib_role",
        "portrait_b64",
        "chart_head",
        "source",
        "duration_sec",
        # 品牌字段 (共享模板逐人设注入): 账号名/印章/标语 (2026-08-08)
        "brand_name",
        "stamp_name",
        "brand_tag",
    }
)

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def _build_substitutions(input_data: dict) -> dict[str, str]:
    """Build a ``{placeholder: value}`` dict from the validated input."""
    subs: dict[str, str] = {}
    subs["title"] = str(input_data.get("title", ""))
    subs["subtitle"] = str(input_data.get("subtitle", ""))
    subs["kicker"] = str(input_data.get("kicker", ""))
    metrics = input_data.get("metrics") or []
    for i in range(4):
        if i < len(metrics):
            m = metrics[i]
            subs[f"metric_label_{i+1}"] = str(m.get("label", ""))
            subs[f"metric_value_{i+1}"] = str(m.get("value", ""))
    chart = input_data.get("chart") or {}
    chart_items = chart.get("items") or []
    for i in range(5):
        if i < len(chart_items):
            c = chart_items[i]
            subs[f"chart_label_{i+1}"] = str(c.get("label", ""))
            subs[f"chart_value_{i+1}"] = str(c.get("value", ""))
    # 完整 chart 结构经 JSON 内联给模板 layout() 三模式自适应渲染 (2026-08-01)
    subs["chart_json"] = _html_escape(
        json.dumps(chart, ensure_ascii=False, separators=(",", ":"))
    )
    # 开场字幕卡 (hf_opening, 2026-08-11): 多行台词 + 强调词 (JSON 属性含引号, 须转义)
    subs["opening_lines_json"] = _html_escape(str(input_data.get("opening_lines_json", "[]")))
    subs["opening_red_words"] = _html_escape(str(input_data.get("opening_red_words", "[]")))
    subs["opening_accent_words"] = _html_escape(str(input_data.get("opening_accent_words", "[]")))
    # 财经片头 v3 参数
    subs["hero_text"] = _html_escape(str(input_data.get("hero_text", "")))
    subs["hot_word"] = _html_escape(str(input_data.get("hot_word", "")))
    subs["sub_text"] = _html_escape(str(input_data.get("sub_text", "")))
    subs["scatter_words"] = _html_escape(str(input_data.get("scatter_words", "[]")))
    # 引用卡参数
    subs["quote_text"] = _html_escape(str(input_data.get("quote_text", "")))
    subs["attrib_name"] = _html_escape(str(input_data.get("attrib_name", "")))
    subs["attrib_role"] = _html_escape(str(input_data.get("attrib_role", "")))
    subs["portrait_b64"] = _html_escape(str(input_data.get("portrait_b64", "")))
    subs["chart_head"] = str(chart.get("label") or chart.get("type") or "")
    subs["source"] = str(input_data.get("source", ""))
    subs["duration_sec"] = str(input_data.get("duration_sec", "12"))
    # 品牌字段: 共享模板不硬编码账号名, 由 input_data 注入 (2026-08-08)
    subs["brand_name"] = str(input_data.get("brand_name", ""))
    subs["stamp_name"] = str(input_data.get("stamp_name", ""))
    subs["brand_tag"] = str(input_data.get("brand_tag", ""))
    return subs


def _html_escape(text: str) -> str:
    """转义 HTML 特殊字符, 使 chart JSON 能安全内联到 <script> 节点内 (2026-08-01)."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _replace_placeholders(html: str, subs: dict[str, str]) -> str:
    def _sub(match: re.Match) -> str:
        key = match.group(1)
        if key in _SAFE_KEYS:
            return subs.get(key, "")
        return match.group(0)

    return _PLACEHOLDER_RE.sub(_sub, html)


def fill_template(
    template_dir: Path,
    template_id: str,
    input_data: dict,
    job_id: str,
) -> Path:
    """Copy the template files into the per-job workspace and substitute placeholders.

    Returns the workspace path.
    """
    cfg = get_config().defaults
    workspace = Path(cfg.hf_visual_root) / job_id
    workspace.mkdir(parents=True, exist_ok=True)

    template_dir = Path(template_dir)

    # 1. Copy template source files (whitelist: only index.html + avatar.b64).
    # Anything else in the template source directory is treated as non-essential
    # and skipped — prevents stale demo artefacts (e.g. test_news_b64.mp4) from
    # being dragged into the job workspace.
    _TEMPLATE_FILE_WHITELIST = {"index.html", "avatar.b64"}
    for name in _TEMPLATE_FILE_WHITELIST:
        src = template_dir / name
        if src.is_file():
            shutil.copy2(src, workspace / name)

    # 2. Write input.json — authoritative record of what was rendered
    (workspace / "input.json").write_text(
        json.dumps(input_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 3. Substitute placeholders inside index.html (only whitelisted keys)
    html_path = workspace / "index.html"
    html = html_path.read_text(encoding="utf-8")
    subs = _build_substitutions(input_data)
    html = _replace_placeholders(html, subs)
    html_path.write_text(html, encoding="utf-8")

    return workspace