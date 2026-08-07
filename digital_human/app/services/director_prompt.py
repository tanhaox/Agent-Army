"""Director prompt loading and building."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import PROJECT_ROOT
from app.models import VideoAsset
from app.schemas import get_video_format_spec

logger = logging.getLogger(__name__)

VISUAL_DIRECTOR_V2_PATH = PROJECT_ROOT / "config" / "visual_director_v2.txt"


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



def load_director_prompt() -> str:
    """Load the v2 director system prompt from disk."""
    if VISUAL_DIRECTOR_V2_PATH.exists():
        return VISUAL_DIRECTOR_V2_PATH.read_text(encoding="utf-8").strip()
    return (
        "你是一位资深财经短视频视觉导演。请为每句口播输出精确的画面方案，"
        "最终输出纯 JSON 数组，每个元素包含 line_id/text/visual_type/intensity/emotion 字段。"
    )


def _build_pipeline_constraint_block(enabled_pipelines: set[str] | None) -> str:
    """Build a constraint block telling the LLM which pipelines are disabled."""
    if enabled_pipelines is None:
        return ""  # 全部启用, 不需要约束

    all_pipelines = {"c": ("C线 ComfyUI", ["host", "mixed_host_broll"]),
                     "p": ("P线 Pexels", ["broll_pexels"]),
                     "h": ("H线 HuggingFace", ["hf_chart", "hf_title"])}

    disabled: list[str] = []
    forbidden_workflows: list[str] = []
    for tag, (label, wfs) in all_pipelines.items():
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

    return "\n".join(lines)


_NO_HOST_DEMO = """```json
{
  "video_title": "刚刚,海关公布:上半年进口10.74万亿,增长22.1%",
  "slots": [
    {
      "slot_index": 0,
      "start_sec": 0.00,
      "end_sec": 4.20,
      "text_context": "大家好,我是老陈。||在这个不确定的时代,||希望能给你一点确定的逻辑。||",
      "segment_id": "seg-001",
      "visual_type": "hf_title",
      "workflow": "hf_title",
      "params": {"render_config": {"title": "上半年进口 10.74 万亿", "subtitle": "增长 22.1%"}, "intensity": "low", "emotion": "opening"}
    },
    {
      "slot_index": 1,
      "start_sec": 4.20,
      "end_sec": 7.50,
      "text_context": "今天咱们聊的话题,||来自人民日报的报道。||",
      "segment_id": "seg-002",
      "visual_type": "broll_pexels",
      "workflow": "broll_pexels",
      "params": {
        "keywords": ["china", "city", "street", "people", "traffic"],
        "category": "城市街景",
        "intensity": "low",
        "emotion": "opening"
      }
    },
    {
      "slot_index": 2,
      "start_sec": 7.50,
      "end_sec": 11.00,
      "text_context": "说三个数字,||听完您就知道钱该往哪儿投。||",
      "segment_id": "seg-003",
      "visual_type": "hf_title",
      "workflow": "hf_title",
      "params": {"render_config": {"title": "说三个数字", "subtitle": "钱该往哪儿投"}, "intensity": "medium", "emotion": "rising"}
    },
    {
      "slot_index": 3,
      "start_sec": 11.00,
      "end_sec": 16.40,
      "text_context": "上半年进口10.74万亿元,||增长22.1%。||",
      "segment_id": "seg-004",
      "visual_type": "hf_chart",
      "workflow": "hf_chart",
      "params": {
        "render_config": {
          "chart_type": "pie_chart",
          "data": [
            {"label": "进口额(万亿元)", "value": 10.74},
            {"label": "增长(%)", "value": 22.1}
          ],
          "label": "进口额(万亿元)",
          "unit": "万亿",
          "growth": "22.1%",
          "color_scheme": "黑金"
        },
        "intensity": "high",
        "emotion": "rising"
      }
    },
    {
      "slot_index": 4,
      "start_sec": 16.40,
      "end_sec": 21.80,
      "text_context": "中国连续17年,||稳坐全球第二大进口市场。||",
      "segment_id": "seg-005",
      "visual_type": "broll_pexels",
      "workflow": "broll_pexels",
      "params": {
        "keywords": ["china", "port", "shipping", "containers"],
        "category": "港口",
        "intensity": "high",
        "emotion": "climax"
      }
    },
    {
      "slot_index": 5,
      "start_sec": 21.80,
      "end_sec": 25.50,
      "text_context": "您最近买到便宜的进口货了吗?||评论区聊聊。||",
      "segment_id": "seg-006",
      "visual_type": "hf_title",
      "workflow": "hf_title",
      "params": {"render_config": {"title": "评论区聊聊", "subtitle": "您买到便宜进口货了吗"}, "intensity": "low", "emotion": "closing"}
    },
    {
      "slot_index": 6,
      "start_sec": 25.50,
      "end_sec": 30.00,
      "text_context": "关注我,看懂财经。||下期见。||",
      "segment_id": "seg-007",
      "visual_type": "hf_title",
      "workflow": "hf_title",
      "params": {"render_config": {"title": "关注我,看懂财经", "subtitle": "下期见"}, "intensity": "low", "emotion": "closing"}
    }
  ]
}
```"""


def _strip_host_mode(prompt: str) -> str:
    """无出镜模式: C 线禁用时把导演系统提示词里的数字人 host 强制规则裁剪掉。

    核心问题 (2026-08-07): visual_director_v2.txt 是"数字人优先"的导演系统,
    约 40 处写死 host/老陈出镜 (规则1/2/2.5/3/4.3/4.4、自检清单、示例、注意
    事项)。之前只靠 _build_pipeline_constraint_block 注入"管线限制"约束块——
    那只是压在系统提示词上的一道"软封印", LLM 面对写死的 host 规则时封印极易
    失效, 导致即便用户只开 P/H 线仍规划出 host slot。

    本次修复在系统提示词这一层直接按 C 线禁用移除 host 内容, 让"无出镜"成为
    不可违背的系统规则而非提示块。此函数按 visual_director_v2.txt 的实际章节
    结构做整节替换 (比逐行正则稳健, 换行/中文引号不影响)。
    """
    import re

    # ── 1) 映射表: 删掉 host / mixed_host_broll 两行 ──
    prompt = re.sub(r"^\| `host` \| `host` \|.*\|\n", "", prompt, flags=re.M)
    prompt = re.sub(r"^\| `mixed_host_broll` \| `mixed_host_broll` \|.*\|\n", "", prompt, flags=re.M)

    # ── 2) params 字段约定: 删掉 host / mixed_host_broll 两段 ──
    prompt = re.sub(r"\*\*host\*\*: `\{.*?\}`\n\n", "", prompt, flags=re.S)
    prompt = re.sub(r"\*\*mixed_host_broll\*\*:.*?\n\n", "", prompt, flags=re.S)

    # ── 3) 规则1 画面类型判断 → 整表换无出镜版 ──
    _rule1 = (
        "| 条件 | visual_type | 理由 |\n"
        "|---|---|---|\n"
        "| 包含\"大家好\"/\"我是老陈\"/\"下期见\"等开场结尾词 | `hf_title` | 标题卡建立画面识别 |\n"
        "| 包含\"评论区聊聊\"/\"您觉得呢\"等互动提问 | `hf_title` | 提问卡承接互动 |\n"
        "| 包含金句/结论/观点性陈述 | `hf_title` / `broll_pexels` | 大字标题+画面传递观点 |\n"
        "| 包含具体数字、百分比、金额、年份 | `broll_pexels` | 用真实画面做数据背景 |\n"
        "| 引用外部事件、历史案例、他国情况 | `broll_pexels` | 需要画面建立场景 |\n"
        "| 核心结论 + 关键数据同时出现 | `hf_chart` | 图表承载数据,信息密度最大 |\n"
        "| 一般叙述/过渡/补充说明 | `broll_pexels` | **默认首选**, 真实画面观感最佳 |"
    )
    prompt = re.sub(
        r"## 规则1:画面类型判断\(visual_type\)\n\n\| 条件.*?(?=\n## 规则2：节奏控制)",
        "\n## 规则1:画面类型判断(visual_type)\n\n" + _rule1,
        prompt, flags=re.S,
    )

    # ── 4) 规则2 节奏控制 → 整表换无出镜版 ──
    _rule2 = (
        "| 规则 | 要求 |\n"
        "|---|---|\n"
        "| **`hf_*` 不得相邻** | 任何两个 `hf_chart`/`hf_title` slot 不能紧挨着, 中间必须插入 `broll_*` |\n"
        "| **`broll_*` 为主力** | 全片以 `broll_pexels` 为主画面, `hf_*` 做节奏点缀 |\n"
        "| **无出镜模式(硬性)** | 本片为无出镜(无数字人)模式, **严禁规划任何出镜 slot** |\n"
        "| `broll_*` / `hf_*` 连续不超过 4 行 | 连续 4 行以上素材,画面单调 |\n"
        "| 每段开头第 1 个 slot 用 `broll_*` 或 `hf_*` | 建立段落感 |\n"
        "| 整段最后一个 slot 用 `hf_title` 或 `broll_*` | 收束感,给观众消化时间 |\n"
        "| 全场高潮点(最核心数据/最强金句)必须用 `hf_chart` | 信息密度拉到最大 |\n"
        "| 开场前 3 个 slot：`broll_* → hf_title → broll_*` | 建立连接→制造好奇→抛出悬念 |"
    )
    prompt = re.sub(
        r"## 规则2：节奏控制（硬性约束）\n\n\| 规则.*?(?=\n## 规则2\.5)",
        "\n## 规则2：节奏控制（硬性约束）\n\n" + _rule2,
        prompt, flags=re.S,
    )

    # ── 5) 规则2.5 机位分配 (仅 host/mixed) → 整节替换 ──
    prompt = re.sub(
        r"## 规则2\.5：机位分配.*?(?=\n## 规则3:信息密度匹配)",
        "\n## 规则2.5：机位分配（已废弃 — 本片无出镜）\n\n无出镜模式下不需要 host 机位。`broll_*` / `hf_*` 不输出 camera 字段。",
        prompt, flags=re.S,
    )

    # ── 6) 规则3 信息密度匹配 → 整表换无出镜版 ──
    _rule3 = (
        "| 信息层级 | 视觉类型 |\n"
        "|---|---|\n"
        "| 轻信息(观点/金句/互动) | `hf_title` / `broll_pexels` |\n"
        "| 中信息(单一数据/单一事实) | `broll_local` / `broll_pexels` / `hf_chart` |\n"
        "| 重信息(多数据对比/因果逻辑/核心结论) | `hf_chart` |"
    )
    prompt = re.sub(
        r"## 规则3:信息密度匹配\n\n\| 信息层级.*?(?=\n## 规则4:素材选择策略)",
        "\n## 规则3:信息密度匹配\n\n" + _rule3,
        prompt, flags=re.S,
    )

    # ── 7) 规则4.3 / 4.4 → 替换降级链与混合场景说明 ──
    prompt = prompt.replace(
        "### 4.3 清单中该 category 不存在 → 改用 `broll_pexels`(再降级为 host)\n按 broll_pexels → broll_local → host 的优先级降级。宁可让老陈出镜,也不配错画面。",
        "### 4.3 清单中该 category 不存在 → 改用 `broll_pexels`(再降级为 broll_local/hf_chart)\n按 broll_pexels → broll_local → hf_chart 的优先级降级。本片无出镜,宁可配标题卡,也不插入出镜。",
    )
    prompt = re.sub(
        r"### 4\.4 混合场景的素材选择.*?(?=\n## 规则5:全局画面一致性)",
        "### 4.4 重信息场景的素材选择\n核心结论/数据高潮用 `hf_chart` 承载, 配合 `broll_pexels` 数据背景画面\n→ 选择画面对比度高、信息密度大的素材\n→ 优先选航拍/大场景/图表,避免选择人物特写",
        prompt, flags=re.S,
    )

    # ── 8) 输出示例 → 整块换无出镜示例 ──
    prompt = re.sub(
        r"# 输出示例\n\n```json.*?```\n",
        "# 输出示例\n\n" + _NO_HOST_DEMO + "\n",
        prompt, flags=re.S,
    )

    # ── 9) 自检清单 → 删除 host 相关检查项 ──
    for line in [
        "- [ ] `host` 连续 slot 是否超过 3 个?",
        "- [ ] 每 5 个 slot 至少 1 次 `host`?",
        "- [ ] 第一个 slot 是否是 `host`?",
        "- [ ] 最后一个 slot 是否是 `host`?",
        "- [ ] 核心数据/最强金句 slot 是否用了 `mixed_host_broll`?",
        "- [ ] 开场前 3 个 slot 是否是 `host → broll_* → host`?",
        "- [ ] **是否有两个 `host` slot 紧挨着？**（不允许）",
    ]:
        prompt = prompt.replace(line + "\n", "")

    # ── 10) 注意事项 → 替换 host 相关条目 ──
    prompt = prompt.replace(
        "2. **素材不足用 host 补**:宁可多让老陈说话,也不配错画面。",
        "2. **素材不足用 hf_title 补**:宁可让标题卡承接,也不插入出镜。",
    )
    prompt = prompt.replace(
        "3. **mixed_host_broll 要克制**:全篇不超过 3 处,只在最核心的位置使用。",
        "3. **画面要克制**:全片不留纯黑屏,用 hf_title/broll 交替填充。",
    )
    prompt = prompt.replace(
        "4. **保持节奏感**:`host` 和 `broll_*` 交替进行,就像对话中的\"你说我听,我看你说\"。",
        "4. **保持节奏感**:`broll_*` 和 `hf_*` 交替进行,画面随口播推进。",
    )

    # ── 11) 核心能力描述 ──
    prompt = prompt.replace(
        "懂得出镜、素材、混合三种画面类型的交替频率,让观众既不疲劳也不走神。",
        "懂得画面素材与动态图表卡片的交替频率,让观众既不疲劳也不走神。",
    )

    # ── 12) 兜底: 删除任何残留含 host 的行 (broll_* / hf_* 均不含该词) ──
    prompt = re.sub(r"^.*\b(?:host|mixed_host_broll)\b.*\n", "", prompt, flags=re.M)
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)
    prompt = prompt.replace("老陈出镜", "画面呈现")
    return prompt.strip()


def build_director_prompt(
    script_text: str,
    segment_timings: list[dict[str, Any]],
    material_catalog: dict[str, Any] | None = None,
    video_format: str | None = None,
    script_title: str | None = None,
    enabled_pipelines: set[str] | None = None,
) -> str:
    """Assemble user prompt for the director LLM.

    Args:
        enabled_pipelines: 启用的管线集合 (e.g. {"c","p","h"}). None=全部启用.
    """
    prompt = load_director_prompt()
    # 无出镜模式: C 线禁用 (用户只开 P/H 或全关) 时, 直接在系统提示词层移除 host 规则
    if enabled_pipelines is not None and "c" not in enabled_pipelines:
        prompt = _strip_host_mode(prompt)
    prompt = prompt.replace("[在此处粘贴原文标题]", (script_title or "").strip())
    prompt = prompt.replace("[在此处粘贴口播脚本]", script_text.strip())

    # 画幅上下文 (2026-08-01): 导演规划必须知道当前横/竖/方, 才能按画幅选构图词
    prompt += _format_frame_spec(video_format)

    catalog = material_catalog or mock_material_catalog()
    prompt = prompt.replace(
        "[在此处粘贴素材库清单JSON]",
        json.dumps(catalog, ensure_ascii=False, indent=2),
    )

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

    return prompt


def build_real_material_catalog(db: Session) -> dict[str, Any]:
    """从 VideoAsset 表构建真实素材库目录，供导演 LLM 规划参考。

    按 scenes[0]（主场景）分组，同组内列出素材文件、tags、AI 多维标签。
    额外添加"数据图表"/"标题卡"动态渲染入口。
    DB 查询失败或素材库为空时 fallback 到 mock。
    """
    try:
        assets = (
            db.query(VideoAsset)
            .filter(VideoAsset.file_path.isnot(None))
            .order_by(VideoAsset.ai_tagged_at.desc().nullslast(), VideoAsset.used_count.asc())
            .all()
        )
    except Exception:
        logger.exception("build_real_material_catalog: DB query failed, using mock")
        return mock_material_catalog()

    if not assets:
        logger.warning("build_real_material_catalog: no VideoAsset found, using mock")
        return mock_material_catalog()

    # 按主场景分组
    grouped: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        primary_scene = (asset.scenes or ["未分类"])[0]
        grouped.setdefault(primary_scene, []).append({
            "file": Path(asset.file_path).name if asset.file_path else "",
            "tags": asset.tags or [],
            "description_zh": (asset.description_zh or "")[:40],
            "tone": (asset.ai_tags_extra or {}).get("tone"),
            "motion_level": (asset.ai_tags_extra or {}).get("motion_level"),
            "content_density": (asset.ai_tags_extra or {}).get("content_density"),
            "time_of_day": (asset.ai_tags_extra or {}).get("time_of_day"),
            "orientation": asset.orientation,
            "_has_ai_tags": (asset.ai_tags_extra or {}).get("tone") is not None,
            "_used_count": asset.used_count or 0,
        })

    # 性能守卫 (2026-08-07): 素材库可能上千条, 全量塞进 LLM prompt 会让
    # 单次调用达到数百 KB → 120s 超时 + 重试, 规划变 4 分钟。
    # 每个场景只保留 top-N 条 (AI 标签优先, 其次 used_count 低), 并截断
    # 未使用的辅助字段。LLM 规划实际只用清单里少数条目, 裁剪不损失质量。
    _MAX_ITEMS_PER_SCENE = 8

    catalog: dict[str, Any] = {}
    for scene, items in sorted(grouped.items()):
        # 排序: 有 AI 标签优先, 其次 used_count 低 (先排 used_count 升序, 再按标签分组)
        items_sorted = sorted(items, key=lambda i: i["_used_count"])
        ai_tagged = [i for i in items_sorted if i["_has_ai_tags"]]
        others = [i for i in items_sorted if not i["_has_ai_tags"]]
        chosen = (ai_tagged + others)[:_MAX_ITEMS_PER_SCENE]
        for c in chosen:
            c.pop("_has_ai_tags", None)
            c.pop("_used_count", None)
        # 默认推荐: 有 AI 标签的优先，used_count 低的优先
        default_item = (ai_tagged or chosen)[0] if (ai_tagged or chosen) else None
        catalog[scene] = {
            "素材列表": chosen,
            "默认推荐": default_item["file"] if default_item else None,
            "素材数量": len(chosen),
            "素材总数": len(items),  # 提示 LLM 该场景还有更多素材
        }

    # 始终追加动态渲染入口
    catalog["数据图表"] = {"素材列表": [], "默认推荐": None, "动态渲染": True}
    catalog["标题卡"] = {"素材列表": [], "默认推荐": None, "动态渲染": True}

    logger.info(
        "build_real_material_catalog: %d scenes, %d assets",
        len(catalog) - 2, len(assets),
    )
    return catalog


def mock_material_catalog() -> dict[str, Any]:
    """最小化兜底目录 — 仅在 DB 异常或无素材时使用。"""
    return {
        "港口": {
            "素材列表": [
                {"file": "港口_001.mp4", "tags": ["港口", "集装箱", "货轮", "航拍"]},
            ],
            "默认推荐": "港口_001.mp4",
        },
        "工厂": {
            "素材列表": [
                {"file": "工厂_001.mp4", "tags": ["生产线", "机械臂", "智能制造"]},
            ],
            "默认推荐": "工厂_001.mp4",
        },
        "城市": {
            "素材列表": [
                {"file": "城市_001.mp4", "tags": ["CBD", "商业", "都市"]},
            ],
            "默认推荐": "城市_001.mp4",
        },
        "数据图表": {
            "素材列表": [],
            "默认推荐": None,
            "动态渲染": True,
        },
        "标题卡": {
            "素材列表": [],
            "默认推荐": None,
            "动态渲染": True,
        },
    }
