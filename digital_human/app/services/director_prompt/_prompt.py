"""Director prompt — 用户提示词装配 (导演 LLM 输入构建).

build_director_prompt 是编排函数 (压线 ≤70 不拆): 无出镜裁剪 → 画幅 →
catalog_mode 判定 → 词表/全量 JSON → 选词约束 → timing → 管线约束。
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import get_config
from app.schemas import get_video_format_spec
from app.services.director_prompt._constants import (
    HARD_DIMENSIONS,
    LOCATION_VALUES,
    ORIENTATION_VALUES,
    PEOPLE_VALUES,
    SOFT_DIMENSIONS,
    VISUAL_DIRECTOR_V2_PATH,
    VOCABULARY_PACK_PATH,
)
from app.services.director_prompt._catalog import mock_material_catalog
from app.services.director_prompt._strip_host import strip_host_mode
from app.services.director_prompt._vocabulary import load_vocabulary_pack

logger = logging.getLogger(__name__)

__all__ = ["build_director_prompt", "load_director_prompt"]


# ── 管线映射: 标签 → (中文名, 工作流列表) ──
_PIPELINE_MAP: dict[str, tuple[str, list[str]]] = {
    "c": ("C线 ComfyUI", ["host", "mixed_host_broll"]),
    "p": ("P线 Pexels", ["broll_pexels"]),
    "h": ("H线 HuggingFace", ["hf_chart", "hf_title"]),
}


def load_director_prompt() -> str:
    """Load the v2 director system prompt from disk."""
    if VISUAL_DIRECTOR_V2_PATH.exists():
        return VISUAL_DIRECTOR_V2_PATH.read_text(encoding="utf-8").strip()
    return (
        "你是一位资深财经短视频视觉导演。请为每句口播输出精确的画面方案，"
        "最终输出纯 JSON 数组，每个元素包含 line_id/text/visual_type/intensity/emotion 字段。"
    )


def _format_frame_spec(video_format: str | None) -> str:
    """Return the frame-format block injected into the director prompt.

    横/竖/方 三种画幅给 LLM, 让它按画幅选 broll 构图词 (2026-08-01).
    """
    spec = get_video_format_spec(video_format)
    fmt = video_format or "portrait"
    lines = [
        f"\n\n## 补充输入4：本片画幅规格（硬性，选择 broll 构图时必须遵守）",
        f"当前画幅: {fmt}（{spec['label']}），输出分辨率 {spec['width']}x{spec['height']}。",
    ]
    if fmt == "portrait":
        lines.append("- 竖屏（当前画幅）: broll 素材必须是竖向构图(如高层楼宇、竖版街道、人物全身), 禁止横向宽景; keywords 用竖向主体词。")
        lines.append("- 横屏: broll 素材是横向宽景构图(城市天际线/公路/大海), keywords 用横向场景词。")
    elif fmt == "landscape":
        lines.append("- 横屏（当前画幅）: broll 素材必须是横向宽景构图(如城市天际线、公路、大海), 禁止竖向特写; keywords 用横向场景词(如 skyline/landscape)。")
        lines.append("- 竖屏: broll 素材是竖向构图(高层楼宇/街道/人物全身), keywords 用竖向主体词。")
    else:
        lines.append("- 方形（当前画幅）: broll 素材构图居中均衡, 主体不要贴边; keywords 用居中主体词。")
    lines.append(f"当前画幅是 **{fmt}**，所有 broll_pexels 的 keywords 必须选与该画幅匹配的构图词。")
    return "\n".join(lines)


def _pipeline_substitution_lines(
    forbidden_workflows: list[str],
    enabled_pipelines: set[str],
) -> list[str]:
    """替代方案指引 — 按被禁工作流 + 仍启用管线组合出可替代视觉."""
    lines: list[str] = []
    if "host" in forbidden_workflows and "mixed_host_broll" in forbidden_workflows:
        if "h" in enabled_pipelines:
            lines.append("- 开场/收尾用 hf_title 替代 host 出镜")
        elif "p" in enabled_pipelines:
            lines.append("- 开场/收尾用 broll_pexels 替代 host 出镜")
        else:
            lines.append("- 开场/收尾用 broll_local 替代 (本地素材兜底)")
    if "broll_pexels" in forbidden_workflows:
        if "c" in enabled_pipelines:
            lines.append("- 需要空镜时用 mixed_host_broll 替代 broll_pexels")
        elif "h" in enabled_pipelines:
            lines.append("- 需要空镜时用 hf_chart 替代 broll_pexels")
        else:
            lines.append("- 需要空镜时用 broll_local 替代")
    if "hf_chart" in forbidden_workflows and "hf_title" in forbidden_workflows:
        if "c" in enabled_pipelines:
            lines.append("- 数据可视化/标题卡用 host 出镜替代")
        else:
            lines.append("- 数据可视化/标题卡用 broll_local 替代")
    return lines


def _build_pipeline_constraint_block(enabled_pipelines: set[str] | None) -> str:
    """Build a constraint block telling the LLM which pipelines are disabled."""
    if enabled_pipelines is None:
        return ""  # 全部启用, 不需要约束

    disabled: list[str] = []
    forbidden_workflows: list[str] = []
    for tag, (label, wfs) in _PIPELINE_MAP.items():
        if tag not in enabled_pipelines:
            disabled.append(f"- {label} → 禁止工作流: {', '.join(wfs)}")
            forbidden_workflows.extend(wfs)

    if not disabled:
        return ""

    lines = [
        "\n\n## 管线限制（硬性约束 — 必须遵守！）",
        f"以下管线已被用户禁用，**绝对不能**为这些管线生成 slot:",
        *disabled,
        "",
        "**替代方案指引**:",
    ]
    lines.extend(_pipeline_substitution_lines(forbidden_workflows, enabled_pipelines))
    return "\n".join(lines)


def _format_vocabulary_constraint_block() -> str:
    """词表包模式下追加的选词硬约束（broll_local 全维度词表选词; broll_pexels keywords 自由）。

    解耦 (2026-08-09): broll_local 的 9 维度 + keywords 从词表包选词;
    broll_pexels 的 keywords 是**自由画面搜索词**, 不受词表限制 (专有名词/
    实时事件词如 特朗普/伊朗 允许), 仅 9 维度若输出仍需从词表包对应分组取
    ——9 维度只供本地素材优先碰撞用, 不参与 Pexels 下载搜索。
    """
    return (
        "\n\n## 补充输入2说明：关键词词表包选词规则（硬性）\n"
        "素材库以**按维度分组的词表包**提供（而非全量清单），每个维度 1~N 个可检索词。\n"
        f"- 硬维度（{ '、'.join(HARD_DIMENSIONS) }）：选词必须严格取该维度枚举值，用于本地硬过滤。\n"
        f"- 软维度（{ '、'.join(SOFT_DIMENSIONS) }）：从词表包对应分组选词。\n"
        f"- **broll_local 的 params 必须输出全部 9 个维度**"
        f"（{ '、'.join(HARD_DIMENSIONS) } + { '、'.join(SOFT_DIMENSIONS) }），"
        "每维度最少 1-2 个词（scenes/shot_types 最少 1 个；location/orientation/people/tone/motion_level/content_density/time_of_day 最少 1 个），keywords 也从词表包 keywords 分组取。\n"
        "- **broll_pexels 的 keywords 是自由画面搜索词**，不受词表限制：可用词表外词（专有名词/实时事件/具体画面，如 特朗普、伊朗、雨后街道），第 1 个必须是全局主体关键词（规则5）；location/people 可选硬维度用于定向；**必须同时输出 9 维度**（scenes/shot_types/tone/motion_level/content_density/time_of_day，词从词表包对应分组取，与 broll_local 同格式），供本地素材优先碰撞命中——9 维度不参与 Pexels 下载搜索，不会限制在线下载；缺 9 维度则本地碰撞直接跳过（P 线全部下载）。\n"
        "- hard 维度只允许枚举值"
        f"（location: {'/'.join(LOCATION_VALUES)}，orientation: {'/'.join(ORIENTATION_VALUES)}，people: {'/'.join(PEOPLE_VALUES)}）。\n"
        "- 词不得互相冲突：location 为 domestic 的 slot 不得再出现 foreign 词；全片地域语义必须与口播一致（讲中国产业链绝不允许 foreign）。\n"
        "- 本地匹配会做硬维度过滤 + 软维度 ≥75% 命中率校验；broll_local 选词不全或词不在包内会导致本地碰撞不达标，下游自动转 broll_pexels 在线下载。\n"
    )


def build_director_prompt(
    script_text: str,
    segment_timings: list[dict[str, Any]],
    material_catalog: dict[str, Any] | None = None,
    video_format: str | None = None,
    script_title: str | None = None,
    enabled_pipelines: set[str] | None = None,
    visual_intent: list[dict[str, Any]] | None = None,
    visual_theme: str | None = None,
) -> str:
    """Assemble user prompt for the director LLM.

    Args:
        enabled_pipelines: 启用的管线集合 (e.g. {"c","p","h"}). None=全部启用.
        visual_intent: 可选, 稿件结构意图 (钩子/预埋/回收/呼吸点/金句 → 建议画面情绪).
            从爆品改造稿的结构标记提取, 让导演按"观众实际听到的新稿 + 结构意图"配画面, 而非盲配.
        visual_theme: 可选, 人物级视觉主题 (persona.visual_theme, 如科技/地缘场景词).
            导演按此选全局主体关键词, 替代默认地域词.
    """
    prompt = load_director_prompt()
    # 无出镜模式: C 线禁用 (用户只开 P/H 或全关) 时, 直接在系统提示词层移除 host 规则
    if enabled_pipelines is not None and "c" not in enabled_pipelines:
        prompt = strip_host_mode(prompt)
    prompt = prompt.replace("[在此处粘贴原文标题]", (script_title or "").strip())
    prompt = prompt.replace("[在此处粘贴口播脚本]", script_text.strip())

    # 画幅上下文 (2026-08-01): 导演规划必须知道当前横/竖/方, 才能按画幅选构图词
    prompt += _format_frame_spec(video_format)

    # 输入2 (ID-034): catalog_mode 判定。config 未加载(脚本直接调用)时用默认 "vocabulary";
    # 显式 "full" 才注入全量 catalog, 其余(默认/未知)一律走词表包。
    catalog_mode = "vocabulary"
    try:
        if get_config().defaults.director_catalog_mode == "full":
            catalog_mode = "full"
    except Exception:
        pass  # config 未加载 → 保持默认 vocabulary

    if catalog_mode == "vocabulary":
        pack = load_vocabulary_pack()
        # 词表包文件缺失(首次部署/尚未打标) → fallback 全量 catalog, 保证 prompt 仍可用
        if pack is None:
            logger.warning(
                "catalog_mode=vocabulary but pack missing (%s), falling back to full catalog",
                VOCABULARY_PACK_PATH,
            )
            catalog = material_catalog or mock_material_catalog()
            catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)
        else:
            catalog_json = json.dumps(pack, ensure_ascii=False, indent=2)
    else:
        catalog = material_catalog or mock_material_catalog()
        catalog_json = json.dumps(catalog, ensure_ascii=False, indent=2)
    prompt = prompt.replace(
        "[在此处粘贴素材库清单JSON]",
        catalog_json,
    )

    # 词表包模式下补充选词约束（全维度 + 每维度 ≥1-2 词）
    if catalog_mode == "vocabulary":
        prompt += _format_vocabulary_constraint_block()

    timing_json = json.dumps(segment_timings, ensure_ascii=False, indent=2)
    prompt += (
        "\n\n## 补充输入3：每句口播的真实起止时间（秒）\n"
        "导演规划时必须保证每个 slot 的 start/end 落在这些真实时间范围内，"
        "不要超出音频总时长。\n" + timing_json
    )

    # 管线约束 (2026-08-03): 告诉 LLM 哪些管线禁用, 避免生成无效 slot
    constraint = _build_pipeline_constraint_block(enabled_pipelines)
    if constraint:
        prompt += constraint

    # 视觉意图注入 (2026-08-11): 把爆品改造稿的结构意图传给导演, 让它按
    # "观众实际听到的新稿 + 每段意图"配画面, 而非盲配. 这是视觉层"导演盲盒"的解法.
    if visual_intent:
        intent_lines = [
            "\n\n## 补充输入4：每段的视觉意图（稿件结构标记 → 建议画面情绪）",
            "这是对口播稿的结构分析。请你配画面时严格呼应这些意图：",
            "- 钩子/冲击段 → 画面要硬、有冲击力/悬念感，禁止蓝天白云/风景空镜",
            "- 争议/预埋段 → 画面要有张力/暗调/暗示，配合埋伏笔的悬念感",
            "- 回收/升华段 → 画面要收束/提升/光明",
            "- 呼吸点 → 画面要放松/留白，让观众缓口气",
            "- 金句/结论 → 画面要突出/定格，可配大字",
            "",
            "各段意图（按时间顺序）：",
        ]
        for item in visual_intent:
            start = item.get("start_sec", "?")
            intent = item.get("intent", "body")
            desc = item.get("desc", "")
            intent_lines.append(f"- [{start}s] {intent}: {desc}")
        prompt += "\n".join(intent_lines)

    # 人物级视觉主题注入 (2026-08-11): persona.visual_theme 决定全局主体关键词方向
    # (老谭聊科技 → server room/datacenter; 老谭聊地缘 → world map/geopolitics)
    if visual_theme:
        prompt += (
            "\n\n## 补充输入5：人物视觉主题（全局主体关键词方向）\n"
            f"当前账号的视觉主题是：**{visual_theme}**\n"
            "全局主体关键词（规则5.1）必须从该主题取场景词，禁止用地域/城市词替代。"
        )

    return prompt
