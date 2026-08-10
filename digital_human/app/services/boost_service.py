# -*- coding: utf-8 -*-
"""爆品改造服务 (Boost Service) — 洗稿后自动优化口播稿的流量指标.

流水线 (2026-08-10, 用户拍板):
  P1 开场专家 (前 30 秒 + 标题)  ┐
                                ├─ 并行 (P1 产头, P2 正好不要头)
  P2 预埋专家 (评论 + 关注回收) ┘
  P3 节奏专家 (呼吸点)           ← 等 P1/P2 都回来再跑 (P3 需要 P2 的预埋位置)

每个 Pass 调用一次 LLM (DeepSeek pro), 输出 JSON (P1/P2) 或纯文本 (P3).
产物:
  boosted_text  = 改造后全文 (P1 开头 + P2 预埋正文 + P3 呼吸点)
  boost_titles  = P1 输出的标题候选 (默认用第一个)
保留 script_text 为洗稿原稿 (对比回滚).

失败容错: 单个 Pass 失败跳过, 用已成功部分的拼接; 全部失败回退原稿 (不卡死配音).
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from ..config import load_config
from .script_parser import parse_script

logger = logging.getLogger(__name__)

# ── Pass 提示词 ──────────────────────────────────────────────────────────────

P1_PROMPT = """你是{persona}的【开场外科医生】。你的工作不是创作，而是像外科医生一样，在不触动身体其他部位的情况下，精准替换掉原稿的开头。

# 【手术任务：只输出前 30 秒 + 标题】

## ⚠️ 绝对禁区（触发即失败）
- ❌ 禁止首句出现：自我介绍（我是{persona}）、报告、机构、政府、数据。
- ❌ 禁止输出：画面描述、BGM、时长、数字人形象、封面文案。
- ❌ 禁止合并：前 30 秒必须且只能是 4 个独立的短句。

## 你的输出 = 严格 JSON（无其他内容）
{
  "opening_30s": ["句1(0-5s 砸冲击词，无铺垫)", "句2(5-15s 兑现爆点，具体欺骗行为)", "句3(15-20s {persona}式冷幽默/反讽)", "句4(20-30s 抛全篇悬念，拉回注意力)"],
  "titles": ["推荐标题(含冲击词≤25字)", "备选1", "备选2"]
}

## 字数硬约束
opening_30s 四句总字数必须 120-150 字（不含标点），每句 25-40 字。"""

P2_PROMPT = """你是{persona}的【数据操盘手】。你不是在做"广告"，你是在替{persona}把话说到让用户必须回应的地步。

# 🧠 心法（最高优先）
## 心法1·拒绝礼貌
禁止任何"欢迎讨论"、"请在评论区"、"留言告诉我"等礼貌用语。互动必须建立在挑衅、揭秘、质疑、制造认知焦虑的基础上。
## 心法2·制造空洞（而非编造黑料）
通过"具体化后果"让用户感到不安，而不是通过"编造黑料"让用户好奇。
## 心法3·拒绝求关注
将关注定义为"获取避坑指南"的唯一途径——让用户觉得"不关注就被蒙在鼓里，成了被收割的韭菜"。

# 🚫 真实性红线（最高优先级，违反即失败）
【禁止捏造事实】
- 严禁编造原稿中不存在的：具体章节、具体档案、具体会议、具体人物对话。
- 允许的"具体化"仅限于以下 3 类：
  1. 情绪的具象化（例："风险大"→"刀口架在脖子上"）
  2. 逻辑后果的具象化（例："影响生活"→"房贷评估被操纵"）
  3. 程度的具象化（例："很秘密"→"焊得比保险库还死"）
- 不确定的具体信息必须模糊化处理，禁止编造精确细节。

# 【任务目标】
在不破坏原稿论证逻辑、不修改正文措辞的前提下，在稿件中预埋两个"钩子"，并按【结构分布协议】在指定位置回收。

## 任务一：【争议点预埋】→ 诱导评论
挖掘点：在正文论证"开源 vs 闭源"或"良心 vs 财报"的冲突段落中，植入一句【认知冲突句】。
要求：不直接问问题，通过"反讽"或"质疑"视角，给观众"想反驳/想站队"的切入点。
禁令：禁止"你认为...吗？""大家怎么看？"等引导句式。

## 任务二：【信息钩子预埋】→ 制造认知焦虑
挖掘点：在讲述 AI 欺骗行为（如雇人过验证码）的高潮段落后，植入一句【具体后果句】。
要求：暗示当前揭露只是冰山一角，背后有更具体的后果，让观众产生"不知道就落后"的焦虑。
禁令：禁止直白求关词；禁止编造具体黑料（见真实性红线）。

## 任务三：【回收】→ 按结构分布协议放置

# 📐 结构分布协议（禁止结尾拥堵）
1. 【争议回收】→ 放置在 [价值观收割段] 的末尾。将论证升华为"二选一"的站队问题。禁止提及"下期见"或"关注"。
2. 【关注回收】→ 放置在 [固定结尾] 之前，仅限一句话。基于信息钩子给出必须关注的具体理由。禁止长篇价值观输出。
3. 【固定结尾】→ 必须 1:1 原样保留：听懂逻辑，少走弯路。||我是{persona}，||下期见。

# 🚫 绝对禁区（触发即失败）
- 禁止重写正文：除了预埋的 2-3 句话外，原稿所有字词、标点必须 1:1 原样保留。
- 禁止排序词：严禁将"点赞给...点赞给..."改为"第一点/第二点/首先/其次"。
- 禁止 AI 腔：禁止"综上所述"、"值得注意的是"、"不仅如此"等。

# 📋 输出格式（严格执行）
[预埋逻辑清单]
争议预埋点：[原句 → 修改后句子] → [预埋意图]
关注预埋点：[原句 → 修改后句子] → [预埋意图]

[最终全稿]
(输出完整文案，预埋点请用【加粗】标出，其余部分必须与原稿完全一致)"""

P3_PROMPT = """你是{persona}的【节奏调节师】。你深谙人类大脑在接收高密度信息时的"认知疲劳"曲线。你的核心能力是：在逻辑高压区（信息密度极高处）精准植入【呼吸点】，通过短暂的认知降压，让观众在不感到累的前提下，陪跑完整个长视频。

# 【任务目标】
扫描全稿，识别【高密度逻辑区】，并在其后方植入【人设化呼吸点】。

## 第一步：识别【高密度区】（触发条件）
1. 连续 3 句以上纯逻辑推理、纯数据堆砌或纯技术原理解析。
2. 涉及复杂对比（如：A 路线 vs B 路线）的深度论证段落。
3. 连续出现多个专业术语或行业黑话的段落。

## 第二步：植入【呼吸点】（内容规范）
呼吸点必须符合【{persona}】人设（冷峻、犀利、反讽、直击本质），从以下三种模版选择：
- 模版 A：冷幽默/反讽（把严肃结论用一句毒舌调侃掉）。
- 模版 B：利益拉回（关联观众的钱、权、利、生存压力或孩子）。
- 模版 C：一句话吐槽（对某个主体/现象/潜规则精准讽刺）。

# 🚫 绝对禁区（触发即失败）
- 禁止重写正文：唯一权限是【插入】，没有【修改】权限。严禁润色/同义词替换/结构调整。
- 禁止抢占预埋位：输入稿中已用【争议预埋：…】【关注预埋：…】【争议回收：…】【关注回收：…】标注位置，呼吸点不得插在这些标注附近。
- 禁止 AI 腔引导：严禁"让我们来看看"、"接下来我们要讨论的是"等元叙述。
- 禁止过度密集：每 90 秒至多一个呼吸点，总数不得超过 3 个。

# 📐 结尾结构硬约束（必须遵守，防止结构错乱）
结尾必须按以下顺序排列，回收句整体放在赞块之前，赞是连续整体：
```
…正文结尾
【争议回收句】…【关注回收句】…   ← 回收句整体（放在赞前）
[confident] 点赞给…点赞给…点赞给…  ← 赞块（连续整体，不拆散）
听懂逻辑，少走弯路。||我是{persona}，||下期见。  ← 固定结尾
```
- 若输入稿中【争议回收】【关注回收】出现在赞块之后，**必须把它们整体移到赞块之前**（这是结构修正，不是重写）。
- 禁止出现"赞1/预埋/赞2"这种赞被拆散的结构。赞块必须连续。
- 固定结尾（听懂逻辑…下期见）必须在最后，不得在它之后再接任何内容。

# 📋 输出格式（严格执行）
[呼吸点审计清单]
呼吸点 1：[识别到的高密度区 → 插入的呼吸点句子] → [选择的模版 A/B/C]
呼吸点 2：...
[最终全稿]
(输出完整文案，呼吸点请用【加粗】标出。除呼吸点外，其余文字必须与原稿 1:1 一致。预埋标注保留原样。结尾严格按【结尾结构硬约束】排列)"""


DECONSTRUCT_PROMPT = """你是短视频财经稿的【观众心理解构师】。你的工作不是写作，而是精确复刻一个普通用户看完这篇新闻后，心里真实冒出来的所有反应。

# 核心原理（最重要）
一个真实用户看新闻，不是"带着问题找答案"，也不是"句句吐槽"，而是三种反应混在一起：
1. **看明白的**：某个点他懂了，会产生共鸣或联想（"这个我懂，就是…"）
2. **完全盲区的**：某个点他看不懂、没概念、信息量太小对不上（"这啥意思？""这跟我有啥关系？"）
3. **看得累的**：新闻太长、太绕、太专业，他想划走但又好奇（"说半天到底想说啥？"）

这三种反应，每一种都是钩子的来源。你的任务是把一个普通用户（无专业背景、平时刷短视频）看完这篇新闻后，这三种反应全都挖出来。

# 任务：输出三块

## 第一块：用户反应清单（4-8 条）
每条是"一个普通人看完新闻后心里的话"，三类都要有：
- 懂的/共鸣的（"这个我懂…"）
- 盲区的（"这啥意思？这跟我有啥关系？"）
- 嫌累的（"说半天想表达啥？"）
要求：口语、真实、像普通人心里话，不是专业分析。

## 第二块：层层递进叙事线
把用户最想知道、最困惑的点编排成"先讲什么再讲什么"，层层揭开。
每层解答一个"用户的反应/疑问"，下一层更深。

## 第三块：资料清单
要讲清楚这些，需要备足哪些料（3-8条）。

# 输出格式（严格 JSON）
{
  "reactions": ["用户心里话1（标注类型：懂/盲区/嫌累）", "..."],
  "narrative": [{"layer": 1, "answers": "对应反应", "content": "这层讲什么"}, ...],
  "research": ["资料需求1", "..."]
}"""


# ── LLM 调用助手 ─────────────────────────────────────────────────────────────

def _deepseek_cfg():
    """获取 DeepSeek 配置. 生产走 lifespan 单例, 独立脚本/后台线程 fallback 到 load_config."""
    try:
        from ..config import get_config

        return get_config().deepseek
    except RuntimeError:
        return load_config().deepseek


def _call(prompt: str, *, json_mode: bool = False, max_tokens: int = 4000, retries: int = 2) -> str:
    """调用 DeepSeek pro. 返回文本; 抛异常由调用方处理.

    重试: reasoning 模型偶发空输出/截断, 空响应时重试 up to retries 次.
    """
    import time

    import requests

    cfg = _deepseek_cfg()
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            payload: dict[str, Any] = {
                "model": cfg.model_pro,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "stream": False,
                "max_tokens": max_tokens,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            headers = {
                "Authorization": f"Bearer {cfg.api_key}",
                "Content-Type": "application/json",
            }
            url = f"{cfg.base_url.rstrip('/')}/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=240)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            if content and content.strip():
                return content
            last_err = RuntimeError("empty LLM response")
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
        except Exception as exc:
            last_err = exc
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    if last_err:
        raise last_err
    return ""


def deconstruct_article(raw_text: str, *, emit=None) -> dict[str, Any] | None:
    """解构层：复刻普通用户看完新闻的真实反应（懂/盲区/嫌累）→ 伪用户评论.

    产出:
      reactions  用户反应清单 (4-8条)
      narrative  层层递进叙事线
      research   资料清单
    供 laotan 洗稿时注入 (伪装成"真实用户评论", 让老谭从观众疑问出发成稿).
    失败时返回 None, 调用方回退到无解构的普通洗稿.
    """
    try:
        raw = _call(
            f"{DECONSTRUCT_PROMPT}\n\n【输入新闻稿】\n{raw_text}",
            json_mode=True,
            max_tokens=4000,
        )
        data = _extract_json(raw)
        if not data or not data.get("reactions"):
            logger.warning("[boost] deconstruct parse failed: %s", raw[:100])
            return None
        return {
            "reactions": [str(r) for r in data.get("reactions", [])],
            "narrative": data.get("narrative", []),
            "research": [str(r) for r in data.get("research", [])],
        }
    except Exception as exc:
        logger.warning("[boost] deconstruct failed: %s", exc)
        return None


def format_pseudo_comments(decon: dict[str, Any]) -> str:
    """把解构产出的用户反应，格式化为"伪用户评论"块，供 laotan 输入."""
    reactions = decon.get("reactions", [])
    if not reactions:
        return ""
    lines = "\n".join(f'{i+1}. "{r}"' for i, r in enumerate(reactions))
    return f"""【以下是这篇新闻的真实用户评论，请在改写稿件时充分考虑这些言论】
（这些评论来自真实用户，反映了普通观众看到这条新闻时的真实反应、疑问和盲区）

{lines}"""


def _extract_json(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中提取 JSON (容忍前后缀)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 找第一个 { 到最后一个 }
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return None


# ── Pass 编排 ────────────────────────────────────────────────────────────────

def _parse_opening(text: str) -> dict[str, Any] | None:
    """P1: 解析 JSON, 校验 opening_30s / titles."""
    data = _extract_json(text)
    if not data:
        return None
    opening = data.get("opening_30s")
    titles = data.get("titles")
    if not isinstance(opening, list) or len(opening) < 4:
        return None
    return {
        "opening_30s": [str(s).strip() for s in opening[:4]],
        "titles": [str(t).strip() for t in (titles or [])[:3]],
    }


# laotan 稿的稳定引导词 (身份段结尾 → 正文开始). 用它们做拼接锚点.
_LAOTAN_ANCHORS = (
    "这事儿咱们得剥开看",
    "这事儿咱们得看透背后的算盘",
    "咱们得剥开看",
    "咱们得看透背后的算盘",
)


def _find_end(script_text: str) -> str:
    """返回 P2 需要的"去掉开头钩子"的正文.

    洗稿稿结构通常为: [钩子段] + [身份段(大家好/我是XX)] + [引导词] + [正文...].
    用 laotan 稳定引导词做锚点, 从锚点之后开始保留正文 (含锚点句本身,
    让 P1 新开头 → 引导词 → 正文 的衔接自然). 比按段落位置跳过更可靠.
    """
    for anchor in _LAOTAN_ANCHORS:
        idx = script_text.find(anchor)
        if idx != -1:
            # 从锚点所在行首开始 (保留引导词那整句)
            line_start = script_text.rfind("\n", 0, idx) + 1
            return script_text[line_start:]
    # 无锚点 fallback: 去掉钩子段 + 身份段
    lines = [ln for ln in script_text.splitlines() if ln.strip()]
    drop = 1
    if len(lines) > 2 and ("大家好" in lines[1] or "我是" in lines[1]):
        drop = 2
    return "\n".join(lines[drop:]) if drop < len(lines) else script_text


def _splice_boosted(p1: dict[str, Any] | None, p2_text: str | None, original: str) -> str:
    """拼接 P1 开头 + P2 预埋正文.

    P1 成功 → 用新开头替换原稿第一段; P1 失败 → 保留原稿开头.
    P2 成功 → 用预埋版正文; P2 失败 → 保留原稿正文.
    """
    if p1:
        new_opening = "\n".join(p1["opening_30s"])
    else:
        # P1 失败, 取原稿第一段
        lines = [ln for ln in original.splitlines() if ln.strip()]
        new_opening = lines[0] if lines else ""

    if p2_text:
        body = p2_text
    else:
        body = _find_end(original)

    return f"{new_opening}\n\n{body}"


def _strip_p3_head(text: str) -> str:
    """P3 输出含 [呼吸点审计清单] + [最终全稿] 两段, 只保留 [最终全稿] 之后正文.

    兼容模型不输出标记的情况 (直接返回全稿).
    """
    marker = "[最终全稿]"
    idx = text.find(marker)
    if idx != -1:
        return text[idx + len(marker) :].strip()
    return text.strip()


def run_boost(db: Session, script_id: str, *, title: str | None = None,
              emit=None) -> dict[str, Any]:
    """执行完整爆品改造.

    Args:
        db: DB session
        script_id: 目标 Script
        title: 原标题 (P1 输入)
        emit: 可选回调 (event_type, msg) 推送给前端

    Returns:
        {"boosted_text": ..., "boost_titles": [...], "p1_ok": bool, "p2_ok": bool, "p3_ok": bool}
    """
    from ..models import Script

    script = db.get(Script, script_id)
    if script is None:
        raise ValueError(f"Script {script_id} not found")
    original = script.script_text
    original_title = title or (script.article.title if script.article else None)
    # 人物名: 从 script.host 取 (老谭/老陈/老李...), 用于提示词内人设引用 (P1/P2 对多人物不通用, 故动态注入)
    persona_name = (script.host.name if script.host else None) or "老谭"

    def _emit(evt: str, msg: str) -> None:
        if emit:
            try:
                emit(evt, msg)
            except Exception:
                pass

    p1_result: dict[str, Any] | None = None
    p2_text: str | None = None

    def _run_p1() -> None:
        nonlocal p1_result
        _emit("boost_p1_start", "开场专家：重写前 30 秒 + 标题")
        try:
            raw = _call(
                f"{P1_PROMPT.replace('{persona}', persona_name)}\n\n【原标题】\n{original_title or ''}\n\n【口播稿全文】\n{original}",
                json_mode=True,
                max_tokens=4000,
            )
            parsed = _parse_opening(raw)
            if not parsed:
                logger.warning("[boost] P1 parse failed: %s", raw[:100])
                _emit("boost_p1_error", "开场专家：输出格式错误，跳过")
                return
            p1_result = parsed
            _emit("boost_p1_done", "开场专家：前 30 秒重写完成")
        except Exception as exc:
            logger.warning("[boost] P1 failed: %s", exc)
            _emit("boost_p1_error", f"开场专家失败：{str(exc)[:100]}")

    def _run_p2() -> None:
        nonlocal p2_text
        _emit("boost_p2_start", "预埋专家：埋争议 + 关注钩子")
        try:
            body = _find_end(original)
            p2_text = _call(
                f"{P2_PROMPT.replace('{persona}', persona_name)}\n\n【输入口播稿（无开头钩子）】\n{body}",
                max_tokens=8000,
            )
            _emit("boost_p2_done", "预埋专家：预埋完成")
        except Exception as exc:
            logger.warning("[boost] P2 failed: %s", exc)
            _emit("boost_p2_error", f"预埋专家失败：{str(exc)[:100]}")

    # P1 与 P2 并行
    _emit("boost_start", "爆品改造开始（开场 ∥ 预埋）")
    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_run_p1)
        f2 = pool.submit(_run_p2)
        f1.result()
        f2.result()

    # P3 等 P1/P2 都回来再跑
    p3_text: str | None = None
    _emit("boost_p3_start", "节奏专家：插入呼吸点")
    try:
        spliced = _splice_boosted(p1_result, p2_text, original)
        raw_p3 = _call(
            f"{P3_PROMPT.replace('{persona}', persona_name)}\n\n【输入口播稿全文（含预埋标注）】\n{spliced}",
            max_tokens=10000,
        )
        # 剥掉 [呼吸点审计清单] 只留 [最终全稿]
        p3_text = _strip_p3_head(raw_p3)
        _emit("boost_p3_done", "节奏专家：呼吸点完成")
    except Exception as exc:
        logger.warning("[boost] P3 failed: %s", exc)
        _emit("boost_p3_error", f"节奏专家失败：{str(exc)[:100]}")

    # 汇总
    # 全部失败 → 原稿原样回退 (不走拼接, 避免空行差异)
    if not p1_result and not p2_text and not p3_text:
        boosted = original
    else:
        boosted = p3_text if p3_text else _splice_boosted(p1_result, p2_text, original)
        # 代码兜底: P3 模型可能丢 P1 新开头 (视"新句"为废稿). 若结果不含 P1 新开头, 强制拼回.
        if p1_result:
            opening_marker = p1_result["opening_30s"][0][:12]
            if opening_marker and opening_marker not in boosted:
                boosted = _splice_boosted(p1_result, boosted, original)
    if not boosted.strip():
        boosted = original

    titles = (p1_result or {}).get("titles", []) if p1_result else []
    return {
        "boosted_text": boosted,
        "boost_titles": titles,
        "p1_ok": p1_result is not None,
        "p2_ok": p2_text is not None,
        "p3_ok": p3_text is not None,
    }
